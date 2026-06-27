"""Mouse-control listing and default shortcut pairs (offscreen Qt)."""

from __future__ import annotations

from app.gui import commands, strings
from app.gui.window_input import default_shortcut_pairs, mouse_control_pairs


def test_mouse_control_pairs_list_the_wheel_gestures() -> None:
    chords = {chord for chord, _ in mouse_control_pairs()}
    assert strings.MOUSE_WHEEL in chords
    assert strings.MOUSE_SHIFT_WHEEL in chords
    assert strings.MOUSE_CTRL_WHEEL in chords


def test_mouse_control_pairs_exclude_keyboard_shortcuts() -> None:
    chords = {chord for chord, _ in mouse_control_pairs()}
    assert "PgDown" not in chords
    assert "F1" not in chords


def test_default_pairs_include_palette_chord() -> None:
    pairs = default_shortcut_pairs()
    assert ("Ctrl+Shift+P", commands.COMMAND_PALETTE) in pairs
