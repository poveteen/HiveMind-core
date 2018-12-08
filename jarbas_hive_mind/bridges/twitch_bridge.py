import base64
import json
import logging
import socket
import string
import sys
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasTwitchBridgev0.1"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class JarbasTwitchClientProtocol(WebSocketClientProtocol):
    # Set all the variables necessary to connect to Twitch IRC
    HOST = "irc.twitch.tv"
    NICK = "jarbas_le_bot"
    PORT = 6667
    PASS = "oauth:GET_YOURS"
    CHANNELNAME = "jarbasai"

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        self.NICK = self.factory.username
        self.PASS = self.factory.oauth
        self.connect_to_twitch()
        self.input_loop = Thread(target=self.twitch_loop)
        self.input_loop.setDaemon(True)
        self.input_loop.start()

    def connect_to_twitch(self):
        # Connecting to Twitch IRC by passing credentials and joining a certain channel
        self.s = socket.socket()
        self.s.connect((self.HOST, self.PORT))
        self.s.send("PASS " + self.PASS + "\r\n")
        self.s.send("NICK " + self.NICK + "\r\n")
        self.s.send("JOIN #" + self.CHANNELNAME + " \r\n")

    # Method for sending a message
    def twitch_send(self, message):
        self.s.send("PRIVMSG #" + self.CHANNELNAME + " :" + message + "\r\n")

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                user = msg.get("context", {}).get("user")
                logger.info("Output: " + utterance)
                if user:
                    utterance += " " + user
                self.twitch_send(utterance)
            if msg.get("type", "") == "server.complete_intent_failure":
                logger.error("Output: complete_intent_failure")
                self.twitch_send("does not compute")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"

    def twitch_loop(self):

        readbuffer = ""
        MODT = False

        while True:
            readbuffer = readbuffer + self.s.recv(1024)
            temp = string.split(readbuffer, "\n")
            readbuffer = temp.pop()

            for line in temp:
                # Checks whether the message is PING because its a method of Twitch to check if you're afk
                if (line[0] == "PING"):
                    self.s.send("PONG %s\r\n" % line[1])
                else:
                    # Splits the given string so we can work with it better
                    parts = string.split(line, ":")

                    if "QUIT" not in parts[1] and "JOIN" not in parts[1] and "PART" not in parts[1]:
                        try:
                            # Sets the message variable to the actual message sent
                            message = parts[2][:len(parts[2]) - 1]
                        except:
                            message = ""
                        # Sets the username variable to the actual username
                        usernamesplit = string.split(parts[1], "!")
                        username = usernamesplit[0]
                        print("twitch message: ", message)
                        if "@" + self.NICK in message:
                            message = message.replace("@" + self.NICK, "")
                            # Only works after twitch is done announcing stuff (MODT = Message of the day)
                            if MODT:
                                msg = {"data": {"utterances": [message], "lang": "en-us"},
                                       "type": "recognizer_loop:utterance",
                                       "context": {"source": "twitch", "destinatary":
                                           "https_server", "platform": platform, "user": username}}
                                msg = json.dumps(msg)
                                self.sendMessage(bytes(msg, "utf-8"), False)

                        for l in parts:
                            if "End of /NAMES list" in l:
                                MODT = True


class JarbasTwitchClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasTwitchClientProtocol
    oauth = ""
    channel = ""
    username = "Jarbas_BOT"

    def __init__(self, *args, **kwargs):
        super(JarbasTwitchClientFactory, self).__init__(*args, **kwargs)
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


def connect_to_twitch(oauth, channel, username="Jarbas_BOT", host="127.0.0.1",
                        port=5678, name="Standalone Twitch Bridge",
                      api="test_key", useragent=platform):
    authorization = name + ":" + api
    usernamePasswordDecoded = bytes(authorization, "utf-8")
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasTwitchClientFactory(address, headers=headers,
                                        useragent=useragent)
    factory.protocol = JarbasTwitchClientProtocol
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO parse args
    connect_to_twitch("", "")


