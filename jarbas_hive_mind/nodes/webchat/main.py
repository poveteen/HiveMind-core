#!/usr/bin/env python
#-*- coding:utf-8 -*-
# from mycroft.util import create_signal
import logging
import os
import sys
from os.path import expanduser
from subprocess import check_output
from threading import Thread

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from mycroft.configuration import Configuration
from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG

logger = logging.getLogger("Jarbas_WebChatClient")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")

ip = check_output([b'hostname', b'--all-ip-addresses']).replace(b" \n",
                                                                b"").decode(
    "utf-8")
clients = {}
port = 8092
lang = "en-us"
platform = "JarbasWebChatHiveNodev0.1"


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html',ip=ip,  port=port)


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('js/app.js')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    peer = "unknown"

    def create_internal_emitter(self):
        # connect to mycroft internal websocket
        self.emitter = WebsocketClient()
        self.register_internal_messages()
        self.emitter_thread = Thread(target=self.connect_to_internal_emitter)
        self.emitter_thread.setDaemon(True)
        self.emitter_thread.start()

    def register_internal_messages(self):
        # catch all messages
        self.emitter.on('speak', self.handle_speak)

    def connect_to_internal_emitter(self):
        self.emitter.run_forever()

    def open(self):
        LOG.info('Client IP: ' + self.request.remote_ip)
        self.peer = self.request.remote_ip
        clients[self.peer] = self
        self.create_internal_emitter()
        self.write_message("Welcome to Jarbas Web Client")

    def on_message(self, message):
        utterance = message.strip()
        LOG.info("Utterance : " + utterance)
        if utterance:
            if utterance == '"mic_on"':
                create_signal('startListening')
            else:
                data = {"utterances": [utterance], "lang": lang}
                context = {"source": self.peer, "destinatary":
                           "skills", "client_name": platform, "peer": self.peer}
                self.emitter.emit(Message("recognizer_loop:utterance", data, context))

    def handle_speak(self, event):
        if event.context.get("client_name", platform) == platform:
            peer = event.context.get("peer", "")
            if peer == self.peer:
                self.write_message(event.data['utterance'])

    def on_close(self):
        global clients
        self.emitter.remove("speak", self.handle_speak)
        clients.pop(self.peer)


def launch(config=None):
    import tornado.options

    config = config or Configuration.get().get("hivemind", {}).get("webchat_node", {})
    port = config.get("port", 8286)
    ssl = config.get("ssl", False)
    cert = config.get("cert_file", expanduser('~/.mycroft/hivemind/certs/default.crt'))
    key = config.get("key_file", expanduser('~/.mycroft/hivemind/certs/default.key'))

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
    if ssl:
        httpServer = tornado.httpserver.HTTPServer(application, ssl_options={
            "certfile": cert,
            "keyfile": key
        })
        url = "https://" + str(ip) + ":" + str(port)
    else:
        httpServer = tornado.httpserver.HTTPServer(application)
        url = "http://" + str(ip) + ":" + str(port)

    tornado.options.parse_command_line()

    print("*********************************************************")
    print("*   Access from web browser " + url)
    print("*********************************************************")

    httpServer.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    launch()