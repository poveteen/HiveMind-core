import base64
import json
import logging
import socket
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


class JarbasTwitchBridgeProtocol(WebSocketClientProtocol):
    # Set all the variables necessary to connect to Twitch IRC
    HOST = "irc.twitch.tv"
    NICK = "jarbas_bot"
    PORT = 6667
    PASS = "oauth:GET_YOURS"
    CHANNELNAME = "jarbasai"

    def onConnect(self, response):
        logger.info("[INFO] " + "Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("[INFO] " + "WebSocket connection open. ")
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
        self.s.send(b"PASS " + bytes(self.PASS, encoding="utf-8") + b"\r\n")
        self.s.send(b"NICK " + bytes(self.NICK, encoding="utf-8") + b"\r\n")
        self.s.send(
            b"JOIN #" + bytes(self.CHANNELNAME, encoding="utf-8") + b" \r\n")

    # Method for sending a message
    def twitch_send(self, message):
        msg = bytes("PRIVMSG #" + self.CHANNELNAME + " :" + message +
                    "\r\n", encoding="utf-8")
        self.s.send(msg)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                user = msg.get("context", {}).get("user")
                logger.info("[OUTPUT] " + utterance)
                if user:
                    utterance += " " + user
                self.twitch_send(utterance)
            if msg.get("type", "") == "server.complete_intent_failure":
                utterance = "does not compute"
                logger.error("Output: complete_intent_failure")
                logger.info("[OUTPUT] " + utterance)
                self.twitch_send(utterance)
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("[INFO] " + "WebSocket connection closed: {0}".format(
            reason))
        self.factory.client = None
        self.factory.status = "disconnected"
        if "Internalservererror:InvalidAPIkey" in reason:
            logger.error("[ERROR] invalid user:key provided")
            raise ConnectionAbortedError("invalid user:key provided")

    def twitch_loop(self):

        readbuffer = ""
        MODT = False

        while True:
            readbuffer = readbuffer + self.s.recv(1024).decode("utf-8")
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                # Splits the given string so we can work with it better
                parts = line.split(":")
                # Checks whether the message is PING because its a method of Twitch to check if you're afk
                if (parts[0].strip() == "PING"):
                    msg = bytes("PONG %s\r\n" % parts[1], encoding="utf-8")
                    self.s.send(msg)
                else:
                    # Only works after twitch is done announcing stuff (MODT = Message of the day)
                    if not MODT:
                        for l in parts:
                            if "End of /NAMES list" in l:
                                MODT = True
                        continue
                    if "QUIT" not in parts[1] and "JOIN" not in parts[
                        1] and "PART" not in parts[1]:
                        try:
                            # Sets the message variable to the actual message sent
                            message = parts[2][:len(parts[2]) - 1]
                        except:
                            continue
                        # Sets the username variable to the actual username
                        usernamesplit = parts[1].split("!")
                        username = usernamesplit[0]
                        if "@" + self.NICK.lower() in message.lower():
                            message = message.replace("@" + self.NICK, "")
                            self.handle_twitch_mention(message, username)
                        else:
                            self.handle_twitch_message(message, username)

    def handle_twitch_message(self, message, sender):
        logger.info("[INFO] " + sender + " said: " + message)

    def handle_twitch_mention(self, message, sender):
        logger.info("[INFO] " + sender + " said to you: " + message)
        msg = {"data": {"utterances": [message],
                        "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": {"source": "twitch",
                           "destination": "hive_mind",
                           "platform": platform,
                           "user": sender}}
        msg = json.dumps(msg)
        msg = bytes(msg, encoding="utf-8")
        self.sendMessage(msg, False)


class JarbasTwitchBridge(WebSocketClientFactory,
                         ReconnectingClientFactory):
    protocol = JarbasTwitchBridgeProtocol

    def __init__(self, oauth, channel, username="Jarbas_BOT", *args, **kwargs):
        super(JarbasTwitchBridge, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None
        self.oauth = oauth
        self.channel = channel
        self.username = username

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


def connect_to_twitch(oauth, channel, username="Jarbas_BOT", host="127.0.0.1",
                      port=5678, name="Jarbas Twitch Bridge",
                      api="twitch_key", useragent=platform):
    authorization = bytes(name + ":" + api, encoding="utf-8")
    usernamePasswordDecoded = authorization
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    logger.info("[INFO] connected to hivemind: " + address)
    bridge = JarbasTwitchBridge(oauth=oauth, channel=channel,
                                username=username, headers=headers,
                                useragent=useragent)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, bridge, contextFactory)
    reactor.run()


if __name__ == '__main__':
    BOTNAME = "Jarbas_BOT"
    PASS = "oauth:XXX"
    CHANNELNAME = "jarbasai"
    connect_to_twitch(PASS, CHANNELNAME, BOTNAME)
