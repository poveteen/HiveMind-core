from setuptools import setup

setup(
    name='jarbas_hive_mind',
    version='0.1',
    packages=['jarbas_hive_mind', 'jarbas_hive_mind.minds', 'jarbas_hive_mind.nodes', 'jarbas_hive_mind.nodes.flask',
              'jarbas_hive_mind.nodes.webchat', 'jarbas_hive_mind.utils', 'jarbas_hive_mind.drones',
              'jarbas_hive_mind.bridges', 'jarbas_hive_mind.database', 'jarbas_hive_mind.terminals',
              'jarbas_hive_mind.terminals.speech', 'jarbas_hive_mind.terminals.speech.stt',
              'jarbas_hive_mind.terminals.speech.recognizer', 'jarbas_hive_mind.terminals.webchat'],
    url='https://github.com/JarbasAl/hive_mind',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Telepathy for mycroft core'
)