import base64
import json
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

from jarbas_hive_mind.utils.log import LOG as logger
from jarbas_hive_mind.utils.messagebus import Message
from jarbas_hive_mind.utils.messagebus import WebsocketClient

platform = "Jarbas Drone"


class JarbasDroneProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.bus.emit(Message("hive.mind.connected",
                                      {"server_id": response.headers[
                                              "server"]}))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        self.factory.bus.emit(Message("hive.mind.websocket.open"))

    def onMessage(self, payload, isBinary):
        logger.info("status: " + self.factory.status)
        if not isBinary:
            payload = payload.decode("utf-8")
            data = {"payload": payload, "isBinary": isBinary}
        else:
            data = {"payload": None, "isBinary": isBinary}
        self.factory.bus.emit(Message("hive.mind.message.received",
                                      data))

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.bus.emit(Message("hive.mind.connection.closed",
                                      {"wasClean": wasClean,
                                           "reason": reason,
                                           "code": code}))
        self.factory.client = None
        self.factory.status = "disconnected"

    def serialize_message(self, message):
        # convert a Message object into raw data that can be sent over
        # websocket
        if hasattr(message, 'serialize'):
            return message.serialize()
        else:
            return json.dumps(message.__dict__)


class JarbasDrone(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasDroneProtocol

    def __init__(self, bus=None, *args, **kwargs):
        super(JarbasDrone, self).__init__(*args, **kwargs)
        self.client = None
        self.status = "disconnected"
        # mycroft_ws
        self.bus = bus
        self.mycroft_bus_thread = None
        self.create_mycroft_bus()

    # initialize methods
    def connect_to_mycroft(self):
        self.bus.run_forever()

    def create_mycroft_bus(self):
        # connect to mycroft internal websocket
        self.bus = self.bus or WebsocketClient()
        self.register_mycroft_messages()
        self.mycroft_bus_thread = Thread(target=self.connect_to_mycroft)
        self.mycroft_bus_thread.setDaemon(True)
        self.mycroft_bus_thread.start()

    def register_mycroft_messages(self):
        self.bus.on("hive.mind.message.received",
                    self.handle_receive_server_message)
        self.bus.on("hive.mind.message.send",
                    self.handle_send_server_message)

    def shutdown(self):
        self.bus.remove("hive.mind.message.received",
                        self.handle_receive_server_message)
        self.bus.remove("hive.mind.message.send",
                        self.handle_send_server_message)

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info(
            "Client connection failed: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info(
            "Client connection lost: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    # mycroft handlers
    def handle_receive_server_message(self, message):
        server_msg = message.data.get("payload")
        is_file = message.data.get("isBinary")
        if is_file:
            # TODO received file
            pass
        else:
            # forward server message to internal bus
            message = Message.deserialize(server_msg)
            self.bus.emit(message)

    def handle_send_server_message(self, message):
        server_msg = message.data.get("payload")
        is_file = message.data.get("isBinary")
        if is_file:
            # TODO send file
            pass
        else:
            # send message to server
            server_msg = Message.deserialize(server_msg)
            server_msg.context["platform"] = platform
            self.sendMessage(server_msg.type, server_msg.data,
                             server_msg.context)

    def sendRaw(self, data):
        if self.client is None:
            logger.error("Client is none")
            return
        self.client.sendMessage(data, isBinary=True)

    def sendMessage(self, type, data, context=None):
        if self.client is None:
            logger.error("Client is none")
            return
        if context is None:
            context = {}
        msg = self.client.serialize_message(Message(type, data, context))
        self.client.sendMessage(msg, isBinary=False)
        self.bus.emit(Message("hive.mind.message.sent",
                              {"type": type,
                               "data": data,
                               "context": context,
                               "raw": msg}))


def connect_to_hivemind(host="127.0.0.1", port=5678, name="Jarbas Drone",
                        key="drone_key", useragent=platform, bus=None):
    authorization = bytes(name + ":" + key, encoding="utf-8")
    usernamePasswordDecoded = authorization
    key = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': key}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasDrone(bus=bus, headers=headers,
                          useragent=useragent)
    factory.protocol = JarbasDroneProtocol
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO arg parse
    connect_to_hivemind()
