"""Unit tests: forwarded-open focus gating in :func:`app.gui.main._open_in`."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.gui.main import _open_in
from app.gui.main_window import MainWindow


def _window(*, focus_on_forward: bool) -> MagicMock:
    window = MagicMock(spec=MainWindow)
    window.instance_controller.focus_on_forward = focus_on_forward
    return window


def test_focus_on_raises_and_activates(qapp: object) -> None:
    window = _window(focus_on_forward=True)
    _open_in(window, Path("x.pdf"))
    window.open_pdf.assert_called_once_with(Path("x.pdf"))
    window.raise_.assert_called_once()
    window.activateWindow.assert_called_once()


def test_focus_off_raises_above_others_without_activating(qapp: object) -> None:
    window = _window(focus_on_forward=False)
    with patch("app.gui.main._raise_above_others") as raise_above:
        _open_in(window, Path("x.pdf"))
    window.open_pdf.assert_called_once_with(Path("x.pdf"))
    # Off surfaces the window (un-minimize + raise above others) but never
    # steals keyboard focus.
    window.setWindowState.assert_called_once()
    window.raise_.assert_called_once()
    raise_above.assert_called_once_with(window)
    window.activateWindow.assert_not_called()


def test_activate_only_ping_without_path(qapp: object) -> None:
    window = _window(focus_on_forward=True)
    _open_in(window, None)
    window.open_pdf.assert_not_called()
    window.activateWindow.assert_called_once()
