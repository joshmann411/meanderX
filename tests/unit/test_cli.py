import pytest

from app import cli


def test_cli_help(capsys):
    cli.main(["--help"])

    assert "python -m app.cli ingest all" in capsys.readouterr().out


def test_cli_invalid_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["unknown"])

    assert exc.value.code == 2
    assert "Usage:" in capsys.readouterr().out
