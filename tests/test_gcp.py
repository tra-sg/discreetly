from __future__ import unicode_literals
import pytest
import discreetly
import mock
from google.cloud.kms_v1.proto import service_pb2

# Unit testing GCP services is not straightforward. There isn't presently
# anything like a library equivalent to moto for google.cloud.*
#
# The tests below try to mock out datastore and kms and verify that
# calls and responses are more-or-less as expected.
#
# For future reference, it may be useful to look at:
#
#   * https://github.com/googleapis/google-cloud-python/tree/master/datastore/tests/unit  # noqa: E501
#   * https://github.com/googleapis/google-cloud-python/blob/master/kms/tests/unit/gapic/v1/test_key_management_service_client_v1.py  # noqa: E501
#


@pytest.fixture
def config_fixture():
    return {
        "default": {
            "type": "gcp",
            "datastore_project": "acme-corp",
            "keyid": (
                "projects/acme-corp-kms/"
                "locations/global/"
                "keyRings/dev/"
                "cryptoKeys/default"
            ),
        }
    }


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv(str("GOOGLE_APPLICATION_CREDENTIALS"), str("testing"))


def decrypt_response(plaintext):
    return service_pb2.DecryptResponse(plaintext=plaintext.encode("utf-8"))


def encrypt_response(ciphertext):
    return service_pb2.EncryptResponse(ciphertext=ciphertext.encode("utf-8"))


def decrypt_request(ciphertext, cryptokey):
    return {
        "ciphertext": ciphertext,
        "keyid": cryptokey,
    }


@mock.patch("google.cloud.kms.KeyManagementServiceClient", autospec=True)
@mock.patch("google.cloud.datastore.Client", autospec=True)
def test_gcp_get(datastore_client, kms_client, config_fixture):
    cryptokey = config_fixture["default"]["keyid"]
    ciphertext = "gobbledygook"
    plaintext = "hushhush"
    datastore_client.return_value.get.return_value = decrypt_request(
        ciphertext, cryptokey
    )

    kms_client.return_value.decrypt.return_value = decrypt_response(plaintext)

    s = discreetly.Session.create(config_fixture)
    assert s.get("testy/foo/bar/baz") == plaintext
    kms_client.return_value.decrypt.assert_called_with(cryptokey, ciphertext)


@mock.patch("google.cloud.kms.KeyManagementServiceClient", autospec=True)
@mock.patch("google.cloud.datastore.Client", autospec=True)
def test_gcp_set(datastore_client, kms_client, config_fixture):
    cryptokey = config_fixture["default"]["keyid"]
    ciphertext = "gobbledygobbledygook"
    plaintext = "hushhushhush"

    kms_client.return_value.encrypt.return_value = encrypt_response(ciphertext)

    s = discreetly.Session.create(config_fixture)
    s.set("foo/bar/baz", plaintext)

    datastore_client.return_value.put.assert_called_once()
    kms_client.return_value.encrypt.assert_called_with(
        cryptokey, plaintext.encode("utf-8")
    )


@mock.patch("google.cloud.kms.KeyManagementServiceClient", autospec=True)
@mock.patch("google.cloud.datastore.Client", autospec=True)
def test_gcp_list(datastore_client, kms_client, config_fixture):
    s = discreetly.Session.create(config_fixture)
    s.list("foo/bar")


# @mock.patch("google.cloud.kms.KeyManagementServiceClient", autospec=True)
# @mock.patch("google.cloud.datastore.Client", autospec=True)
# def test_delete(datastore_client, kms_client, config_fixture):
#     s = discreetly.Session.create(config_fixture)
#     s.delete("foo/bar/baz")
