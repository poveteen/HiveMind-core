import base64
import json
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from mycroft.configuration import Configuration
from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG as logger
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasDrone:" + Configuration.get().get("enclosure", {}).get(
    "platform", "linux")


class JarbasClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.emitter.emit(Message("hive.mind.connected",
                                          {"server_id": response.headers[
                                              "server"]}))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        self.factory.emitter.emit(Message("hive.mind.websocket.open"))

    def onMessage(self, payload, isBinary):
        logger.info("status: " + self.factory.status)
        if not isBinary:
            payload = payload.decode("utf-8")
            data = {"payload": payload, "isBinary": isBinary}
        else:
            data = {"payload": None, "isBinary": isBinary}
        self.factory.emitter.emit(Message("hive.mind.message.received",
                                          data))

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.emitter.emit(Message("hive.mind.connection.closed",
                                          {"wasClean": wasClean,
                                           "reason": reason,
                                           "code": code}))
        self.factory.client = None
        self.factory.status = "disconnected"

    def Message_to_raw_data(self, message):
        # convert a Message object into raw data that can be sent over
        # websocket
        if hasattr(message, 'serialize'):
            return message.serialize()
        else:
            return json.dumps(message.__dict__)


class JarbasClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasClientProtocol
    emitter = None

    def __init__(self, *args, **kwargs):
        super(JarbasClientFactory, self).__init__(*args, **kwargs)
        self.client = None
        self.status = "disconnected"
        # mycroft_ws
        self.emitter_thread = None

    # initialize methods
    def connect_to_internal_emitter(self):
        self.emitter.run_forever()

    def create_internal_emitter(self, emitter=None):
        # connect to mycroft internal websocket
        self.emitter = emitter or self.emitter or WebsocketClient()
        self.register_internal_messages()
        self.emitter_thread = Thread(target=self.connect_to_internal_emitter)
        self.emitter_thread.setDaemon(True)
        self.emitter_thread.start()

    def register_internal_messages(self):
        self.emitter.on("hive.mind.message.received",
                        self.handle_receive_server_message)
        self.emitter.on("hive.mind.message.send",
                        self.handle_send_server_message)

    def shutdown(self):
        self.emitter.remove("hive.mind.message.received",
                            self.handle_receive_server_message)
        self.emitter.remove("hive.mind.message.send",
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
            self.emitter.emit(message)

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
        msg = self.client.Message_to_raw_data(Message(type, data, context))
        self.client.sendMessage(bytes(msg, "utf-8"), isBinary=False)
        self.emitter.emit(Message("hive.mind.message.sent",
                                  {"type": type,
                                   "data": data,
                                   "context": context,
                                   "raw": msg}))


def connect_to_hivemind(host="127.0.0.1",
                        port=5678, name="Jarbas Drone",
                        api="test_key", useragent=platform, emitter=None):
    authorization = name + ":" + api
    usernamePasswordDecoded = bytes(authorization, "utf-8")
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasClientFactory(address, headers=headers,
                                  useragent=useragent)
    factory.protocol = JarbasClientProtocol
    factory.create_internal_emitter(emitter)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO arg parse
    connect_to_hivemind()
