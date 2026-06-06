"""Keyboard + mouse control listing for the controls dialog (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.gui import commands, strings
from app.gui.main_window import MainWindow
from app.gui.window_input import shortcut_pairs


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    settings = Settings(
        backup_dir=tmp_path / "backup",
        log_level="INFO",
        recent_file=tmp_path / "recent.json",
    )
    return MainWindow(settings)


def test_pairs_include_mouse_wheel_controls(window: MainWindow) -> None:
    pairs = shortcut_pairs(commands.build_commands(window))
    chords = {chord for chord, _ in pairs}
    assert strings.MOUSE_WHEEL in chords
    assert strings.MOUSE_SHIFT_WHEEL in chords
    assert strings.MOUSE_CTRL_WHEEL in chords


def test_pairs_keep_keyboard_shortcuts(window: MainWindow) -> None:
    pairs = shortcut_pairs(commands.build_commands(window))
    chords = {chord for chord, _ in pairs}
    assert "PgDown" in chords
    assert "F1" in chords
