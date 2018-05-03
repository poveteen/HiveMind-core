## Hive Mind

listen for secure websocket connection, interact with mycroft-core  message bus

## Message Bus API

informational messages

    "hive.client.connection.error" - {"error": "invalid api key", "ip": ip, "api_key": api, "platform": platform}
    "hive.client.connect" - {"ip": ip, "headers": request.headers}
    "hive.client.disconnect" - {"ip": ip, "code": code, "reason": "connection closed", "wasClean": wasClean, "sock": sock_num}
    "hive.mind.complete_intent_failure"
    "hive.mind.send.error" - {"error": "That client is not connected", "peer": peer}"

listens for

    'hive.client.broadcast' - {"payload": json_message, "isBinary": False}
    'hive.client.send' - {"peer": peer, "payload": json_message, "isBinary": False}

    forwards all messages with message.context["destinatary"] in self.peers

## Configuration

add a section to your config file (optional)

    "hivemind": {
        "mind": {
            "port": 5678,
            "max_connections": -1,
            "ssl": True,
            "cert": "path/to/ssl.crt",
            "key": "path/to/ssl.key"
        }
    }