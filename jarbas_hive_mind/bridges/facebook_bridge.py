from builtins import str
import base64
import json
from threading import Thread
import logging
from time import sleep
import sys

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from fbchat.utils import Message
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

from fbchat import log, Client


platform = "JarbasFaceBookBridgev0.1"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class FaceBot(Client):
    protocol = None

    def bind(self, protocol):
        self.protocol = protocol

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

        # If you're not the author, echo
        if author_id != self.uid:
            msg = {"data": {"utterances": [message_object.text],
                            "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {"source": self.protocol.peer,
                               "destinatary": "https_server", "platform": platform,
                               "user": author_id, "fb_chat_id": author_id,
                               "target": "fbchat"}}
            msg = json.dumps(msg)
            self.protocol.clients[author_id] = {"type": thread_type}
            self.protocol.sendMessage(msg, False)


class JarbasFacebookClientProtocol(WebSocketClientProtocol):
    facebook = None
    chat_thread = None
    clients = {}
    MAIL = ""
    PASSWD = ""

    def start_fb_chat(self):
        self.facebook = FaceBot(self.MAIL, self.PASSWD)
        self.facebook.listen()

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"
        self.MAIL = self.factory.mail
        self.PASSWD = self.factory.passwd

    def onOpen(self):
        logger.info("WebSocket connection open. ")

        self.chat_thread = Thread(target=self.start_fb_chat)
        self.chat_thread.setDaemon(True)
        self.chat_thread.start()
        while self.facebook is None:
            sleep(1)
        self.facebook.bind(self)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            msg = json.loads(payload)
            utterance = ""
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
            elif msg.get("type", "") == "server.complete_intent_failure":
                utterance = "does not compute"

            if utterance:
                user_id = msg["context"]["fb_chat_id"]
                self.facebook.send(Message(text=utterance),
                                   thread_id=user_id,
                                   thread_type=self.clients[user_id]["type"])
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"


class JarbasFacebookClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasFacebookClientProtocol

    def __init__(self, mail, password, name="facebook bridge", *args, **kwargs):
        super(JarbasFacebookClientFactory, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.name = name
        self.client = None
        self.mail = mail
        self.passwd = password

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("Client connection failed: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("Client connection lost: " + str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)


def connect_to_facebook(mail, password, host="127.0.0.1", port=5678,
                        name="facebook bridge", api="test_key", useragent=platform):
    authorization = name + ":" + api
    usernamePasswordDecoded = authorization
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasFacebookClientFactory(address, mail=mail, password=password,
                                          name=name, headers=headers, useragent=useragent)
    factory.protocol = JarbasFacebookClientProtocol
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO arg parse
    connect_to_facebook("", "")
