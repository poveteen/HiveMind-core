import base64
import json
import logging
import random
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from remi import start, App, gui
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasREMITerminalv0.1"

logger = logging.getLogger(platform)
logger.setLevel("INFO")


class JarbasRemiTerminalProtocol(WebSocketClientProtocol):
    remi = None

    def onConnect(self, response):
        logger.info("[INFO] Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("[INFO] WebSocket connection open. ")
        RemiTerminal.protocol = self

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("[OUTPUT] " + utterance)
                RemiTerminal.history_widget.append(
                    "Jarbas: " + utterance.lower())
            elif msg.get("type", "") == "hive.complete_intent_failure":
                logger.error("[ERROR] complete intent failure")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("[INFO] WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"
        if "Internalservererror:InvalidAPIkey" in reason:
            logger.error("[ERROR] invalid user:key provided")
            # TODO show something in UI ?
            raise ConnectionAbortedError("invalid user:key provided")


class JarbasRemiTerminal(WebSocketClientFactory,
                         ReconnectingClientFactory):
    protocol = JarbasRemiTerminalProtocol

    def __init__(self, *args, **kwargs):
        super(JarbasRemiTerminal, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("[INFO] Client connection failed: " + str(reason) +
                    " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("[INFO] Client connection lost: " + str(reason) +
                    " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)


class RemiTerminal(App):
    protocol = None
    history_widget = None
    suggestions = ["hello world",
                   "do you like pizza",
                   "tell me about nicola tesla",
                   "tell me a joke"]
    host = "127.0.0.1"
    port = 5678
    name = "Jarbas Remi Terminal"
    key = "remi_key"
    authorization = bytes(name + ":" + key, encoding="utf-8")
    usernamePasswordDecoded = authorization
    key = base64.b64encode(usernamePasswordDecoded)

    def __init__(self, *args):
        super(RemiTerminal, self).__init__(*args)

    def main(self):
        authorization = bytes(self.name + ":" + self.key, encoding="utf-8")
        usernamePasswordDecoded = authorization
        key = base64.b64encode(usernamePasswordDecoded)

        headers = {'authorization': key}
        adress = u"wss://" + self.host + u":" + str(self.port)
        terminal = JarbasRemiTerminal(adress, headers=headers,
                                      useragent=platform)
        contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(self.host, self.port, terminal, contextFactory)

        self.reactor_loop = Thread(target=reactor.run)
        self.reactor_loop.setDaemon(True)
        self.reactor_loop.start()

        # returning the root widget
        return self.get_chat_widget()

    def get_chat_widget(self):
        verticalContainer = gui.Widget(width=400, margin='0px auto',
                                       style={'display': 'block',
                                              'overflow': 'hidden'})
        chatButtonContainer = gui.Widget(width=400,
                                         layout_orientation=gui.Widget.LAYOUT_HORIZONTAL,
                                         margin='0px',
                                         style={'display': 'block',
                                                'overflow': 'auto'})

        RemiTerminal.history_widget = gui.ListView.new_from_list((), width=500,
                                                                 height=300,
                                                                 margin='10px')

        self.txt_input = gui.TextInput(width=400, height=30, margin='10px')
        self.txt_input.set_on_change_listener(self.on_chat_enter)

        send_button = gui.Button('Send', width=150, height=30, margin='10px')
        send_button.set_on_click_listener(self.on_chat_click)

        sug_button = gui.Button('Suggestion', width=150, height=30,
                                margin='10px')
        sug_button.set_on_click_listener(self.on_suggestion_click)

        chatButtonContainer.append(send_button)
        chatButtonContainer.append(sug_button)

        verticalContainer.append(self.txt_input)
        verticalContainer.append(chatButtonContainer)
        verticalContainer.append(RemiTerminal.history_widget)
        return verticalContainer

    def on_suggestion_click(self, widget):
        sug = random.choice(self.suggestions)
        self.txt_input.set_text(sug)
        self.utterance = sug

    def on_chat_type(self, widget, newValue):
        self.utterance = str(newValue)

    def on_chat_click(self, widget):
        self.utterance = self.utterance.strip()
        if self.utterance:
            msg = {"data": {"utterances": [self.utterance], "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {"source": RemiTerminal.protocol.peer,
                               "destination": "hive_mind",
                               "platform": platform}}
            msg = json.dumps(msg)
            msg = bytes(msg, encoding="utf-8")
            RemiTerminal.protocol.sendMessage(msg, False)

            RemiTerminal.history_widget.append(
                "you: " + self.utterance.strip())
            self.txt_input.set_text('')
            self.utterance = ""

    def on_chat_enter(self, widget, userData):
        self.utterance = userData.strip()
        if self.utterance:
            msg = {"data": {"utterances": [self.utterance], "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {"source": RemiTerminal.protocol.peer,
                               "destination": "hive_mind",
                               "platform": platform}}
            msg = json.dumps(msg)
            msg = bytes(msg, encoding="utf-8")
            RemiTerminal.protocol.sendMessage(msg, False)

            RemiTerminal.history_widget.append(
                "you: " + self.utterance.strip())
            self.txt_input.set_text('')
            self.utterance = ""



