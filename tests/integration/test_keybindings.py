"""End-to-end: configuring a shortcut rebuilds live QShortcuts and persists.

The add/replace/reassign/multi-remove *orchestration* itself now lives in the
shared ``command_palette`` library and is covered there
(``python-command-palette/tests/unit/test_shortcut_editor.py``, against a
``MemoryStore``) -- re-testing every branch of that logic here would just
duplicate it. These tests instead cover what's unique to this app: a real
``MainWindow``, a real SQLite-backed keymap, and that ``configure_shortcuts()``
actually reaches the library editor and installs live ``QShortcut``s.
"""

from __future__ import annotations

from typing import Any

from command_palette import KeymapState
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QMenu

from app.gui import commands, strings
from app.gui.main_window import MainWindow
from app.gui.window_input import default_shortcut_pairs


def _seq(chord: str) -> str:
    return QKeySequence(chord).toString()


def _installed_chords(window: MainWindow) -> list[str]:
    return [shortcut.key().toString() for shortcut in window._shortcut_installer.shortcuts()]


def _apply(window: MainWindow) -> None:
    """Re-install shortcuts from the persisted keymap -- mirrors what the
    shortcut editor's ``on_change`` callback does after every edit."""
    window.apply_keymap(window._keymap_state.effective())


def test_assign_chord_installs_exactly_one_shortcut(window: MainWindow) -> None:
    window._keymap_state.assign("Alt+W", commands.EXIT)
    _apply(window)
    assert _installed_chords(window).count(_seq("Alt+W")) == 1
    assert window.current_keymap().command_for("Alt+W") == commands.EXIT


def test_reassign_steals_chord_from_previous_owner(window: MainWindow) -> None:
    # Ctrl+S defaults to Save; reassigning it to Exit must remove it from Save.
    window._keymap_state.assign("Ctrl+S", commands.EXIT)
    _apply(window)
    keymap = window.current_keymap()
    assert keymap.command_for("Ctrl+S") == commands.EXIT
    assert keymap.chords_for(commands.SAVE) == ()
    assert _installed_chords(window).count(_seq("Ctrl+S")) == 1


def test_remove_then_reset_restores_default(window: MainWindow) -> None:
    window._keymap_state.remove_command(commands.SAVE)
    _apply(window)
    assert window.current_keymap().chords_for(commands.SAVE) == ()
    window._key_bindings.reset()
    restored = window._keymap_state.effective()
    assert "Ctrl+S" in restored.chords_for(commands.SAVE)


def test_palette_chord_is_a_binding_but_menu_stays_reachable(window: MainWindow) -> None:
    # The palette chord is a normal binding now…
    assert window.current_keymap().command_for("Ctrl+Shift+P") == commands.COMMAND_PALETTE
    # …and even if it were removed, the File menu still reaches the palette.
    window._keymap_state.remove_command(commands.COMMAND_PALETTE)
    _apply(window)
    titles: list[str] = []
    for menu_action in window.menuBar().actions():
        menu = menu_action.menu()
        if isinstance(menu, QMenu):
            titles.extend(action.text() for action in menu.actions())
    assert strings.ACTION_COMMAND_PALETTE in titles


def test_palette_row_shows_all_chords(window: MainWindow) -> None:
    from app.gui.palette_entries import build_palette_entries

    entries = build_palette_entries(window._registry, [], window.current_keymap())
    zoom = next(e for e in entries if e.payload.command_id == commands.ZOOM_IN)
    assert zoom.shortcut == "Ctrl++, Ctrl+=, Ctrl+Up"


def test_configure_shortcuts_reaches_library_editor_and_installs_live_shortcut(
    window: MainWindow, monkeypatch: Any
) -> None:
    """``configure_shortcuts()`` -> the library's ``open_shortcut_editor`` -> a
    real ``QShortcut``, and the binding survives a fresh ``KeymapState`` over
    the same backend (proves it round-tripped through SQLite, not just an
    in-memory ``KeymapState``)."""
    from command_palette import shortcut_editor as lib_shortcut_editor

    exit_command = commands.find(window._registry, commands.EXIT)

    class _IgnoresDialogChrome:
        """`decorate` (the app's palette-chrome applier) calls real QDialog
        methods like `.resize()`/`.setWindowFlags()` -- no-op them all."""

        def __getattr__(self, _name: str) -> Any:
            return lambda *_args: None

    class _FakePicker(_IgnoresDialogChrome):
        def __init__(self, entries: list[Any], options: Any = None, parent: Any = None) -> None:
            self._entries = entries

        def exec(self) -> int:
            return 1

        def chosen(self) -> Any:
            return next(e for e in self._entries if e.payload == exit_command.command_id)

    class _FakeCapture(_IgnoresDialogChrome):
        def __init__(self, title: str, parent: Any = None, *, labels: Any = None) -> None:
            pass

        def exec(self) -> int:
            return 1

        def chosen_chord(self) -> str:
            return "Alt+W"

    monkeypatch.setattr(lib_shortcut_editor, "FilterListDialog", _FakePicker)
    monkeypatch.setattr(lib_shortcut_editor, "KeyCaptureDialog", _FakeCapture)

    window.configure_shortcuts()

    assert _installed_chords(window).count(_seq("Alt+W")) == 1
    assert window.current_keymap().command_for("Alt+W") == commands.EXIT

    # Persisted through this app's SQLite backend, not just in memory:
    reloaded = KeymapState(window._key_bindings, default_shortcut_pairs())
    assert reloaded.effective().command_for("Alt+W") == commands.EXIT
