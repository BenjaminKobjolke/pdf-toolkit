"""Unit tests for the mode footer bar (offscreen Qt)."""

from __future__ import annotations

import pytest

from app.gui import strings
from app.gui.mode_status_bar import ModeStatusBar


@pytest.fixture
def bar(qapp: object) -> ModeStatusBar:
    return ModeStatusBar()


def test_defaults_to_regular_mode(bar: ModeStatusBar) -> None:
    assert bar.mode_text() == strings.MODE_REGULAR


def test_edit_mode_shows_edit_text(bar: ModeStatusBar) -> None:
    bar.set_edit_mode(True)
    assert bar.mode_text() == strings.MODE_EDIT_TEXT


def test_toggling_back_returns_to_regular(bar: ModeStatusBar) -> None:
    bar.set_edit_mode(True)
    bar.set_edit_mode(False)
    assert bar.mode_text() == strings.MODE_REGULAR
