## Webchat Hive Node

connects to mycroft-core message bus and serves a local webchat page

See code the frontend is based off from on Youtube (https://www.youtube.com/watch?v=J8NGy9UwkPI)

## Configuration

add a section to your config file (optional)

    "hivemind": {
        "webchat_node": {
            "port": 8286
            "ssl": False,
            "cert": "path/to/ssl.crt",
            "key": "path/to/ssl.key"
        }
    }


## Credits

[Jcasoft](https://github.com/jcasoft/Web-Chat-Client-for-Mycroft)

JarbasAI
