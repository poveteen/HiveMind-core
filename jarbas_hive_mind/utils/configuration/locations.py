try:
    from mycroft.configuration.locations import *
except ImportError:
    from os.path import join, dirname, expanduser

    DEFAULT_CONFIG = join(dirname(__file__), 'mycroft.conf')
    SYSTEM_CONFIG = '/etc/mycroft/mycroft.conf'
    USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')
    REMOTE_CONFIG = "mycroft.ai"
