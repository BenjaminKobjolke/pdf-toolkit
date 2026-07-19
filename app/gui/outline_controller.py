"""Owns the selected-item outline appearance: the live settings, their edit
prompts, persistence, and pushing changes to the shared style holder.

Persists every change via :class:`OutlineSettingsStore` and mutates the shared
:class:`~app.gui.outline_style.OutlineStyle` holder, then asks for a repaint — so
the window stays a thin coordinator (mirrors :class:`PaletteController`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from PySide6.QtWidgets import QWidget

from app.config.outline_settings import (
    WIDTH_PX_MAX,
    WIDTH_PX_MIN,
    OutlineLineStyle,
    OutlineSettingsStore,
)
from app.gui import number_input_dialog, settings_strings
from app.gui.color_picker_dialog import pick_color
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.outline_style import OutlineStyle

_STYLE_LABELS: dict[OutlineLineStyle, str] = {
    OutlineLineStyle.DASHED: settings_strings.OUTLINE_STYLE_DASHED,
    OutlineLineStyle.SOLID: settings_strings.OUTLINE_STYLE_SOLID,
}


class OutlineController:
    """Loads, edits, persists, and applies the selection-outline settings."""

    def __init__(
        self,
        parent: QWidget,
        store: OutlineSettingsStore,
        holder: OutlineStyle,
        request_repaint: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._store = store
        self._holder = holder
        self._request_repaint = request_repaint
        self._settings = store.load()
        self._holder.set(self._settings)
        self._recent_colors: list[str] = []

    # --- edit prompts (bound to palette commands) ---------------------------

    def set_width(self) -> None:
        """Prompt for the outline stroke width in pixels."""
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=settings_strings.DIALOG_OUTLINE_WIDTH_TITLE,
                label=settings_strings.PROMPT_OUTLINE_WIDTH,
                value=self._settings.width_px,
                minimum=WIDTH_PX_MIN,
                maximum=WIDTH_PX_MAX,
            ),
        )
        if value is not None:
            self._save(width_px=value)

    def set_style(self) -> None:
        """Choose the line type (dashed / solid) from a keyboard-driven list."""
        entries = [
            ListEntry(title=_STYLE_LABELS[style], payload=style)
            for style in (OutlineLineStyle.DASHED, OutlineLineStyle.SOLID)
        ]
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=settings_strings.OUTLINE_STYLE_PLACEHOLDER,
                title=settings_strings.DIALOG_OUTLINE_STYLE_TITLE,
            ),
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._save(style=chosen.payload)

    def set_color(self) -> None:
        """Pick the outline color via the shared color dialog."""
        chosen = pick_color(
            self._parent,
            self._recent_colors,
            title=settings_strings.DIALOG_OUTLINE_COLOR_TITLE,
        )
        if chosen is not None:
            self._save(color=chosen)

    # --- internals ----------------------------------------------------------

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        self._holder.set(self._settings)
        self._request_repaint()
