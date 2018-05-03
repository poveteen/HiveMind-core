## Hive Drone

Attempts to connect to a Hive Mind through secure websocket connection, interact with mycroft-core message bus

Forwards every message from the Hive Mind to the message bus

## Message Bus API

informational messages

    "hivemind.mind.websocket.open"
    "hivemind.mind.connected" - {"server_id": response.headers["server"]}
    "hivemind.mind.message.sent" - {"type": type, "data": data, "context": context, "raw": msg.json}
    "hivemind.mind.message.received" - {"type": type, "data": data, "context": context, "raw": msg.json}
    "hivemind.mind.connection.closed" - {"wasClean": wasClean, "reason": reason, "code": code}

listens for

    "hivemind.mind.message.send" - {payload": json_message, "isBinary": False}


## Configuration

add a section to your config file (optional)

    "hivemind": {
        "drone": {
            "port": 5678,
            "host": "0.0.0.0",
            "ssl": False,
            "cert": "path/to/ssl.crt",
            "key": "path/to/ssl.key"
        }
    }