"""Integration test for the GUI CLI entry point (no real event loop)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.main as gui_main
from app.cli import gui as gui_cli
from app.gui.main_window import MainWindow


@pytest.fixture(autouse=True)
def isolate_single_instance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep main() away from the user's real settings DB and viewer pipe."""
    monkeypatch.setenv("PDF_TOOLKIT_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(gui_main.single_instance, "try_send_to_running", lambda *a, **k: False)
    monkeypatch.setattr(gui_main.InstanceServer, "start", lambda self: True)


def test_gui_cli_main_launches_without_blocking(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown: list[bool] = []
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: shown.append(True))
    monkeypatch.setattr("sys.argv", ["FastFileViewer"])

    exit_code = gui_cli.main()

    assert exit_code == 0
    assert shown  # window was constructed and shown


def test_path_arg_opens_that_pdf(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """A file path argument (how a file association launches us) opens that PDF."""
    opened: list[str] = []
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: None)
    monkeypatch.setattr(MainWindow, "open_pdf", lambda self, path: opened.append(str(path)))

    exit_code = gui_main.main([r"C:\docs\report.pdf"])

    assert exit_code == 0
    assert opened == [r"C:\docs\report.pdf"]


def test_reuse_on_forwards_and_exits_without_window(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When a running viewer accepts the path, no second window is created."""
    forwarded: list[Path | None] = []
    monkeypatch.setattr(
        gui_main.single_instance,
        "try_send_to_running",
        lambda path, **_k: forwarded.append(path) or True,
    )
    constructed: list[bool] = []
    monkeypatch.setattr(MainWindow, "__init__", lambda self, *_a: constructed.append(True))

    exit_code = gui_main.main([r"C:\docs\report.pdf"])

    assert exit_code == 0
    assert forwarded == [Path(r"C:\docs\report.pdf")]
    assert constructed == []
