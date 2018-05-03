# Hive Terminals

Hive Terminals are standalone clients that do not require a local running mycroft-core instance, these connect to a Hive Mind and talk to a remote mycroft instance

# Terminal Examples

* [Command Line Terminal](https://github.com/JarbasAl/hive_mind/blob/master/jarbas_hive_mind/terminals/cli_terminal.py) - chat with a Hive Mind through a command line
* [Voice Terminal](https://github.com/JarbasAl/hive_mind/blob/master/jarbas_hive_mind/terminals/voice_terminal.py) - talk with a Hive Mind by voice, [isolated wake word and STT components](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/terminals/speech) extracted from mycroft-core, [responsive voice TTS](https://github.com/JarbasAl/py_responsivevoice)
* [Remi Terminal](https://github.com/JarbasAl/hive_mind/blob/master/jarbas_hive_mind/terminals/remi_terminal.py) - chat with a Hive Mind through a locally served remi app terminal, can be run as a widget or accessed in browser
* [Webchat Terminal](https://github.com/JarbasAl/hive_mind/blob/master/jarbas_hive_mind/terminals/webchat_terminal.py) - chat with a Hive Mind through a locally served web chat
* [Https Terminal](https://github.com/JarbasAl/hive_mind/blob/master/jarbas_hive_mind/terminals/https_cli_terminal.py) - chat with a [Flask Hive Node](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/nodes/flask) through the terminal, useful if you don't want to use a websocket



