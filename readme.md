# Jarbas Mycroft Hive
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)](https://en.cryptobadges.io/donate/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://paypal.me/jarbasai)
<span class="badge-patreon"><a href="https://www.patreon.com/jarbasAI" title="Donate to this project using Patreon"><img src="https://img.shields.io/badge/patreon-donate-yellow.svg" alt="Patreon donate button" /></a></span>
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/JarbasAl)

Join the mycroft collective, utils for mycroft-core mesh networking

![](hivemind.png)

## Install

activate mycroft virtual env and then

    pip install jarbas_hive_mind
    
or

    git clone https://github.com/JarbasAl/hive-mind
    cd hive-mind
    pip install .
        
## Components

- [Minds](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/minds)
- [Drones](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/drones)
- [Nodes](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/nodes)
- [Terminals](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/terminals)
- [Bridges](https://github.com/JarbasAl/hive_mind/tree/master/jarbas_hive_mind/bridges)

## Concept

Set of 3 skills

    telepathy_mind
    telepathy_drone
    telepathy_collective

* mind - turns that mycroft-core instance into a mycroft server
* drone - turns that mycroft-core instance to a mind client, all kinds of messagebus interactions are possible
* collective - get a list of public(or not) minds, ask them anything, this would be a volunteer network of everyone using the skill, a private list, or a combination


minds parse and filters requests, connecting clients require api keys

drones - pass the bus message along every time, blindly trust hive mind orders


Building your own Hive

* terminals - standalone connections to interface with a Hive Mind
* nodes - direct connections to a mycroft-core instance messagebus, provide micro services
* bridges - connect external services to a Hive Mind, useful for chatbots

## Use Cases

- Create a chatbot, demo for [hack.chat](https://hack.chat/?JarbasAI) and [twitch](https://www.twitch.tv/jarbasai)
- Create a private distributed mycroft network
- Chat rooms / Intercom
- Send binary data across mycroft instances, for example a picture from a camera to a face recognition server
- Ask public hiveminds on fallback, i got a skill installed that solves your problem? you got the answer
- Turn any internet enabled device on a mycroft enabled component
- Talk with mycroft anywhere
- Fully customizable, advanced mesh network structures can be created by combining the available components
