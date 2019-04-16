import base64
from os.path import exists
from threading import Thread

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from twisted.internet import reactor, ssl

from jarbas_hive_mind.database.client import ClientDatabase
from jarbas_hive_mind.settings import CERTS_PATH, DEFAULT_SSL_CRT, \
    DEFAULT_SSL_KEY, DEFAULT_PORT, USE_SSL
from jarbas_hive_mind.utils import create_self_signed_cert
from jarbas_hive_mind.utils.log import LOG
from jarbas_hive_mind.utils.messagebus.message import Message
from jarbas_hive_mind.utils.messagebus.ws import WebsocketClient

author = "jarbasAI"

NAME = "JarbasMindv0.1"

users = ClientDatabase()


# protocol
class JarbasMindProtocol(WebSocketServerProtocol):
    def onConnect(self, request):

        LOG.info("Client connecting: {0}".format(request.peer))
        # validate user
        userpass_encoded = bytes(request.headers.get("authorization"),
                                 encoding="utf-8")[2:-1]
        userpass_decoded = base64.b64decode(userpass_encoded).decode("utf-8")
        name, key = userpass_decoded.split(":")
        ip = request.peer.split(":")[1]
        context = {"source": self.peer}
        self.platform = request.headers.get("platform", "unknown")

        try:
            user = users.get_client_by_api_key(key)
        except:
            LOG.info("Client provided an invalid api key")
            self.factory.mycroft_send("hive.client.connection.error",
                                      {"error": "invalid api key",
                                       "ip": ip,
                                       "api_key": key,
                                       "platform": self.platform},
                                      context)
            raise ValueError("Invalid API key")
        # send message to internal mycroft bus
        data = {"ip": ip, "headers": request.headers}
        self.blacklist = users.get_blacklist_by_api_key(key)
        self.factory.mycroft_send("hive.client.connect", data, context)
        # return a pair with WS protocol spoken (or None for any) and
        # custom headers to send in initial WS opening handshake HTTP response
        headers = {"server": NAME}
        return (None, headers)

    def onOpen(self):
        """
       Connection from client is opened. Fires after opening
       websockets handshake has been completed and we can send
       and receive messages.

       Register client in factory, so that it is able to track it.
       """
        self.factory.register_client(self, self.platform)
        LOG.info("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            LOG.info(
                "Binary message received: {0} bytes".format(len(payload)))
        else:
            LOG.info(
                "Text message received: {0}".format(payload.decode('utf8')))

        self.factory.process_message(self, payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.factory.unregister_client(self, reason=u"connection closed")
        LOG.info("WebSocket connection closed: {0}".format(reason))
        ip = self.peer.split(":")[1]
        data = {"ip": ip, "code": code, "reason": "connection closed",
                "wasClean": wasClean}
        context = {"source": self.peer}
        self.factory.mycroft_send("hive.client.disconnect", data, context)

    def connectionLost(self, reason):
        """
       Client lost connection, either disconnected or some error.
       Remove client from list of tracked connections.
       """
        self.factory.unregister_client(self, reason=u"connection lost")
        LOG.info("WebSocket connection lost: {0}".format(reason))
        ip = self.peer.split(":")[1]
        data = {"ip": ip, "reason": "connection lost"}
        context = {"source": self.peer}
        self.factory.mycroft_send("hive.client.disconnect", data, context)


# server internals
class JarbasMind(WebSocketServerFactory):
    def __init__(self, bus=None, *args, **kwargs):
        super(JarbasMind, self).__init__(*args, **kwargs)
        # list of clients
        self.clients = {}
        # ip block policy
        self.ip_list = []
        self.blacklist = True  # if False, ip_list is a whitelist
        # mycroft_ws
        self.bus = bus
        self.bus_daemon = None
        self.create_mycroft_connection()

    def mycroft_send(self, type, data=None, context=None):
        data = data or {}
        context = context or {}
        if "client_name" not in context:
            context["client_name"] = NAME
        self.bus.emit(Message(type, data, context))

    def connect_to_mycroft(self):
        self.bus.run_forever()

    def create_mycroft_connection(self):
        # connect to mycroft internal websocket
        self.bus = self.bus or WebsocketClient()
        self.register_mycroft_messages()
        self.bus_daemon = Thread(target=self.connect_to_mycroft)
        self.bus_daemon.setDaemon(True)
        self.bus_daemon.start()

    def register_mycroft_messages(self):
        # HACK, TODO find why failing
        # self.bus.on('message', self.handle_message)

        def wrapper(cl, message):
            message = Message.deserialize(message)
            self.handle_message(message)

        self.bus.on("message", self.handle_message)
        # self.bus.client.on_message = wrapper

        self.bus.on('hive.client.broadcast', self.handle_broadcast)
        self.bus.on('hive.client.send', self.handle_send)

    # websocket handlers
    def register_client(self, client, platform=None):
        """
       Add client to list of managed connections.
       """
        platform = platform or "unknown"
        LOG.info("registering client: " + str(client.peer))
        t, ip, sock = client.peer.split(":")
        # see if ip address is blacklisted
        if ip in self.ip_list and self.blacklist:
            LOG.warning("Blacklisted ip tried to connect: " + ip)
            self.unregister_client(client, reason=u"Blacklisted ip")
            return
        # see if ip address is whitelisted
        elif ip not in self.ip_list and not self.blacklist:
            LOG.warning("Unknown ip tried to connect: " + ip)
            #  if not whitelisted kick
            self.unregister_client(client, reason=u"Unknown ip")
            return
        self.clients[client.peer] = {"object": client,
                                     "status": "connected",
                                     "platform": platform}

    def unregister_client(self, client, code=3078,
                          reason=u"unregister client request"):
        """
       Remove client from list of managed connections.
       """
        LOG.info("deregistering client: " + str(client.peer))
        if client.peer in self.clients.keys():
            client_data = self.clients[client.peer] or {}
            j, ip, sock_num = client.peer.split(":")
            context = {"user": client_data.get("names", ["unknown_user"])[0],
                       "source": client.peer}
            self.bus.emit(
                Message("hive.client.disconnect",
                        {"reason": reason, "ip": ip, "sock": sock_num},
                        context))
            client.sendClose(code, reason)
            self.clients.pop(client.peer)

    def process_message(self, client, payload, isBinary):
        """
       Process message from client, decide what to do internally here
       """
        LOG.info("processing message from client: " + str(client.peer))
        client_data = self.clients[client.peer]
        client_protocol, ip, sock_num = client.peer.split(":")

        if isBinary:
            # TODO receive files
            pass
        else:
            # add context for this message
            payload = payload.decode("utf-8")
            message = Message.deserialize(payload)
            message.context["source"] = client.peer
            message.context["destination"] = "skills"
            if "platform" not in message.context:
                message.context["platform"] = client_data.get("platform",
                                                              "unknown")

            # messages/skills/intents per user
            if message.type in client.blacklist.get("messages", []):
                LOG.warning(client.peer + " sent a blacklisted message " \
                                          "type: " + message.type)
                return
            # TODO check intent / skill that will trigger

            # send client message to internal mycroft bus
            self.mycroft_send(message.type, message.data, message.context)

    # mycroft handlers
    def handle_send(self, message):
        # send message to client
        msg = message.data.get("payload")
        is_file = message.data.get("isBinary")
        peer = message.data.get("peer")
        if is_file:
            # TODO send file
            pass
        elif peer in self.clients:
            # send message to client
            client = self.clients[peer]
            payload = Message.serialize(msg)
            client.sendMessage(payload, False)
        else:
            LOG.error("That client is not connected")
            self.mycroft_send("hive.client.send.error",
                              {"error": "That client is not connected",
                               "peer": peer}, message.context)

    def handle_broadcast(self, message):
        # send message to all clients
        msg = message.data.get("payload")
        is_file = message.data.get("isBinary")
        if is_file:
            # TODO send file
            pass
        else:
            # send message to all clients
            server_msg = Message.serialize(msg)
            self.broadcast(server_msg)

    def handle_message(self, message=None):
        # forward internal messages to clients if they are the target
        message = Message.deserialize(message)
        if message.type == "complete_intent_failure":
            message.type = "hive.complete_intent_failure"
        message.context = message.context or {}
        peer = message.context.get("destination")
        if peer and peer in self.clients:
            client_data = self.clients[peer] or {}
            client = client_data.get("object")
            message = message.serialize()
            client.sendMessage(bytes(message, encoding="utf-8"),
                               False)

    def shutdown(self):
        self.bus.remove('message', self.handle_message)
        self.bus.remove('hive.client.broadcast', self.handle_broadcast)
        self.bus.remove('hive.client.send', self.handle_send)


def start_mind(config=None, bus=None):
    # server
    config = config or {}
    host = config.get("host", "0.0.0.0")
    port = config.get("port", DEFAULT_PORT)
    # TODO non-ssl support
    use_ssl = config.get("ssl", USE_SSL)
    max_connections = config.get("max_connections", -1)
    address = u"wss://" + str(host) + u":" + str(port)
    cert = config.get("cert_file", DEFAULT_SSL_CRT)
    key = config.get("key_file", DEFAULT_SSL_KEY)

    factory = JarbasMind(bus=bus)
    factory.protocol = JarbasMindProtocol
    if max_connections >= 0:
        factory.setProtocolOptions(maxConnections=max_connections)

    if not exists(key) or not exists(cert):
        LOG.warning("ssl keys dont exist, creating self signed")
        name = key.split("/")[-1].replace(".key", "")
        create_self_signed_cert(CERTS_PATH, name)
        cert = CERTS_PATH + "/" + name + ".crt"
        key = CERTS_PATH + "/" + name + ".key"
        LOG.info("key created at: " + key)
        LOG.info("crt created at: " + cert)
        # update config with new keys
        config["cert_file"] = cert
        config["key_file"] = key
        # factory.config_update({"mind": config}, True)

    # SSL server context: load server key and certificate
    contextFactory = ssl.DefaultOpenSSLContextFactory(key, cert)

    reactor.listenSSL(port, factory, contextFactory)
    print("Starting mind: ", address)
    reactor.run()


if __name__ == '__main__':
    start_mind()
