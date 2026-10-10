"""Integration test for the install_global CLI."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.cli import install_global as install_cli
from app.cli.install_global import BAT_FILES


def test_main_installs_bats_into_prompted_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()

    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{target}\n"))

    exit_code = install_cli.main()

    assert exit_code == 0
    for name, *_ in BAT_FILES:
        assert (target / name).is_file()


def test_main_returns_nonzero_when_target_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{tmp_path / 'nope'}\n"))

    exit_code = install_cli.main()

    assert exit_code != 0


def test_main_accepts_target_via_argv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()

    monkeypatch.setattr("sys.argv", ["pdf-install-global", str(target)])

    exit_code = install_cli.main()

    assert exit_code == 0
    for name, *_ in BAT_FILES:
        assert (target / name).is_file()


def test_main_aborts_on_existing_files_without_force(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()
    (target / BAT_FILES[0][0]).write_text("existing", encoding="utf-8")

    # Stdin sequence: target dir + "n" answer to overwrite prompt
    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{target}\nn\n"))

    exit_code = install_cli.main()

    assert exit_code != 0
    assert (target / BAT_FILES[0][0]).read_text(encoding="utf-8") == "existing"


def test_main_overwrites_when_user_confirms(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()
    (target / BAT_FILES[0][0]).write_text("existing", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{target}\ny\n"))

    exit_code = install_cli.main()

    assert exit_code == 0
    new_text = (target / BAT_FILES[0][0]).read_text(encoding="utf-8")
    assert new_text != "existing"


def test_main_prompts_are_answerable_in_watcher_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()
    (target / BAT_FILES[0][0]).write_text("existing", encoding="utf-8")

    monkeypatch.setenv("TICKETS_WATCHER_COMMAND_RUN", "1")
    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{target}\ny\n"))

    assert install_cli.main() == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines.count("::tw-input-line::") == 2
    assert lines[0] == f"Install target directory [{install_cli.DEFAULT_TARGET}]: "
    assert lines[1] == "::tw-input-line::"
    overwrite_prompt = lines.index("Overwrite? [y/N]: ")
    assert lines[overwrite_prompt + 1] == "::tw-input-line::"


def test_main_does_not_print_markers_outside_watcher_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "cmdtools"
    target.mkdir()

    monkeypatch.delenv("TICKETS_WATCHER_COMMAND_RUN", raising=False)
    monkeypatch.setattr("sys.argv", ["pdf-install-global"])
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{target}\n"))

    assert install_cli.main() == 0
    assert "::tw-input-line::" not in capsys.readouterr().out
