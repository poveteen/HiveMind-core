import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(os.path.dirname(__file__), requirements_file),
              'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


setup(
    name='jarbas_hive_mind',
    version='0.2.1',
    packages=['jarbas_hive_mind',
              'jarbas_hive_mind.minds',
              'jarbas_hive_mind.nodes',
              'jarbas_hive_mind.nodes.flask',
              'jarbas_hive_mind.utils',
              'jarbas_hive_mind.utils.messagebus',
              'jarbas_hive_mind.drones',
              'jarbas_hive_mind.bridges',
              'jarbas_hive_mind.database',
              'jarbas_hive_mind.terminals',
              'jarbas_hive_mind.terminals.speech',
              'jarbas_hive_mind.terminals.speech.stt',
              'jarbas_hive_mind.terminals.speech.recognizer',
              'jarbas_hive_mind.terminals.camera',
              'jarbas_hive_mind.terminals.webchat'],
    package_data={'': package_files('jarbas_hive_mind')},
    include_package_data=True,
    install_requires=required('requirements.txt'),
    url='https://github.com/JarbasAl/hive_mind',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Telepathy for mycroft core'
)
