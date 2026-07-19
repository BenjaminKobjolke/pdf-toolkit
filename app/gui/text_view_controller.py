"""Owns text/markdown appearance: the live settings, their edit prompts,
persistence, and applying them to the render seam.

Persists every change via :class:`TextViewSettingsStore`, pushes it to
:func:`app.pdf.file_format.set_text_view_settings` (which the renderer reads),
then reloads the open document — font size changes pagination, so a re-open +
re-count is needed, not just a repaint. Mirrors :class:`PaletteController` /
:class:`OutlineController` so the window stays a thin coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from PySide6.QtWidgets import QWidget

from app.config.text_view_settings import (
    FONT_PT_MAX,
    FONT_PT_MIN,
    TextViewSettingsStore,
)
from app.gui import number_input_dialog, settings_strings
from app.pdf.file_format import set_text_view_settings


class TextViewController:
    """Loads, edits, persists, and applies the text/markdown appearance settings."""

    def __init__(
        self,
        parent: QWidget,
        store: TextViewSettingsStore,
        reload_document: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._store = store
        self._reload = reload_document
        self._settings = store.load()
        set_text_view_settings(self._settings)

    def apply_saved(self) -> None:
        """Push the stored settings to the render seam (call before first render)."""
        set_text_view_settings(self._settings)

    # --- edit prompts (bound to palette commands) ---------------------------

    def toggle_dark_mode(self) -> None:
        """Flip the light/dark reading theme for text/markdown documents."""
        self._save(dark_mode=not self._settings.dark_mode)

    def set_font_size(self) -> None:
        """Prompt for the text/markdown base font size in points."""
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=settings_strings.DIALOG_TEXT_FONT_TITLE,
                label=settings_strings.PROMPT_TEXT_FONT,
                value=self._settings.font_pt,
                minimum=FONT_PT_MIN,
                maximum=FONT_PT_MAX,
            ),
        )
        if value is not None:
            self._save(font_pt=value)

    # --- internals ----------------------------------------------------------

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        set_text_view_settings(self._settings)
        self._reload()
