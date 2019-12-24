from __future__ import unicode_literals
import json
import logging
import os
from discreetly.backends import AbstractBackend
from discreetly.backends.gcp import GCPBackend
from discreetly.backends.aws import AWSBackend


logger = logging.getLogger(__name__)


class Session(AbstractBackend):
    CONFIG_FILE_ENV = "DISCREETLY_CONFIG_FILE"

    def __init__(self, config=None, profile="default"):
        self.config = None
        self.config_file = None

        if config is not None:
            if isinstance(config, dict):
                self.config = config
            else:
                # assume it represents a path to the config file
                self.config_file = config
        else:
            # load config from path given by env variable
            self.config_file = os.environ.get(
                Session.CONFIG_FILE_ENV, "discreetly.json"
            )

        if self.config_file is not None:
            logger.debug('config_file is: "%s"', self.config_file)
            with open(self.config_file, "r") as configfile:
                self.config = json.load(configfile)

        logger.debug(
            "config:\n%s", json.dumps(self.config, sort_keys=True, indent=4)
        )

        self.profile = self.config.get(profile)
        if self.profile is None:
            raise KeyError('Invalid profile: "%s"' % profile)

        logger.debug(
            "profile:\n%s", json.dumps(self.profile, sort_keys=True, indent=4)
        )

        type = self.profile.get("type")
        if type == "gcp":
            self.backend = GCPBackend(self.profile)
        elif type == "aws":
            self.backend = AWSBackend(self.profile)
        else:
            raise NotImplementedError("Backend %s not implemented." % type)

    @classmethod
    def create(cls, config=None, profile="default"):
        return cls(config, profile)

    def get(self, key, **kwargs):
        """
        Gets the value associated with provided key
        """
        return self.backend.get(key, **kwargs)

    def set(self, key, value, **kwargs):
        """
        Sets the key with the provided value
        """
        return self.backend.set(key, value, **kwargs)

    def delete(self, key, **kwargs):
        return self.backend.delete(key, **kwargs)

    def list(self, path, **kwargs):
        return self.backend.list(path, **kwargs)
