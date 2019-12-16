import pytest
import discreetly

# unittest.mock is Python 3.3 and up
# If/when we drop support for Python < 3.3, we won't need the try
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@pytest.fixture
def config_fixture():
    return {"default": {"type": "aws"}}


@pytest.fixture
def mock_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    # See https://github.com/pytest-dev/pytest/pull/4056
    monkeypatch.setenv(str("AWS_ACCESS_KEY_ID"), str("testing"))
    monkeypatch.setenv(str("AWS_SECRET_ACCESS_KEY"), str("testing"))
    monkeypatch.setenv(str("AWS_SECURITY_TOKEN"), str("testing"))
    monkeypatch.setenv(str("AWS_SESSION_TOKEN"), str("testing"))

    # boto needs the region to be set
    monkeypatch.setenv(str("AWS_DEFAULT_REGION"), str("us-east-1"))


def test_session_create(config_fixture, mock_credentials):
    discreetly.Session.create(config_fixture)


def test_session_config_file_missing(mock_credentials):
    with pytest.raises(
        (OSError, IOError), match="Not a directory: '/dev/null/123'"
    ):
        with patch.dict(
            "os.environ", {"DISCREETLY_CONFIG_FILE": "/dev/null/123"}
        ):
            discreetly.Session.create()


def test_session_bad_profile(config_fixture, mock_credentials):
    with pytest.raises(KeyError, match='Invalid profile: "bad_profile"'):
        discreetly.Session.create(config_fixture, "bad_profile")
