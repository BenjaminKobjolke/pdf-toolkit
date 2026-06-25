"""End-to-end: configuring a shortcut rebuilds live QShortcuts and persists."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QMenu

from app.config.key_bindings import KeyOverride, assign, merge_keymap, remove_command
from app.gui import commands, confirm_dialog, keybinding_actions, strings
from app.gui.commands import Command
from app.gui.main_window import MainWindow
from app.gui.window_input import default_shortcut_pairs


def _seq(chord: str) -> str:
    return QKeySequence(chord).toString()


def _installed_chords(window: MainWindow) -> list[str]:
    return [shortcut.key().toString() for shortcut in window._shortcut_installer.shortcuts()]


def _apply(window: MainWindow, overrides: tuple[KeyOverride, ...]) -> None:
    window._key_bindings.save(overrides)
    window.apply_keymap(merge_keymap(default_shortcut_pairs(), overrides))


def test_assign_chord_installs_exactly_one_shortcut(window: MainWindow) -> None:
    _apply(window, assign(window._key_bindings.load(), "Alt+W", commands.EXIT))
    assert _installed_chords(window).count(_seq("Alt+W")) == 1
    assert window.current_keymap().command_for("Alt+W") == commands.EXIT


def test_reassign_steals_chord_from_previous_owner(window: MainWindow) -> None:
    # Ctrl+S defaults to Save; reassigning it to Exit must remove it from Save.
    _apply(window, assign(window._key_bindings.load(), "Ctrl+S", commands.EXIT))
    keymap = window.current_keymap()
    assert keymap.command_for("Ctrl+S") == commands.EXIT
    assert keymap.chords_for(commands.SAVE) == ()
    assert _installed_chords(window).count(_seq("Ctrl+S")) == 1


def test_remove_then_reset_restores_default(window: MainWindow) -> None:
    _apply(
        window, remove_command(window._key_bindings.load(), default_shortcut_pairs(), commands.SAVE)
    )
    assert window.current_keymap().chords_for(commands.SAVE) == ()
    window._key_bindings.reset()
    restored = merge_keymap(default_shortcut_pairs(), window._key_bindings.load())
    assert "Ctrl+S" in restored.chords_for(commands.SAVE)


def test_palette_chord_is_a_binding_but_menu_stays_reachable(window: MainWindow) -> None:
    # The palette chord is a normal binding now…
    assert window.current_keymap().command_for("Ctrl+Shift+P") == commands.COMMAND_PALETTE
    # …and even if it were removed, the File menu still reaches the palette.
    _apply(
        window,
        remove_command(
            window._key_bindings.load(), default_shortcut_pairs(), commands.COMMAND_PALETTE
        ),
    )
    titles: list[str] = []
    for menu_action in window.menuBar().actions():
        menu = menu_action.menu()
        if isinstance(menu, QMenu):
            titles.extend(action.text() for action in menu.actions())
    assert strings.ACTION_COMMAND_PALETTE in titles


def test_configure_actions_bind_flow(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCapture:
        def __init__(self, _title: str, _parent: object) -> None: ...

        def exec(self) -> int:
            return 1

        def chosen_chord(self) -> str:
            return "Alt+W"

    monkeypatch.setattr(keybinding_actions, "KeyCaptureDialog", FakeCapture)
    monkeypatch.setattr(confirm_dialog, "show_message", staticmethod(lambda *a, **k: None))

    exit_command = commands.find(window._registry, commands.EXIT)
    window._keybinding_actions._bind(exit_command)

    assert window.current_keymap().command_for("Alt+W") == commands.EXIT
    assert (
        merge_keymap(default_shortcut_pairs(), window._key_bindings.load()).command_for("Alt+W")
        == commands.EXIT
    )


def test_configure_actions_clear_flow(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(confirm_dialog, "show_message", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(
        confirm_dialog,
        "confirm",
        staticmethod(lambda *a, **k: confirm_dialog.DialogResult.PRIMARY),
    )
    save_command: Command = commands.find(window._registry, commands.SAVE)
    from app.gui.filter_list_dialog import ListEntry

    window._keybinding_actions._clear(ListEntry(title=save_command.title, payload=save_command))
    assert window.current_keymap().chords_for(commands.SAVE) == ()
