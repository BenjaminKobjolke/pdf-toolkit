"""Command-palette and keyboard-shortcut dialog workflows."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from app.config.command_history import CommandHistoryStore
from app.config.key_bindings import KeyMap
from app.gui import strings
from app.gui.commands import Command
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.palette_controller import PaletteController
from app.gui.palette_entries import build_palette_entries
from app.gui.window_input import shortcut_pairs


class PaletteActions:
    """Open palette dialogs and persist command usage history."""

    def __init__(
        self,
        parent: QWidget,
        registry: list[Command],
        palette: PaletteController,
        history: CommandHistoryStore,
        keymap_provider: Callable[[], KeyMap],
    ) -> None:
        self._parent = parent
        self._registry = registry
        self._palette = palette
        self._history = history
        self._keymap_provider = keymap_provider

    def open_commands(self) -> None:
        """Show commands with recently-run entries floated to the top."""
        entries = build_palette_entries(
            self._registry, self._history.load(), self._keymap_provider()
        )
        dialog = FilterListDialog(
            entries,
            placeholder=strings.PALETTE_PLACEHOLDER,
            title=strings.PALETTE_TITLE,
            show_shortcuts=True,
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            command: Command = chosen.payload
            self._history.add(command.command_id)
            command.run()

    def show_shortcuts(self) -> None:
        """Show a searchable, read-only list of every keyboard shortcut."""
        entries = [
            ListEntry(title=strings.SHORTCUT_ROW_FMT.format(chord=chord, title=title))
            for chord, title in shortcut_pairs(self._registry, self._keymap_provider())
        ]
        dialog = FilterListDialog(
            entries,
            placeholder=strings.SHORTCUTS_PLACEHOLDER,
            title=strings.SHORTCUTS_TITLE,
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        dialog.exec()
