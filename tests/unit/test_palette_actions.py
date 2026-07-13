"""The F1 chooser routes to the editable keyboard dialog or the mouse list."""

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtWidgets import QWidget

from app.config.command_history import CommandHistoryStore
from app.config.key_bindings import KeyMap
from app.gui import strings
from app.gui.palette_actions import PaletteActions
from app.gui.palette_controller import PaletteController


def _actions(open_keyboard: MagicMock) -> PaletteActions:
    return PaletteActions(
        QWidget(),
        [],
        MagicMock(spec=PaletteController),
        MagicMock(spec=CommandHistoryStore),
        lambda: KeyMap(()),
        open_keyboard,
        lambda: None,
    )


def test_chooser_offers_keyboard_then_mouse(qapp: object) -> None:
    actions = _actions(MagicMock())
    titles = [entry.title for entry in actions._chooser_entries()]
    assert titles == [strings.CHOOSE_KEYBOARD_LABEL, strings.CHOOSE_MOUSE_LABEL]


def test_keyboard_entry_invokes_the_editable_dialog(qapp: object) -> None:
    open_keyboard = MagicMock()
    actions = _actions(open_keyboard)
    keyboard_entry, _mouse_entry = actions._chooser_entries()
    keyboard_entry.payload()
    open_keyboard.assert_called_once_with()


def test_mouse_entry_routes_to_the_mouse_list(qapp: object) -> None:
    actions = _actions(MagicMock())
    _keyboard_entry, mouse_entry = actions._chooser_entries()
    assert mouse_entry.payload == actions._show_mouse_controls
