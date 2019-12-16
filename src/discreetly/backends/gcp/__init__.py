from __future__ import unicode_literals
import logging
from abc import ABCMeta
from future.utils import with_metaclass
from google.cloud.client import ClientWithProject
from google.cloud import datastore, kms
from discreetly.backends import AbstractBackend

logger = logging.getLogger(__name__)


class GCPBackend(with_metaclass(ABCMeta, AbstractBackend)):
    def __init__(self, config, *args, **kwargs):
        super(GCPBackend, self).__init__(config)

        self.kms_client = kms.KeyManagementServiceClient()
        self.datastore_client = datastore.Client(
            project=config.get("datastore_project")
            or self._get_default_project(),
            namespace=config.get("datastore_namespace"),
        )

        self.datastore_kind = config.get("datastore_kind", "Secret")
        self.datastore_property_ciphertext = config.get(
            "datastore_property_ciphertext", "ciphertext"
        )
        self.datastore_property_keyid = config.get(
            "datastore_property_keyid", "keyid"
        )
        self.default_keyid = config.get("keyid") or self._get_default_keyid()

    def get(self, key, **kwargs):
        logger.debug('get "%s"', key)

        parents, key = self._parse_path(key)
        key_path = parents + key
        key = self.datastore_client.key(*key_path)
        result = self.datastore_client.get(key)

        if result is None:
            raise ValueError("Value %s not found." % key)

        ciphertext = result.get(self.datastore_property_ciphertext)
        cryptokey = result.get(self.datastore_property_keyid)
        return self._decrypt_value(ciphertext, cryptokey)

    def set(self, key, value, **kwargs):
        logger.debug('set "%s"', key)
        self._set_value(key, value, **kwargs)

    def delete(self, key, **kwargs):
        logger.debug('delete "%s"', key)
        parents, key = self._parse_path(key)
        key_path = parents + key
        key = self.datastore_client.key(*key_path)
        self.datastore_client.delete(key)

    def list(self, path, **kwargs):
        logger.debug('list "%s"', path)
        parts = path.strip("/").split("/")
        parents = self._parse_parents(parts)
        ancestor = self.datastore_client.key(*parents)
        query = self.datastore_client.query(
            kind=self.datastore_kind, ancestor=ancestor
        )
        query.keys_only()
        results = list(query.fetch())

        return [
            "/".join(entity.key.flat_path[1:-1:2] + entity.key.flat_path[-1::])
            for entity in results
        ]

    def _set_value(self, key, value, **kwargs):
        parents, key = self._parse_path(key)
        key_path = parents + key
        key = self.datastore_client.key(*key_path)
        cryptokey = kwargs.get("keyid", self.default_keyid)
        entity = datastore.Entity(
            key=key, exclude_from_indexes=[self.datastore_property_ciphertext]
        )
        entity.update(
            {
                self.datastore_property_ciphertext: self._encrypt_value(
                    value, cryptokey
                ),
                self.datastore_property_keyid: cryptokey,
            }
        )
        self.datastore_client.put(entity)

    def _decrypt_value(self, ciphertext, cryptokey=None):
        if cryptokey is None:
            cryptokey = self.default_keyid
            logger.warn("No cryptokey specified. Trying default")
        response = self.kms_client.decrypt(cryptokey, ciphertext)
        return response.plaintext.decode()

    def _encrypt_value(self, plaintext, cryptokey=None):
        if cryptokey is None:
            cryptokey = self.default_keyid
        response = self.kms_client.encrypt(
            cryptokey, plaintext.encode("utf-8")
        )
        return response.ciphertext

    def _parse_path(self, path):
        """
        Given a path of the form "path/to/keyname", returns the parents and
        key as a tuple of lists, e.g.:
        (['Parent', 'path', 'Parent', 'to'], ['Secret', 'keyname'])
        """
        parts = path.strip("/").split("/")
        key_name = parts.pop()
        if not key_name:
            raise Exception

        parents = self._parse_parents(parts)
        return parents, [self.datastore_kind, key_name]

    def _parse_parents(self, seq):
        return [v for parent in seq for v in ("Parent", parent)]

    def _get_default_project(self):
        """
        Gets the default Google project ID.

        This relies on the fact that if a GCP Client is created without
        specifying the project, the project ID will be determined by
        searching the following locations:

        - GOOGLE_CLOUD_PROJECT environment variable
        - GOOGLE_APPLICATION_CREDENTIALS JSON file
        - Default service configuration path from `$ gcloud beta auth application-default login`  # noqa: E501
        - Google App Engine application ID
        - Google Compute Engine project ID (from metadata server)

        See: https://googleapis.dev/python/google-cloud-core/latest/config.html
        """
        if not self.default_project:
            base_client = ClientWithProject()
            self.default_project = base_client.project
        return self.default_project

    def _get_default_keyid(self):
        return self.kms_client.crypto_key_path(
            self._get_default_project(), "global", "discreetly", "default"
        )
