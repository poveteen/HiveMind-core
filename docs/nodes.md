# Hive Nodes

Hive nodes are micro services that interface with a mycroft-core instance

Nodes are assumed to connect directly to the mycroft-core messagebus and not go through a mind

Nodes may need to be started before the skills process if they need to listen to bus messages

# Node Examples

* [flask hive node](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/nodes/flask) provides a REST http(s) endpoint, allows you to query registered intents, ask questions to mycroft among other things
* [webchat hive node](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/nodes/webchat), serves a local web chat



