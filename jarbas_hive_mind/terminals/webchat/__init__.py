#!/usr/bin/env python
import json
import logging
import os
from subprocess import check_output
from threading import Thread

import tornado.httpserver
import tornado.options
import tornado.web
import tornado.websocket
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet.protocol import ReconnectingClientFactory

platform = "JarbasWebChatTerminalv0.1"
logger = logging.getLogger(platform)
logger.setLevel("INFO")

ip = check_output([b'hostname', b'--all-ip-addresses']) \
    .decode("utf-8").split()[-1]
port = 8286
clients = {}
lang = "en-us"


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html', ip=ip, port=port)


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('js/app.js')


class JarbasWebChatTerminalProtocol(WebSocketClientProtocol):
    chat = None
    config = {"port": port,
              "ssl": False}

    def onConnect(self, response):
        logger.info("[INFO] Server connected: {0}".format(response.peer))

    def onOpen(self):
        logger.info("[INFO] WebSocket connection open. ")
        self.factory.client = self
        self.factory.status = "connected"
        self.webchat = Thread(target=self.serve_chat)
        self.webchat.setDaemon(True)
        self.webchat.start()

    def serve_chat(self):
        WebSocketHandler.server = self
        port = self.config.get("port", 8286)
        cert = self.config.get("cert_file", "")
        key = self.config.get("key_file", "")

        tornado.options.parse_command_line()

        routes = [
            tornado.web.url(r"/", MainHandler, name="main"),
            tornado.web.url(r"/static/(.*)", tornado.web.StaticFileHandler,
                            {'path': './'}),
            tornado.web.url(r"/ws", WebSocketHandler)
        ]

        settings = {
            "debug": True,
            "template_path": os.path.join(os.path.dirname(__file__),
                                          "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
        }

        application = tornado.web.Application(routes, **settings)
        if self.config.get("ssl", False):
            httpServer = tornado.httpserver.HTTPServer(application,
                                                       ssl_options={
                                                           "certfile": cert,
                                                           "keyfile": key
                                                       })
            url = "https://" + str(ip) + ":" + str(port)
        else:
            httpServer = tornado.httpserver.HTTPServer(application)
            url = "http://" + str(ip) + ":" + str(port)

        tornado.options.parse_command_line()

        logger.info("[INFO] Access from web browser " + url)

        httpServer.listen(port)
        tornado.ioloop.IOLoop.instance().start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("[OUTPUT] " + utterance)
                if self.chat is not None:
                    self.chat.write_message(utterance)
            elif msg.get("type", "") == "hive.complete_intent_failure":
                logger.error("[ERROR] complete intent failure")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("[INFO] WebSocket connection closed: {0}".format(reason))
        if "Internalservererror:InvalidAPIkey" in reason:
            logger.error("[ERROR] invalid user:key provided")
            # TODO show something in web ui?
            raise ConnectionAbortedError("invalid user:key provided")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    peer = "unknown"
    server = None

    def open(self):
        logger.info('[INFO] Client IP: ' + self.request.remote_ip)
        self.peer = self.request.remote_ip
        clients[self.peer] = self
        self.write_message("Welcome to Jarbas Web Client")
        self.server.chat = self

    def on_message(self, message):
        utterance = message.strip()

        if utterance:
            logger.info("[INFO] Utterance : " + utterance)
            data = {"utterances": [utterance], "lang": lang}
            context = {"source": self.peer,
                       "destination": "hive_mind",
                       "platform": platform}
            msg = {"data": data,
                   "type": "recognizer_loop:utterance",
                   "context": context}
            msg = json.dumps(msg)
            msg = bytes(msg, encoding="utf-8")
            self.server.sendMessage(msg, False)

    def on_close(self):
        global clients
        try:
            clients.pop(self.peer)
        except:
            pass


class JarbasWebChatTerminal(WebSocketClientFactory,
                            ReconnectingClientFactory):
    protocol = JarbasWebChatTerminalProtocol

    def __init__(self, *args, **kwargs):
        super(JarbasWebChatTerminal, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("[INFO] Client connection failed: " + str(
            reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("[INFO] Client connection lost: " + str(
            reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)


