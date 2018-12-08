import base64
import json
import logging
import random
import sys
from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from remi import start, App, gui
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

logger = logging.getLogger("Standalone_Jarbas_Remi_Client")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")

platform = "JarbasREMITerminalv0.1"


class JarbasRemiClientProtocol(WebSocketClientProtocol):
    remi = None

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        RemiClient.protocol = self

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("Output: " + utterance)
                RemiClient.history_widget.append(
                    "Jarbas: " + utterance.lower())
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))
        self.factory.client = None
        self.factory.status = "disconnected"


class JarbasRemiClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasRemiClientProtocol

    def __init__(self, *args, **kwargs):
        super(JarbasRemiClientFactory, self).__init__(*args, **kwargs)
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


class RemiClient(App):
    protocol = None
    history_widget = None
    suggestions = ["hello world",
                   "do you like pizza",
                   "tell me about nicola tesla",
                   "tell me a joke"]
    host = "127.0.0.1"
    port = 5678
    name = "standalone remi client"
    api = "test_key"

    def __init__(self, *args):
        super(RemiClient, self).__init__(*args)

    def main(self):
        authorization = self.name + ":" + self.api
        usernamePasswordDecoded = bytes(authorization, "utf-8")
        api = base64.b64encode(usernamePasswordDecoded)
        headers = {'authorization': api}
        address = u"wss://" + self.host + u":" + str(self.port)
        factory = JarbasRemiClientFactory(address, headers=headers,
                                          useragent=platform)
        factory.protocol = JarbasRemiClientProtocol
        contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(self.host, self.port, factory, contextFactory)

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

        RemiClient.history_widget = gui.ListView.new_from_list((), width=500,
                                                               height=300,
                                                               margin='10px')

        self.txt_input = gui.TextInput(width=400, height=30, margin='10px')
        self.txt_input.set_text('chat: ')
        self.txt_input.set_on_change_listener(self.on_chat_type)
        # self.txt_input.set_on_enter_listener(self.on_chat_enter)

        send_button = gui.Button('Send', width=150, height=30, margin='10px')
        send_button.set_on_click_listener(self.on_chat_click)

        sug_button = gui.Button('Suggestion', width=150, height=30,
                                margin='10px')
        sug_button.set_on_click_listener(self.on_suggestion_click)

        chatButtonContainer.append(send_button)
        chatButtonContainer.append(sug_button)

        verticalContainer.append(self.txt_input)
        verticalContainer.append(chatButtonContainer)
        verticalContainer.append(RemiClient.history_widget)
        return verticalContainer

    def on_suggestion_click(self, widget):
        sug = random.choice(self.suggestions)
        self.txt_input.set_text('chat: ' + sug)
        self.utterance = sug

    def on_chat_type(self, widget, newValue):
        self.utterance = str(newValue)

    def on_chat_click(self, widget):
        self.utterance = self.utterance.replace("chat:", "").lower()
        msg = {"data": {"utterances": [self.utterance], "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": {"source": RemiClient.protocol.peer,
                           "destinatary":
                               "https_server", "platform": platform}}
        msg = json.dumps(msg)
        RemiClient.protocol.sendMessage(bytes(msg, "utf-8"), False)

        RemiClient.history_widget.append("you: " + self.utterance.replace("chat:",
                                                                          "").lower())
        self.txt_input.set_text('chat: ')
        self.utterance = ""

    def on_chat_enter(self, widget, userData):
        self.utterance = userData.replace("chat:", "").lower()

        msg = {"data": {"utterances": [self.utterance], "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": {"source": RemiClient.protocol.peer,
                           "destinatary":
                               "https_server", "platform": platform}}
        msg = json.dumps(msg)
        RemiClient.protocol.sendMessage(bytes(msg, "utf-8"), False)

        RemiClient.history_widget.append("you: " + self.utterance.replace("chat:",
                                                                          "").lower())
        self.txt_input.set_text('chat: ')
        self.utterance = ""


def connect_to_hivemind_server(host="127.0.0.1", port=5678, name="standalone remi terminal",
                               api="test_key", remi_host='127.0.0.1', remi_port=8171):
    RemiClient.host = host
    RemiClient.port = port
    RemiClient.name = name
    RemiClient.api = api
    start(RemiClient, address=remi_host, port=remi_port, multiple_instance=True,
          enable_file_cache=True, update_interval=0.1, start_browser=False)


def connect_to_hivemind_standalone(host="127.0.0.1", port=5678, name="standalone remi terminal", api="test_key"):
    RemiClient.host = host
    RemiClient.port = port
    RemiClient.name = name
    RemiClient.api = api
    start(RemiClient, standalone=True)


if __name__ == "__main__":
    connect_to_hivemind_server()
