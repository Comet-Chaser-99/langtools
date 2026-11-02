import pytest

from elan_ng import __version__
from elan_ng.app import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_self_test_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--self-test"]) == 0
    assert "self-test OK" in capsys.readouterr().out
