import base64
import json
import logging
import sys
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasCliTerminalv0.1"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class JarbasCliClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        self.input_loop = Thread(target=self.get_cli_input)
        self.input_loop.setDaemon(True)
        self.input_loop.start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("Output: " + utterance)
            if msg.get("type", "") == "server.complete_intent_failure":
                logger.error("Output: complete_intent_failure")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"

    # cli input thread
    def get_cli_input(self):
        while True:
            line = input("Input: ")
            msg = {"data": {"utterances": [line], "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {"source": self.peer, "destinatary":
                       "https_server", "platform": platform}}
            msg = bytes(json.dumps(msg), "utf-8")
            self.sendMessage(msg, False)


class JarbasCliClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasCliClientProtocol

    def __init__(self, *args, **kwargs):
        super(JarbasCliClientFactory, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("Client connection failed: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("Client connection lost: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)


def connect_to_hivemind(host="127.0.0.1",
                        port=5678, name="Standalone Cli Client",
                        api="test_key", useragent=platform):
    authorization = name + ":" + api
    usernamePasswordDecoded = bytes(authorization, "utf-8")
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasCliClientFactory(address, headers=headers,
                                     useragent=useragent)
    factory.protocol = JarbasCliClientProtocol
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    connect_to_hivemind()
