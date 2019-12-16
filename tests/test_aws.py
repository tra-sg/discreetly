from __future__ import unicode_literals

import pytest
import discreetly
import boto3
from moto import mock_ssm


@pytest.fixture
def config_fixture():
    return {"default": {"type": "aws"}}


@pytest.fixture(autouse=True)
def mock_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    # See https://github.com/pytest-dev/pytest/pull/4056
    monkeypatch.setenv(str("AWS_ACCESS_KEY_ID"), str("testing"))
    monkeypatch.setenv(str("AWS_SECRET_ACCESS_KEY"), str("testing"))
    monkeypatch.setenv(str("AWS_SECURITY_TOKEN"), str("testing"))
    monkeypatch.setenv(str("AWS_SESSION_TOKEN"), str("testing"))

    # boto needs a region to be set
    monkeypatch.setenv(str("AWS_DEFAULT_REGION"), str("us-east-1"))


def test_credential_autouse():
    """
    Verify that the mock_credentials fixture is autoused
    """
    import os

    assert os.getenv("AWS_ACCESS_KEY_ID") == "testing"


@mock_ssm
def test_aws_get(config_fixture):
    client = boto3.client("ssm")
    client.put_parameter(Name="/test/bar", Value="baz", Type="SecureString")

    s = discreetly.Session.create(config_fixture)
    assert s.get("test/bar") == "baz"
    assert s.get("/test/bar") == "baz"


@mock_ssm
def test_aws_set(config_fixture):
    s = discreetly.Session.create(config_fixture)
    s.set("test/foo", "bar")

    client = boto3.client("ssm")

    response = client.get_parameter(Name="/test/foo", WithDecryption=False)
    assert response["Parameter"]["Name"] == "/test/foo"
    assert response["Parameter"]["Value"] == "kms:alias/aws/ssm:bar"
    assert response["Parameter"]["Type"] == "SecureString"

    response = client.get_parameter(Name="/test/foo", WithDecryption=True)
    assert response["Parameter"]["Name"] == "/test/foo"
    assert response["Parameter"]["Value"] == "bar"
    assert response["Parameter"]["Type"] == "SecureString"


@mock_ssm
def test_aws_list(config_fixture):
    expected = ["/test/foo", "/test/foo/bar", "/test/foo/bar/baz", "/test/a/b"]
    client = boto3.client("ssm")

    for name in expected:
        client.put_parameter(Name=name, Value="val", Type="SecureString")

    s = discreetly.Session.create(config_fixture)
    results = s.list("/test")
    assert set(results) == set(expected)

    assert s.list("/test/a") == ["/test/a/b"]


@mock_ssm
def test_aws_delete(config_fixture):
    client = boto3.client("ssm")
    client.put_parameter(Name="/test/foo", Value="bar", Type="SecureString")
    response = client.get_parameter(Name="/test/foo", WithDecryption=True)
    assert response["Parameter"]["Name"] == "/test/foo"
    assert response["Parameter"]["Value"] == "bar"
    assert response["Parameter"]["Type"] == "SecureString"

    s = discreetly.Session.create(config_fixture)
    s.delete("/test/foo")

    with pytest.raises(
        client.exceptions.ParameterNotFound, match="An error occurred"
    ):
        client.get_parameter(Name="/test/foo", WithDecryption=True)
