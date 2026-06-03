"""Integration test for the GUI CLI entry point (no real event loop)."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.main as gui_main
from app.cli import gui as gui_cli
from app.gui.main_window import MainWindow


def test_gui_cli_main_launches_without_blocking(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown: list[bool] = []
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: shown.append(True))
    monkeypatch.setattr("sys.argv", ["pdft-gui"])

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
