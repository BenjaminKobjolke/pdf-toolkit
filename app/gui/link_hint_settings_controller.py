"""Owns the link-overlay appearance: the live settings, their edit prompts,
persistence, and pushing changes to the shared style holder.

Persists every change via :class:`LinkHintSettingsStore` and mutates the shared
:class:`~app.gui.link_hint_style.LinkHintStyle` holder, then asks for a repaint —
so the window stays a thin coordinator (mirrors :class:`OutlineController`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from PySide6.QtWidgets import QWidget

from app.config.link_hint_settings import (
    FONT_PT_MAX,
    FONT_PT_MIN,
    LinkHintSettingsStore,
)
from app.gui import link_strings, number_input_dialog
from app.gui.color_picker_dialog import pick_color
from app.gui.link_hint_style import LinkHintStyle


class LinkHintSettingsController:
    """Loads, edits, persists, and applies the link-overlay appearance settings."""

    def __init__(
        self,
        parent: QWidget,
        store: LinkHintSettingsStore,
        holder: LinkHintStyle,
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

    def set_font_size(self) -> None:
        """Prompt for the hint letter's font size in points."""
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=link_strings.DIALOG_LINK_FONT_TITLE,
                label=link_strings.PROMPT_LINK_FONT,
                value=self._settings.font_pt,
                minimum=FONT_PT_MIN,
                maximum=FONT_PT_MAX,
            ),
        )
        if value is not None:
            self._save(font_pt=value)

    def set_text_color(self) -> None:
        """Pick the hint letter's text color."""
        self._pick_color(link_strings.DIALOG_LINK_TEXT_COLOR_TITLE, "text_color")

    def set_background_color(self) -> None:
        """Pick the chip fill behind the hint letter."""
        self._pick_color(link_strings.DIALOG_LINK_BG_COLOR_TITLE, "background_color")

    def set_box_color(self) -> None:
        """Pick the outline color of the box around each link."""
        self._pick_color(link_strings.DIALOG_LINK_BOX_COLOR_TITLE, "box_color")

    # --- internals ----------------------------------------------------------

    def _pick_color(self, title: str, field: str) -> None:
        chosen = pick_color(self._parent, self._recent_colors, title=title)
        if chosen is not None:
            self._save(**{field: chosen})

    def _save(self, **changes: Any) -> None:
        self._settings = replace(self._settings, **changes)
        self._store.save(self._settings)
        self._holder.set(self._settings)
        self._request_repaint()
