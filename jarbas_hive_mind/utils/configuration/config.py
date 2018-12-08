# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
from os.path import exists, isfile

from jarbas_hive_mind.utils import load_commented_json, merge_dict
from jarbas_hive_mind.utils.configuration.locations import DEFAULT_CONFIG, \
    SYSTEM_CONFIG, USER_CONFIG
from jarbas_hive_mind.utils.log import LOG


class LocalConf(dict):
    """
        Config dict from file.
    """

    def __init__(self, path):
        super(LocalConf, self).__init__()
        if path:
            self.path = path
            self.load_local(path)

    def load_local(self, path):
        """
            Load local json file into self.

            Args:
                path (str): file to load
        """
        if exists(path) and isfile(path):
            try:
                config = load_commented_json(path)
                for key in config:
                    self.__setitem__(key, config[key])

                LOG.debug("Configuration {} loaded".format(path))
            except Exception as e:
                LOG.error("Error loading configuration '{}'".format(path))
                LOG.error(repr(e))
        else:
            LOG.debug("Configuration '{}' not found".format(path))

    def store(self, path=None):
        """
            Cache the received settings locally. The cache will be used if
            the remote is unreachable to load settings that are as close
            to the user's as possible
        """
        path = path or self.path
        with open(path, 'w') as f:
            json.dump(self, f)

    def merge(self, conf):
        merge_dict(self, conf)


class Configuration(object):
    __config = {}  # Cached config
    __patch = {}  # Patch config that skills can update to override config

    @staticmethod
    def get(configs=None, cache=True):
        """
            Get configuration, returns cached instance if available otherwise
            builds a new configuration dict.

            Args:
                configs (list): List of configuration dicts
                cache (boolean): True if the result should be cached
        """
        if Configuration.__config:
            return Configuration.__config
        else:
            return Configuration.load_config_stack(configs, cache)

    @staticmethod
    def load_config_stack(configs=None, cache=False):
        """
            load a stack of config dicts into a single dict

            Args:
                configs (list): list of dicts to load
                cache (boolean): True if result should be cached

            Returns: merged dict of all configuration files
        """
        if not configs:
            configs = [LocalConf(DEFAULT_CONFIG), LocalConf(SYSTEM_CONFIG),
                       LocalConf(USER_CONFIG), Configuration.__patch]
        else:
            # Handle strings in stack
            for index, item in enumerate(configs):
                if isinstance(item, str):
                    configs[index] = LocalConf(item)

        # Merge all configs into one
        base = {}
        for c in configs:
            merge_dict(base, c)

        # copy into cache
        if cache:
            Configuration.__config.clear()
            for key in base:
                Configuration.__config[key] = base[key]
            return Configuration.__config
        else:
            return base

    @staticmethod
    def init(ws):
        """
            Setup websocket handlers to update config.

            Args:
                ws:     Websocket instance
        """
        ws.on("configuration.updated", Configuration.updated)
        ws.on("configuration.patch", Configuration.patch)

    @staticmethod
    def updated(message):
        """
            handler for configuration.updated, triggers an update
            of cached config.
        """
        Configuration.load_config_stack(cache=True)

    @staticmethod
    def patch(message):
        """
            patch the volatile dict usable by skills

            Args:
                message: Messagebus message should contain a config
                         in the data payload.
        """
        config = message.data.get("config", {})
        merge_dict(Configuration.__patch, config)
        Configuration.load_config_stack(cache=True)
