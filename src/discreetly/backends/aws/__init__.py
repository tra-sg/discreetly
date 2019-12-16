from __future__ import unicode_literals

import boto3
import logging
from abc import ABCMeta
from future.utils import with_metaclass
from discreetly.backends import AbstractBackend

logger = logging.getLogger(__name__)


class AWSBackend(with_metaclass(ABCMeta, AbstractBackend)):
    def __init__(self, config):
        super(AWSBackend, self).__init__(config)

        self.ssm_client = boto3.client("ssm")
        self.default_keyid = config.get("keyid")

    def get(self, key, **kwargs):
        logger.debug('get "%s"', key)
        key = self._parse_path(key)

        kwargs["WithDecryption"] = self._is_none_or_truthy(
            kwargs.get("WithDecryption")
        )

        response = self.ssm_client.get_parameter(Name=key, **kwargs)
        return response["Parameter"]["Value"]

    def set(self, key, value, **kwargs):
        logger.debug('set "%s"', key)
        key = self._parse_path(key)

        # Order of preference:
        #   1. keyid argument provided
        #   2. default_keyid (from configuration) was set
        #   Otherwise, don't pass a KeyId argument to put_parameter)
        if "keyid" in kwargs:
            # "rename" keyid to KeyId
            kwargs["KeyId"] = kwargs.pop("keyid")
        elif self.default_keyid:
            kwargs["KeyId"] = self.default_keyid

        if "Type" not in kwargs:
            kwargs["Type"] = "SecureString"

        kwargs["Overwrite"] = self._is_none_or_truthy(kwargs.get("Overwrite"))

        self.ssm_client.put_parameter(Name=key, Value=value, **kwargs)

    def delete(self, key, **kwargs):
        logger.debug('delete "%s"', key)
        key = self._parse_path(key)
        self.ssm_client.delete_parameter(Name=key, **kwargs)

    def list(self, path, **kwargs):
        logger.debug('list "%s"', path)
        path = self._parse_path(path)
        filters = [{"Key": "Path", "Option": "Recursive", "Values": [path]}]

        paginator = self.ssm_client.get_paginator("describe_parameters")
        page_iterator = paginator.paginate(ParameterFilters=filters)

        results = []
        for page in page_iterator:
            results.extend(
                [parameter.get("Name") for parameter in page["Parameters"]]
            )

        return results

    def _parse_path(self, path):
        """
        Strips and leading or trailing whitespace.
        Ensures the key starts with a leading '/'
        """
        path = path.strip()
        if not (path.startswith("/")):
            path = "/" + path
        return path

    def _is_none_or_truthy(self, value):
        return value in (None, True, 1, "True", "true", "t", "1")
