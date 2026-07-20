"""Integration tests for the 'Open with…' palette command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.config.open_with import OpenWithStore
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_backend, silence_dialogs


def test_command_present(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.OPEN_WITH) is not None


def test_command_needs_open_document(window: MainWindow, make_pdf: MakePdf) -> None:
    disabled = commands.find(commands.build_commands(window), commands.OPEN_WITH)
    assert disabled.is_enabled() is False
    window.open_pdf(make_pdf([(200, 300)]))
    enabled = commands.find(commands.build_commands(window), commands.OPEN_WITH)
    assert enabled.is_enabled() is True


def test_launch_opens_configured_app_with_current_file(
    window: MainWindow, make_pdf: MakePdf, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    silence_dialogs(monkeypatch)  # _launch reports success via a modal dialog
    pdf = make_pdf([(200, 300)])
    window.open_pdf(pdf)
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "Popen", lambda args: calls.append(args))

    app = tmp_path / "editor.exe"
    window.open_with_actions._launch(app)

    assert calls == [[str(app), str(pdf)]]


def test_store_shares_window_backend(window: MainWindow, tmp_path: Path) -> None:
    # An app added through the window's store is visible on the same per-test DB,
    # so it survives a restart and shows under Remembered settings.
    window.open_with_actions._store.add(tmp_path / "Gimp.exe")
    assert OpenWithStore(gui_backend(tmp_path)).load() == [tmp_path / "Gimp.exe"]
