import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('jarbas_hive_mind')
setup(
    name='jarbas_hive_mind',
    version='0.2',
    packages=['jarbas_hive_mind', 'jarbas_hive_mind.minds',
              'jarbas_hive_mind.nodes', 'jarbas_hive_mind.nodes.flask',
              'jarbas_hive_mind.nodes.webchat', 'jarbas_hive_mind.utils',
              'jarbas_hive_mind.drones',
              'jarbas_hive_mind.bridges', 'jarbas_hive_mind.database',
              'jarbas_hive_mind.terminals',
              'jarbas_hive_mind.terminals.speech',
              'jarbas_hive_mind.terminals.speech.stt',
              'jarbas_hive_mind.terminals.speech.recognizer',
              'jarbas_hive_mind.terminals.webchat'],
    url='https://github.com/JarbasAl/hive_mind',
    license='MIT',
    package_data={'': extra_files},
    include_package_data=True,
    install_requires=['pyopenssl',
                      'service_identity',
                      'flask',
                      'flask-sslify',
                      'yagmail',
                      'autobahn',
                      'twisted',
                      'sqlalchemy',
                      'tornado==4.5.3',
                      'SpeechRecognition',
                      'responsivevoice',
                      'hclib',
                      'fbchat',
                      'remi'],
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Telepathy for mycroft core'
)
