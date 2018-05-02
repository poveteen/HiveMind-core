from setuptools import setup

setup(
    name='jarbas_hive_mind',
    version='0.1',
    packages=['jarbas_hive_mind', 'jarbas_hive_mind.bridges', 'jarbas_hive_mind.terminals',
              'jarbas_hive_mind.terminals.speech', 'jarbas_hive_mind.terminals.speech.stt',
              'jarbas_hive_mind.terminals.speech.recognizer', 'jarbas_hive_mind.terminals.webchat'],
    url='',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Telepathy for mycroft core'
)
