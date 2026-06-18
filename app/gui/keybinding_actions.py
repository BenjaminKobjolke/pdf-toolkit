"""The "Configure keyboard shortcuts" workflow: bind, reassign, and clear chords.

Reuses the palette widget for the command list (rows show their current chord),
opens :class:`KeyCaptureDialog` to read a new chord, warns before stealing a chord
from another command, and applies every change live via ``apply_keymap``. All
binding rules live in :mod:`app.config.key_bindings`; this class only orchestrates
(reload from store → mutate → save → apply → report).
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from app.config.key_bindings import (
    DefaultPair,
    KeyBindingStore,
    KeyMap,
    KeyOverride,
    assign,
    effective_keymap,
    merge_keymap,
    remove_command,
)
from app.gui import commands, confirm_dialog, strings
from app.gui.commands import Command
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.key_capture_dialog import KeyCaptureDialog
from app.gui.operations import OpResult
from app.gui.palette_controller import PaletteController
from app.gui.palette_entries import build_palette_entries


class KeybindingActions:
    """Open the shortcut-config list and apply bind/clear actions live."""

    def __init__(
        self,
        parent: QWidget,
        registry: list[Command],
        palette: PaletteController,
        store: KeyBindingStore,
        defaults: list[DefaultPair],
        apply_keymap: Callable[[KeyMap], None],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._registry = registry
        self._palette = palette
        self._store = store
        self._defaults = defaults
        self._apply_keymap = apply_keymap
        self._report = report

    def open_config(self) -> None:
        """Show the searchable command list; Enter binds, Del clears."""
        entries = build_palette_entries(self._registry, [], self._keymap())
        dialog = FilterListDialog(
            entries,
            placeholder=strings.CONFIGURE_SHORTCUTS_PLACEHOLDER,
            title=strings.CONFIGURE_SHORTCUTS_TITLE,
            show_shortcuts=True,
            on_delete=self._clear,
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._bind(chosen.payload)

    def _bind(self, command: Command) -> None:
        """Capture a chord for ``command`` and assign it (confirming any steal)."""
        capture = KeyCaptureDialog(command.title, self._parent)
        if not capture.exec():
            return
        chord = capture.chosen_chord()
        if chord is None:
            return
        overrides = self._store.load()
        stolen_from = self._keymap().command_for(chord)
        if stolen_from == command.command_id:
            return
        if stolen_from is not None and not self._confirm_reassign(chord, stolen_from, command):
            return
        self._apply(assign(overrides, chord, command.command_id))
        self._report(OpResult(True, self._set_message(chord, command, stolen_from)))

    def _clear(self, entry: ListEntry) -> None:
        """Remove every chord bound to the entry's command (with confirmation)."""
        command: Command = entry.payload
        chords = self._keymap().chords_for(command.command_id)
        if not chords:
            self._report(
                OpResult(True, strings.MSG_SHORTCUT_NONE_TO_CLEAR_FMT.format(title=command.title))
            )
            return
        if not self._confirm_clear(command, chords):
            return
        self._apply(remove_command(self._store.load(), self._defaults, command.command_id))
        self._report(OpResult(True, strings.MSG_SHORTCUT_CLEARED_FMT.format(title=command.title)))

    def _apply(self, overrides: tuple[KeyOverride, ...]) -> None:
        self._store.save(overrides)
        self._apply_keymap(merge_keymap(self._defaults, overrides))

    def _keymap(self) -> KeyMap:
        return effective_keymap(self._store, self._defaults)

    def _set_message(self, chord: str, command: Command, stolen_from: str | None) -> str:
        if stolen_from is None:
            return strings.MSG_SHORTCUT_SET_FMT.format(chord=chord, title=command.title)
        return strings.MSG_SHORTCUT_STOLEN_FMT.format(
            chord=chord, title=command.title, stolen=self._title_for(stolen_from)
        )

    def _confirm_reassign(self, chord: str, current_id: str, command: Command) -> bool:
        return self._confirm(
            strings.CONFIRM_REASSIGN_TITLE,
            strings.CONFIRM_REASSIGN_FMT.format(
                chord=chord, current=self._title_for(current_id), target=command.title
            ),
        )

    def _confirm_clear(self, command: Command, chords: tuple[str, ...]) -> bool:
        return self._confirm(
            strings.CONFIRM_CLEAR_SHORTCUT_TITLE,
            strings.CONFIRM_CLEAR_SHORTCUT_FMT.format(
                chords=", ".join(chords), title=command.title
            ),
        )

    def _confirm(self, title: str, text: str) -> bool:
        choice = confirm_dialog.confirm(
            self._parent, title, text, primary=strings.BTN_YES, secondary=strings.BTN_NO
        )
        return choice is confirm_dialog.DialogResult.PRIMARY

    def _title_for(self, command_id: str) -> str:
        try:
            return commands.find(self._registry, command_id).title
        except KeyError:
            return command_id
