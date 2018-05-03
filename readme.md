## Jarbas Mycroft Hive

Join the mycroft collective, utils for mycroft-core mesh networking

## Components

- Minds
- Drones
- Nodes
- Terminals
- Bridges

## Concept

Set of 3 skills

    telepathy_mind
    telepathy_drone
    telepathy_hivemind

* mind - turns that mycroft-core instance into a mycroft server
* drone - turns that mycroft-core instance to a mind client, all kinds of messagebus interactions are possible
* hivemind - get a list of public(or not) minds, ask them all everything, this would be a volunteer network of everyone using the skill, i got a skill installed that solves your problem? you got the answer

Building your own Hive

* terminals - standalone connections to interface with a Hive Mind
* nodes - direct connections to a mycroft-core instance messagebus, provide micro services
* bridges - connect external services to a Hive Mind, useful for chatbots