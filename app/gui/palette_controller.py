"""Owns command-palette appearance: the live settings, their edit prompts, and
applying them to a palette dialog. Persists every change via
:class:`PaletteSettingsStore`, so the window stays a thin coordinator.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog, QWidget

from app.config.palette_settings import (
    DIALOG_PCT_MAX,
    DIALOG_PCT_MIN,
    FONT_PT_MAX,
    FONT_PT_MIN,
    HEIGHT_PCT_MAX,
    HEIGHT_PCT_MIN,
    OPACITY_PCT_MAX,
    OPACITY_PCT_MIN,
    WIDTH_PCT_MAX,
    WIDTH_PCT_MIN,
    PaletteSettingsStore,
)
from app.gui import dialog_appearance, number_input_dialog, settings_strings
from app.gui.palette_appearance import apply_appearance


class PaletteController:
    """Loads, edits, persists, and applies the palette appearance settings."""

    def __init__(self, parent: QWidget, store: PaletteSettingsStore) -> None:
        self._parent = parent
        self._store = store
        self._settings = store.load()
        dialog_appearance.set_active(self._settings)

    def apply_to(self, dialog: QDialog, window_size: QSize) -> None:
        """Size/style/flag ``dialog`` from the current settings before it shows."""
        apply_appearance(dialog, self._settings, window_size)

    # --- edit prompts (bound to palette commands) ---------------------------

    def set_width(self) -> None:
        """Prompt for the palette width as a percentage of the window."""
        self._edit_int(
            "width_pct",
            settings_strings.DIALOG_PALETTE_WIDTH_TITLE,
            settings_strings.PROMPT_PALETTE_WIDTH,
            WIDTH_PCT_MIN,
            WIDTH_PCT_MAX,
        )

    def set_height(self) -> None:
        """Prompt for the palette height as a percentage of the window."""
        self._edit_int(
            "height_pct",
            settings_strings.DIALOG_PALETTE_HEIGHT_TITLE,
            settings_strings.PROMPT_PALETTE_HEIGHT,
            HEIGHT_PCT_MIN,
            HEIGHT_PCT_MAX,
        )

    def set_dialog_size(self) -> None:
        """Prompt for the list/picker dialog size as a percentage of the window."""
        self._edit_int(
            "dialog_size_pct",
            settings_strings.DIALOG_DIALOG_SIZE_TITLE,
            settings_strings.PROMPT_DIALOG_SIZE,
            DIALOG_PCT_MIN,
            DIALOG_PCT_MAX,
        )

    def set_font_size(self) -> None:
        """Prompt for the palette font size in points (0 = reset to default).

        When unset, the prompt is pre-filled with the actual default size rather
        than ``0``, so the spinner shows a real number.
        """
        current = self._settings.font_pt or max(self._parent.font().pointSize(), FONT_PT_MIN + 1)
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=settings_strings.DIALOG_PALETTE_FONT_TITLE,
                label=settings_strings.PROMPT_PALETTE_FONT,
                value=current,
                minimum=FONT_PT_MIN,
                maximum=FONT_PT_MAX,
            ),
        )
        if value is not None:
            self._save(font_pt=value)

    def set_opacity(self) -> None:
        """Prompt for the palette opacity as a percentage."""
        self._edit_int(
            "opacity_pct",
            settings_strings.DIALOG_PALETTE_OPACITY_TITLE,
            settings_strings.PROMPT_PALETTE_OPACITY,
            OPACITY_PCT_MIN,
            OPACITY_PCT_MAX,
        )

    def toggle_borderless(self) -> None:
        """Flip the palette frameless-window preference."""
        self._save(borderless=not self._settings.borderless)

    # --- internals ----------------------------------------------------------

    def _edit_int(self, field_name: str, title: str, prompt: str, low: int, high: int) -> None:
        """Prompt for one bounded integer field, then persist it."""
        current = int(getattr(self._settings, field_name))
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=title, label=prompt, value=current, minimum=low, maximum=high
            ),
        )
        if value is not None:
            self._save(**{field_name: value})

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        dialog_appearance.set_active(self._settings)
