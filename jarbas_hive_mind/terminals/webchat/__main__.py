from jarbas_hive_mind.terminals.webchat import platform, logger, JarbasWebChatTerminal
import base64
from twisted.internet import reactor, ssl


def connect_to_hivemind(host="127.0.0.1",
                        port=5678, name="Jarbas WebChat Terminal",
                        key="webchat_key", useragent=platform):
    authorization = bytes(name + ":" + key, encoding="utf-8")
    usernamePasswordDecoded = authorization
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    logger.info("[INFO] connecting to hive mind at " + address)
    terminal = JarbasWebChatTerminal(address, headers=headers,
                                     useragent=useragent)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, terminal, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO parse args
    connect_to_hivemind()
