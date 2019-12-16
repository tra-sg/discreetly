import discreetly
from click.testing import CliRunner
from discreetly.cli import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert discreetly.__version__ in result.output
