#!/usr/bin/env python
import base64
import json
import logging
import os
import sys
from os.path import dirname
from subprocess import check_output
from threading import Thread

import tornado.web
import tornado.websocket
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory

logger = logging.getLogger("Jarbas_WebChatTerminalv0.1")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")

ip = check_output([b'hostname', b'--all-ip-addresses']).replace(b" \n", b"")
port = 8686
clients = {}
lang = "en-us"
platform = "JarbasWebChatClientv0.1"


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html',ip=ip,  port=port)


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('js/app.js')


class JarbasWebChatClientProtocol(WebSocketClientProtocol):
    chat = None
    config = {"port": 8286}

    def onConnect(self, response):
        logger.info("Server connected: {0}".format(response.peer))

    def onOpen(self):
        logger.info("WebSocket connection open. ")
        self.factory.client = self
        self.factory.status = "connected"
        self.webchat = Thread(target=self.serve_chat)
        self.webchat.setDaemon(True)
        self.webchat.start()

    def serve_chat(self):
        import tornado.options
        WebSocketHandler.server = self
        port = self.config.get("port", 8286)
        cert = self.config.get("cert_file",
                          dirname(dirname(dirname(__file__))) + '/certs/JarbasServer.crt')
        key = self.config.get("key_file",
                         dirname(dirname(dirname(__file__))) + '/certs/JarbasServer.key')

        tornado.options.parse_command_line()

        routes = [
            tornado.web.url(r"/", MainHandler, name="main"),
            tornado.web.url(r"/static/(.*)", tornado.web.StaticFileHandler, {'path': './'}),
            tornado.web.url(r"/ws", WebSocketHandler)
        ]

        settings = {
            "debug": True,
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
        }

        application = tornado.web.Application(routes, **settings)
        if self.config.get("ssl", False):
            httpServer = tornado.httpserver.HTTPServer(application, ssl_options={
                "certfile": cert,
                "keyfile": key
            })
            url = "https://" + str(ip) + ":" + str(port)
        else:
            httpServer = tornado.httpserver.HTTPServer(application)
            url = "http://" + ip.decode("utf-8") + ":" + str(port)

        tornado.options.parse_command_line()

        print("*********************************************************")
        print("*   Access from web browser " + url)
        print("*********************************************************")

        httpServer.listen(port)
        tornado.ioloop.IOLoop.instance().start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("Output: " + utterance)
                if self.chat is not None:
                    self.chat.write_message(utterance)
            if msg.get("type", "") == "server.complete_intent_failure":
                logger.error("Output: complete_intent_failure")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    peer = "unknown"
    server = None

    def open(self):
        print('Client IP: ' + self.request.remote_ip)
        self.peer = self.request.remote_ip
        clients[self.peer] = self
        self.write_message("Welcome to Jarbas Web Client")
        self.server.chat = self

    def on_message(self, message):
        utterance = message.strip()
        print("Utterance : " + utterance)
        if utterance:
            if utterance == '"mic_on"':
                pass
            else:
                data = {"utterances": [utterance], "lang": lang}
                context = {"source": self.peer, "destinatary":
                           "skills", "client_name": platform, "peer": self.peer}
                msg = {"data": data,
                       "type": "recognizer_loop:utterance",
                       "context": context}
                msg = json.dumps(msg)
                self.server.sendMessage(bytes(msg, "utf-8"), False)

    def on_close(self):
        global clients
        clients.pop(self.peer)


class JarbasWebChatClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = JarbasWebChatClientProtocol

    def __init__(self, *args, **kwargs):
        super(JarbasWebChatClientFactory, self).__init__(*args, **kwargs)
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
                        port=5678, name="Standalone WebChat Terminal",
                        api="test_key", useragent=platform):
    authorization = name + ":" + api
    usernamePasswordDecoded = bytes(authorization, "utf-8")
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    factory = JarbasWebChatClientFactory(address, headers=headers,
                                         useragent=useragent)
    factory.protocol = JarbasWebChatClientProtocol
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, factory, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO parse args
    connect_to_hivemind()
