"""Unit tests for the status-bar appearance controller (offscreen Qt)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QLabel

from app.config.status_bar_settings import StatusBarSettings, StatusBarSettingsStore
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.status_bar_settings_controller import StatusBarSettingsController


def _store(font_pt: int) -> MagicMock:
    store = MagicMock(spec=StatusBarSettingsStore)
    store.load.return_value = StatusBarSettings(font_pt=font_pt)
    return store


def test_saved_size_applies_to_all_widgets(qapp: object) -> None:
    bar, filter_label = ModeStatusBar(), QLabel()
    StatusBarSettingsController(bar, [bar, filter_label], _store(18))
    assert bar.font().pointSize() == 18
    assert filter_label.font().pointSize() == 18


def test_zero_keeps_default_sizes(qapp: object) -> None:
    bar, filter_label = ModeStatusBar(), QLabel()
    defaults = (bar.font().pointSize(), filter_label.font().pointSize())
    StatusBarSettingsController(bar, [bar, filter_label], _store(0))
    assert (bar.font().pointSize(), filter_label.font().pointSize()) == defaults


def test_set_font_size_saves_and_applies(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.gui.number_input_dialog.prompt_int", lambda *a, **k: 20)
    bar, filter_label = ModeStatusBar(), QLabel()
    store = _store(0)
    controller = StatusBarSettingsController(bar, [bar, filter_label], store)

    controller.set_font_size()

    store.save.assert_called_once_with(StatusBarSettings(font_pt=20))
    assert bar.font().pointSize() == 20
    assert filter_label.font().pointSize() == 20


def test_zero_after_change_restores_defaults(qapp: object, monkeypatch: pytest.MonkeyPatch) -> None:
    bar, filter_label = ModeStatusBar(), QLabel()
    defaults = (bar.font().pointSize(), filter_label.font().pointSize())
    controller = StatusBarSettingsController(bar, [bar, filter_label], _store(18))

    monkeypatch.setattr("app.gui.number_input_dialog.prompt_int", lambda *a, **k: 0)
    controller.set_font_size()

    assert (bar.font().pointSize(), filter_label.font().pointSize()) == defaults
