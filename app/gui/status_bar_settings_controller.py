"""Owns the footer's appearance: the live settings, their edit prompt,
persistence, and applying changes to the footer widgets.

The footer is two rows — the mode status bar and the thumbnail "Filter: …"
label above it — so the one font-size setting is applied to every widget handed
in. Persists every change via :class:`StatusBarSettingsStore`, so the window
stays a thin coordinator (mirrors :class:`TextViewController` /
:class:`PaletteController`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from PySide6.QtWidgets import QWidget

from app.config.status_bar_settings import (
    FONT_PT_MAX,
    FONT_PT_MIN,
    StatusBarSettingsStore,
)
from app.gui import number_input_dialog, settings_strings


class StatusBarSettingsController:
    """Loads, edits, persists, and applies the footer appearance settings."""

    def __init__(
        self, parent: QWidget, widgets: Sequence[QWidget], store: StatusBarSettingsStore
    ) -> None:
        self._parent = parent
        self._widgets = list(widgets)
        # Captured before the first apply so 0 can restore each widget's default.
        self._default_pts = [w.font().pointSize() for w in self._widgets]
        self._store = store
        self._settings = store.load()
        self._apply(self._settings.font_pt)

    def set_font_size(self) -> None:
        """Prompt for the footer's font size in points (0 = reset to default).

        When unset, the prompt is pre-filled with the actual current size rather
        than ``0``, so the spinner shows a real number.
        """
        current = self._settings.font_pt or max(
            self._widgets[0].font().pointSize(), FONT_PT_MIN + 1
        )
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=settings_strings.DIALOG_STATUSBAR_FONT_TITLE,
                label=settings_strings.PROMPT_FONT_PT_ZERO_DEFAULT,
                value=current,
                minimum=FONT_PT_MIN,
                maximum=FONT_PT_MAX,
            ),
        )
        if value is not None:
            self._settings = replace(self._settings, font_pt=value)
            self._store.save(self._settings)
            self._apply(value)

    def _apply(self, pt: int) -> None:
        for widget, default_pt in zip(self._widgets, self._default_pts, strict=True):
            font = widget.font()
            font.setPointSize(pt or default_pt)
            widget.setFont(font)
