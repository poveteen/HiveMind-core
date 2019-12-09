from jarbas_hive_mind.terminals.https import JarbasMicroServicesAPI, logger


def connect_to_hivenode(key="test_key",
                        url="https://0.0.0.0:6712/"):

    ap = JarbasMicroServicesAPI(key, url)
    while True:
        line = input("Input: ")
        res = ap.ask_mycroft(line.lower())
        logger.info("Jarbas: " + res.get("data", {})
                    .get("utterance", "does not compute"))


if __name__ == "__main__":
    # TODO argparse
    connect_to_hivenode()

