import logging
import sys
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasTwitterBridgev0.1"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")

import json

from twitter import Api


class TwitterMonitor:
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, users=None, languages=None):
        if isinstance(users, str):
            users = [users]
        # Users to watch for should be a list. This will be joined by Twitter and the
        # data returned will be for any tweet mentioning:
        # @user1 *OR* @user2 *OR* @user3.
        self.users = users or []
        # Languages to filter tweets by is a list. This will be joined by Twitter
        # to return data mentioning tweets only in the english language.
        self.languages = languages or ['en']

        # Since we're going to be using a streaming endpoint, there is no need to worry
        # about rate limits.
        self.api = Api(consumer_key, consumer_secret,
                       access_token, access_token_secret)
        self.handle_tweet = []

    def on_tweet(self, handler):
        assert hasattr(handler, "__call__")
        self.handle_tweet += [handler]

    def run(self):
        # api.GetStreamFilter will return a generator that yields one status
        # message (i.e., Tweet) at a time as a JSON dictionary.
        for tweet in self.api.GetStreamFilter(track=self.users,
                                              languages=self.languages):
            for handler in self.handle_tweet:
                handler(tweet, self)


class JarbasTwitterBridgeProtocol(WebSocketClientProtocol):
    twitr = None
    monitor_thread = None
    CONSUMER_KEY = 'XXX'
    # CONSUMER_KEY = os.getenv("CONSUMER_KEY", None)
    CONSUMER_SECRET = 'XXX'
    # CONSUMER_SECRET = os.getenv("CONSUMER_SECRET", None)
    ACCESS_TOKEN = 'XXX'
    # ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
    ACCESS_TOKEN_SECRET = 'XXX'
    # ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", None)

    USERS = ['@jarbasAi']

    LANGUAGES = ['en']

    def start_monitoring(self):
        self.twitr = TwitterMonitor(self.CONSUMER_KEY, self.CONSUMER_SECRET,
                                    self.ACCESS_TOKEN,
                                    self.ACCESS_TOKEN_SECRET,
                                    self.USERS, self.LANGUAGES)
        self.twitr.on_tweet(self.handle_tweet)
        self.twitr.run()

    def handle_tweet(self, data, twitr):
        mention = data["in_reply_to_screen_name"]
        text = data["text"]
        user = data["user"]["screen_name"]
        utterance = text.replace("@" + mention, "")
        msg = {"data": {"utterances": [utterance],
                        "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": {"source": self.peer,
                           "destination": "hive_mind",
                           "platform": platform,
                           "user": user}}
        msg = json.dumps(msg)
        msg = bytes(msg, encoding="utf-8")
        self.sendMessage(msg, False)

    def onConnect(self, response):
        logger.info("[INFO] Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

        self.CONSUMER_KEY = self.factory.CONSUMER_KEY
        self.CONSUMER_SECRET = self.factory.CONSUMER_SECRET
        self.ACCESS_TOKEN = self.factory.ACCESS_TOKEN
        self.ACCESS_TOKEN_SECRET = self.factory.ACCESS_TOKEN_SECRET
        self.USERS = self.factory.USERS
        self.LANGUAGES = self.factory.LANGUAGES

    def onOpen(self):
        logger.info("[INFO] WebSocket connection open. ")
        self.monitor_thread = Thread(target=self.start_monitoring)
        self.monitor_thread.setDaemon(True)
        self.monitor_thread.start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            utterance = ""
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
            elif msg.get("type", "") == "server.complete_intent_failure":
                utterance = "does not compute"

            if utterance:
                user = msg["context"]["user"]
                self.twitr.api.PostUpdate("@" + user + " " + utterance)
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("[INFO] WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"


class JarbasTwitterBridge(WebSocketClientFactory,
                          ReconnectingClientFactory):
    protocol = JarbasTwitterBridgeProtocol
    CONSUMER_KEY = 'XXX'
    # CONSUMER_KEY = os.getenv("CONSUMER_KEY", None)
    CONSUMER_SECRET = 'XXX'
    # CONSUMER_SECRET = os.getenv("CONSUMER_SECRET", None)
    ACCESS_TOKEN = 'XXX'
    # ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
    ACCESS_TOKEN_SECRET = 'XXX'
    # ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", None)

    USERS = ['@jarbasAi']

    LANGUAGES = ['en']

    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, users, languages=None,
                 name="twitter bridge", *args, **kwargs):
        super(JarbasTwitterBridge, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.name = name
        self.client = None
        self.CONSUMER_KEY = consumer_key
        self.CONSUMER_SECRET = consumer_secret
        self.ACCESS_TOKEN = access_token
        self.ACCESS_TOKEN_SECRET = access_token_secret
        self.USERS = users
        self.LANGUAGES = languages or ["en"]

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



