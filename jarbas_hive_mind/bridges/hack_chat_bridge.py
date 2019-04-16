import base64
import json
import logging
import sys
from threading import Thread
from time import sleep

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasHackChatBridgev0.2"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class HackChat:
    """A library to connect to https://hack.chat.
    <on_message> is <list> of callback functions to receive data from
    https://hack.chat. Add your callback functions to this attribute.
    e.g., on_message += [my_callback]
    The callback function should have 3 parameters, the first for the
    <HackChat> object, the second for the message someone sent and the
    third for the nickname of the sender of the message.

    https://github.com/gkbrk/hackchat
    """

    def __init__(self, nick, channel="programming", debug=True):
        """Connects to a channel on https://hack.chat.
        Keyword arguments:
        nick -- <str>; the nickname to use upon joining the channel
        channel -- <str>; the channel to connect to on https://hack.chat
        """

        import websocket
        self.debug = debug
        self.nick = nick
        self.channel = channel
        self.online_users = []
        self.on_message = []
        self.on_join = []
        self.on_open = []
        self.on_leave = []
        self.ws = websocket.create_connection("wss://hack.chat/chat-ws")
        self._send_packet({"cmd": "join", "channel": channel, "nick": nick})
        Thread(target=self._ping_thread).start()

    def send_message(self, msg):
        """Sends a message on the channel."""
        self._send_packet({"cmd": "chat", "text": msg})

    def _send_packet(self, packet):
        """Sends <packet> (<dict>) to https://hack.chat."""
        encoded = json.dumps(packet)
        self.ws.send(encoded)

    def run(self):
        """Sends data to the callback functions."""
        while True:
            result = json.loads(self.ws.recv())
            if self.debug:
                print(result)

            if result["cmd"] == "chat" and not result["nick"] == self.nick:
                for handler in list(self.on_message):
                    handler(self, result["text"], result["nick"])
            elif result["cmd"] == "onlineAdd":
                self.online_users.append(result["nick"])
                for handler in list(self.on_join):
                    handler(self, result["nick"])
            elif result["cmd"] == "onlineRemove":
                self.online_users.remove(result["nick"])
                for handler in list(self.on_leave):
                    handler(self, result["nick"])
            elif result["cmd"] == "onlineSet":
                for nick in result["nicks"]:
                    self.online_users.append(nick)
                for handler in list(self.on_open):
                    handler(self, result["nicks"])

    def _ping_thread(self):
        """Retains the websocket connection."""
        while self.ws.connected:
            self._send_packet({"cmd": "ping"})
            sleep(60)


class JarbasHackChatBridgeProtocol(WebSocketClientProtocol):
    hackchat = None
    chat_thread = None
    username = "Jarbas_BOT"
    hack_chat_channel = "JarbasAI"

    @property
    def online_users(self):
        try:
            return self.hackchat.online_users
        except:
            return []

    def start_hack_chat(self):
        self.hackchat = HackChat(self.username, self.hack_chat_channel)
        self.hackchat.on_message += [self.on_hack_message]
        self.hackchat.on_join += [self.on_hack_join]
        self.hackchat.on_open += [self.on_hack_open]
        self.hackchat.on_leave += [self.on_hack_leave]
        self.hackchat.run()

    def on_hack_open(self, connector, users):
        if len(users) == 1:
            self.hackchat.send_message("This channel belongs to me")
        else:
            self.hackchat.send_message("I see {} online users"
                                       .format(len(users) - 1))

    def on_hack_join(self, connector, user):
        self.hackchat.send_message("Hello @{}".format(user))

    def on_hack_leave(self, connector, user):
        self.hackchat.send_message("@{} vanished from cyberspace".format(user))

    def on_hack_message(self, connector, message, user):
        utterance = message.lower().strip()
        if "@" + self.username.lower() in utterance:
            utterance = utterance.replace("@" + self.username.lower(), "")
            msg = {"data": {"utterances": [utterance], "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {
                       "source": self.peer,
                       "destination": "hive_mind",
                       "platform": platform,
                       "hack_chat_nick": user,
                       "user": user}}
            msg = json.dumps(msg)
            msg = bytes(msg, encoding="utf-8")
            self.sendMessage(msg, False)

    def onConnect(self, response):
        logger.info("[INFO] " + "Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"
        self.username = self.factory.username
        self.hack_chat_channel = self.factory.channel
        logger.info("[INFO] " + "Channel: {0}".format(self.hack_chat_channel))
        logger.info("[INFO] " + "Username: {0}".format(self.username))

    def onOpen(self):
        logger.info("[INFO] " + "WebSocket connection open. ")
        self.chat_thread = Thread(target=self.start_hack_chat)
        self.chat_thread.setDaemon(True)
        self.chat_thread.start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            user = msg.get("context", {}).get("hack_chat_nick", "")
            if user not in self.online_users:
                logger.error("[ERROR] " + "invalid hack chat user: " + user)
                return
            utterance = ""
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
            elif msg.get("type", "") == "server.complete_intent_failure":
                utterance = "i can't answer that yet"

            if utterance:
                utterance = "@{} , ".format(user) + utterance
                self.hackchat.send_message(utterance)
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info(
            "[INFO] " + "WebSocket connection closed: {0}".format(reason))
        if self.chat_thread:
            self.chat_thread.join(0)
        self.hackchat = None
        self.factory.client = None
        self.factory.status = "disconnected"
        if "Internalservererror:InvalidAPIkey" in reason:
            logger.error("[ERROR] invalid user:key provided")
            raise ConnectionAbortedError("invalid user:key provided")


class JarbasHackChatBridge(WebSocketClientFactory,
                           ReconnectingClientFactory):
    protocol = JarbasHackChatBridgeProtocol

    def __init__(self, username, channel, *args, **kwargs):
        super(JarbasHackChatBridge, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None
        self.username = username
        self.channel = channel

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("[INFO] " + "Client connection failed: " + str(
            reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("[INFO] " + "Client connection lost: " + str(
            reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)


def connect_to_hackchat(channel, username="Jarbas_BOT", host="127.0.0.1",
                        port=5678, name="Jarbas HackChat Bridge",
                        api="hackchat_key", useragent=platform):
    authorization = bytes(name + ":" + api, encoding="utf-8")
    usernamePasswordDecoded = authorization
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    logger.info("[INFO] connected to hivemind: " + address)
    bridge = JarbasHackChatBridge(channel=channel, username=username,
                                  headers=headers, useragent=useragent)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, bridge, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO arg parse
    connect_to_hackchat("JarbasAI_bot")
