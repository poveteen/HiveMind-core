import base64
from twisted.internet import reactor, ssl
from jarbas_hive_mind.bridges.twitter import platform, logger, JarbasTwitterBridge


def connect_to_twitter(consumer_key, consumer_secret, access_token,
                       access_token_secret, users, languages=None,
                       host="127.0.0.1", port=5678,
                       name="Jarbas Twitter Bridge", api="twitter_key",
                       useragent=platform):
    authorization = bytes(name + ":" + api, encoding="utf-8")
    usernamePasswordDecoded = authorization
    api = base64.b64encode(usernamePasswordDecoded)
    headers = {'authorization': api}
    address = u"wss://" + host + u":" + str(port)
    logger.info("[INFO] connecting to hive mind at " + address)
    bridge = JarbasTwitterBridge(consumer_key, consumer_secret, access_token,
                                 access_token_secret, users, languages,
                                 name=name, headers=headers,
                                 useragent=useragent)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, bridge, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO arg parse
    CONSUMER_KEY = 'xx'
    CONSUMER_SECRET = 'Cxxx'
    ACCESS_TOKEN = 'xxxIy'
    ACCESS_TOKEN_SECRET = 'bvUxx'

    USERS = ['@jarbasAi']

    LANGUAGES = ['en']

    connect_to_twitter(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN,
                       ACCESS_TOKEN_SECRET, USERS, LANGUAGES)
