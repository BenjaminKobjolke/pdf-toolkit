"""Integration tests: a forwarded open request drives the main window."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui.main import _open_in
from app.gui.main_window import MainWindow
from tests.conftest import gui_settings, silence_dialogs


@pytest.fixture
def window(qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    silence_dialogs(monkeypatch)
    return MainWindow(gui_settings(tmp_path))


def test_forwarded_path_opens_and_activates(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[Path] = []
    monkeypatch.setattr(window, "open_pdf", opened.append)

    _open_in(window, Path(r"C:\docs\a.pdf"))

    assert opened == [Path(r"C:\docs\a.pdf")]
    assert window.isVisible()


def test_activate_only_does_not_open(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[Path] = []
    monkeypatch.setattr(window, "open_pdf", opened.append)

    _open_in(window, None)

    assert opened == []
    assert window.isVisible()


def test_forwarded_open_unminimizes(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(window, "open_pdf", lambda _p: None)
    window.showMinimized()

    _open_in(window, Path("x.pdf"))

    assert not window.isMinimized()
