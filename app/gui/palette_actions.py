"""Command-palette and keyboard-shortcut dialog workflows."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from app.config.command_history import CommandHistoryStore
from app.config.key_bindings import KeyMap
from app.gui import strings
from app.gui.commands import Command
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.palette_controller import PaletteController
from app.gui.palette_entries import build_palette_entries
from app.gui.window_input import mouse_control_pairs
from app.pdf.file_format import FileFormat


class PaletteActions:
    """Open palette dialogs and persist command usage history."""

    def __init__(
        self,
        parent: QWidget,
        registry: list[Command],
        palette: PaletteController,
        history: CommandHistoryStore,
        keymap_provider: Callable[[], KeyMap],
        open_keyboard_config: Callable[[], None],
        format_provider: Callable[[], FileFormat | None],
    ) -> None:
        self._parent = parent
        self._registry = registry
        self._palette = palette
        self._history = history
        self._keymap_provider = keymap_provider
        self._open_keyboard_config = open_keyboard_config
        self._format_provider = format_provider

    def open_commands(self) -> None:
        """Show commands with recently-run entries floated to the top."""
        current_format = self._format_provider()
        entries = build_palette_entries(
            self._registry,
            self._history.load(),
            self._keymap_provider(),
            lambda cmd: cmd.available(current_format),
        )
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=strings.PALETTE_PLACEHOLDER,
                title=strings.PALETTE_TITLE,
                show_shortcuts=True,
            ),
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            command: Command = chosen.payload
            self._history.add(command.command_id)
            command.run()

    def show_shortcuts(self) -> None:
        """F1: choose between editing keyboard shortcuts or viewing mouse controls."""
        dialog = FilterListDialog(
            self._chooser_entries(),
            FilterListOptions(
                placeholder=strings.SHORTCUTS_PLACEHOLDER,
                title=strings.SHORTCUTS_TITLE,
            ),
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            chosen.payload()

    def _chooser_entries(self) -> list[ListEntry]:
        """The two F1 rows; each payload is the zero-arg action to run when chosen."""
        return [
            ListEntry(title=strings.CHOOSE_KEYBOARD_LABEL, payload=self._open_keyboard_config),
            ListEntry(title=strings.CHOOSE_MOUSE_LABEL, payload=self._show_mouse_controls),
        ]

    def _show_mouse_controls(self) -> None:
        """Show the read-only list of mouse-wheel gestures."""
        entries = [
            ListEntry(title=strings.SHORTCUT_ROW_FMT.format(chord=gesture, title=desc))
            for gesture, desc in mouse_control_pairs()
        ]
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=strings.MOUSE_CONTROLS_PLACEHOLDER,
                title=strings.MOUSE_CONTROLS_TITLE,
            ),
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        dialog.exec()
