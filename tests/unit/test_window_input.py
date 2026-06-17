"""Keyboard + mouse control listing for the controls dialog (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.key_bindings import merge_keymap
from app.config.settings import Settings
from app.gui import commands, strings
from app.gui.main_window import MainWindow
from app.gui.window_input import default_shortcut_pairs, shortcut_pairs


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
        key_bindings_file=tmp_path / "keybindings.json",
    )
    return MainWindow(settings)


def _pairs(window: MainWindow) -> list[tuple[str, str]]:
    keymap = merge_keymap(default_shortcut_pairs(), ())
    return shortcut_pairs(commands.build_commands(window), keymap)


def test_pairs_include_mouse_wheel_controls(window: MainWindow) -> None:
    chords = {chord for chord, _ in _pairs(window)}
    assert strings.MOUSE_WHEEL in chords
    assert strings.MOUSE_SHIFT_WHEEL in chords
    assert strings.MOUSE_CTRL_WHEEL in chords


def test_pairs_keep_keyboard_shortcuts(window: MainWindow) -> None:
    chords = {chord for chord, _ in _pairs(window)}
    assert "PgDown" in chords
    assert "F1" in chords


def test_default_pairs_include_palette_chord() -> None:
    pairs = default_shortcut_pairs()
    assert ("Ctrl+Shift+P", commands.COMMAND_PALETTE) in pairs
