import base64
from jarbas_hive_mind.bridges.hackchat import platform, logger, JarbasHackChatBridge
from twisted.internet import reactor, ssl


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
