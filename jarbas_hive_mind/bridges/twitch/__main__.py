import base64
from twisted.internet import reactor, ssl
from jarbas_hive_mind.bridges.twitch import platform, logger, JarbasTwitchBridge


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
