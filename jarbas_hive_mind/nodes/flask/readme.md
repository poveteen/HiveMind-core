## Flask Hive Node

the flask hive node provides a REST http(s) endpoint, allows you to query registered intents, ask questions to mycroft mong other things

## Configuration

add a section to your config file (optional)

    "hivemind": {
        "flask_node": {
            "port": 6712
        }
    }

## API

# Processing an utterance

    from jarbas_hive_mind.nodes.flask import JarbasFlaskHiveNodeAPI

    ap = JarbasFlaskHiveNodeAPI("api_key")
    json_response = ap.ask_mycroft("hello world")

# Admin functions

some functions require an admin api key

    ap = JarbasFlaskHiveNodeAPI("admin_key")

    # get an api key string
    api = ap.generate_key()

    # add a new user
    mail = "fakemail@jarbasai.com"
    name = "anon"
    print ap.new_user(api, mail, name)

    # revoke an api
    print ap.revoke_key(api)

# Determining Intents

    ap = JarbasFlaskHiveNodeAPI("api_key")

    # what intent will this utterance trigger
    intent = ap.get_adapt_intent("hello world")

    # what intents are registered {"skill_id": ["intent", "list"] }
    intent_dict = ap.get_intent_map()

# Determining Vocab

    ap = JarbasFlaskHiveNodeAPI("api_key")

    # what vocab is registered {"word": "MatchingKeyword" }
    intent_dict = ap.get_vocab_map()
