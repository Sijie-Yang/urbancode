from typer.testing import CliRunner

from urbancode.cli import app
from urbancode._version import __version__


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert __version__ in result.stdout
