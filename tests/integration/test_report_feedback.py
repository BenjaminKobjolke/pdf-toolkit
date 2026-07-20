"""Integration: _report success flashes the status bar; errors stay modal."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.gui import confirm_dialog, file_strings
from app.gui.main_window import MainWindow
from app.gui.operations import OpResult
from tests.conftest import MakePdf


def test_success_report_flashes_status_bar_without_dialog(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown = []
    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: shown.append(a))

    window._report(OpResult(True, "copied file path"))

    assert shown == []
    assert window._mode_bar.flash_text() == "copied file path"


def test_open_with_launch_flashes_status_bar_without_dialog(
    window: MainWindow, make_pdf: MakePdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown = []
    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: shown.append(a))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    window.open_pdf(make_pdf([(100, 100)]))

    window._open_with_actions._launch(Path("C:/apps/Photoshop.exe"))

    assert shown == []
    expected = file_strings.MSG_OPEN_WITH_LAUNCHED_FMT.format(app="Photoshop")
    assert window._mode_bar.flash_text() == expected


def test_failure_report_still_shows_error_dialog(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown = []
    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: shown.append((a, k)))

    window._report(OpResult(False, "boom"))

    assert len(shown) == 1
