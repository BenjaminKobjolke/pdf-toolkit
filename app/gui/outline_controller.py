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
from app.gui import number_input_dialog, strings
from app.gui.color_picker_dialog import ColorPickerDialog
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.outline_style import OutlineStyle

_STYLE_LABELS: dict[OutlineLineStyle, str] = {
    OutlineLineStyle.DASHED: strings.OUTLINE_STYLE_DASHED,
    OutlineLineStyle.SOLID: strings.OUTLINE_STYLE_SOLID,
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
            strings.DIALOG_OUTLINE_WIDTH_TITLE,
            strings.PROMPT_OUTLINE_WIDTH,
            self._settings.width_px,
            WIDTH_PX_MIN,
            WIDTH_PX_MAX,
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
            placeholder=strings.OUTLINE_STYLE_PLACEHOLDER,
            title=strings.DIALOG_OUTLINE_STYLE_TITLE,
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._save(style=chosen.payload)

    def set_color(self) -> None:
        """Pick the outline color via the shared color dialog."""
        dialog = ColorPickerDialog(
            recent=self._recent_colors,
            title=strings.DIALOG_OUTLINE_COLOR_TITLE,
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._remember_color(chosen)
            self._save(color=chosen)

    # --- internals ----------------------------------------------------------

    def _remember_color(self, hex_value: str) -> None:
        if hex_value in self._recent_colors:
            self._recent_colors.remove(hex_value)
        self._recent_colors.insert(0, hex_value)
        del self._recent_colors[8:]

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        self._holder.set(self._settings)
        self._request_repaint()
