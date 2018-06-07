## Hive Drone

Attempts to connect to a Hive Mind through secure websocket connection, interacts with mycroft-core message bus

Forwards every message from the Hive Mind to the mycroft-core message bus

Requests actions from Hive Mind

A drone may not be a mycroft-core instance, as long as it handles received orders it's considered a drone and not a terminal


## Message Bus API

informational messages

    "hive.mind.websocket.open"
    "hive.mind.connected" - {"server_id": response.headers["server"]}
    "hive.mind.message.sent" - {"type": type, "data": data, "context": context, "raw": msg.json}
    "hive.mind.message.received" - {"type": type, "data": data, "context": context, "raw": msg.json}
    "hive.mind.connection.closed" - {"wasClean": wasClean, "reason": reason, "code": code}

listens for

    "hive.mind.message.send" - {payload": json_message, "isBinary": False}


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