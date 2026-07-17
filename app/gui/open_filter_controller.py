"""Owns the open-dialog file filter: live settings, edit prompts, persistence.

Persists every change via :class:`OpenFilterSettingsStore` and hands the open
dialog its current :class:`FileFilter`. Mirrors :class:`TextViewController` so
the window stays a thin coordinator.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from PySide6.QtWidgets import QWidget

from app.config.open_filter_settings import (
    OpenFilterSettingsStore,
    parse_extensions,
)
from app.gui import file_browser_strings, settings_strings, text_prompt_dialog
from app.gui.file_browser_model import FileFilter


class OpenFilterController:
    """Loads, edits, and persists which files the open dialog lists."""

    def __init__(self, parent: QWidget, store: OpenFilterSettingsStore) -> None:
        self._parent = parent
        self._store = store
        self._settings = store.load()

    def current_filter(self) -> FileFilter:
        """The filter the open dialog should use right now."""
        if self._settings.all_files:
            return file_browser_strings.FILTER_ALL
        return FileFilter(file_browser_strings.OPEN_FILTER_LABEL, self._settings.extensions)

    # --- edit prompts (bound to palette commands) ---------------------------

    def toggle_all_files(self) -> None:
        """Flip between listing every file and only the extension list."""
        self._save(all_files=not self._settings.all_files)

    def edit_extensions(self) -> None:
        """Prompt for the extension list; a non-empty answer switches to list mode."""
        current = ", ".join(e.lstrip(".") for e in self._settings.extensions)
        answer = text_prompt_dialog.prompt_text(
            self._parent,
            settings_strings.DIALOG_OPEN_FILTER_TITLE,
            settings_strings.PROMPT_OPEN_FILTER_EXTENSIONS,
            current,
        )
        if answer is None:
            return
        extensions = parse_extensions(answer)
        if extensions:
            self._save(extensions=extensions, all_files=False)

    # --- internals ----------------------------------------------------------

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
