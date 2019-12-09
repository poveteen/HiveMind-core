from jarbas_hive_mind.terminals.basic_web import RemiTerminal, start


def connect_to_hivemind_server(host="127.0.0.1", port=5678,
                               name="Jarbas Remi Terminal",
                               key="remi_key", remi_host='127.0.0.1',
                               remi_port=8171):
    RemiTerminal.host = host
    RemiTerminal.port = port
    RemiTerminal.name = name
    RemiTerminal.key = key
    start(RemiTerminal, address=remi_host, port=remi_port,
          multiple_instance=True,
          enable_file_cache=True, update_interval=0.1, start_browser=False)


def connect_to_hivemind_standalone(host="127.0.0.1", port=5678,
                                   name="Jarbas Remi Terminal",
                                   key="remi_key"):
    RemiTerminal.host = host
    RemiTerminal.port = port
    RemiTerminal.name = name
    RemiTerminal.key = key
    start(RemiTerminal, standalone=True)


if __name__ == "__main__":
    # TODO argparse
    connect_to_hivemind_server()