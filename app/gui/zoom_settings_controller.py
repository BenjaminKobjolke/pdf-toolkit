"""Owns the default zoom: the remembered setting, its edit prompt, persistence,
and pushing the choice to the page view.

Persists every change via :class:`ZoomSettingsStore` and pushes it into the
:class:`~app.gui.page_view.PageView` (which applies it on the next render, or
immediately when a document is already open) — mirroring
:class:`~app.gui.outline_controller.OutlineController`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from app.config.zoom_settings import (
    ZOOM_PCT_MAX,
    ZOOM_PCT_MIN,
    ZoomSettings,
    ZoomSettingsStore,
)
from app.gui import number_input_dialog, settings_strings
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry

if TYPE_CHECKING:
    from app.gui.page_view import PageView

# Quick-pick percentages offered alongside "Fit to window" and "Custom…".
_PRESETS = (50, 75, 100, 150, 200)
# Sentinel payload marking the "Custom percentage…" row (prompts for a number).
_CUSTOM = object()


class ZoomSettingsController:
    """Loads, edits, persists, and applies the default-zoom setting."""

    def __init__(self, parent: QWidget, store: ZoomSettingsStore, page_view: PageView) -> None:
        self._parent = parent
        self._store = store
        self._page_view = page_view
        self._settings = store.load()
        page_view.set_default_zoom(self._settings.fit, self._settings.percent)

    def current(self) -> ZoomSettings:
        """Return the global default zoom (fallback when no per-document zoom)."""
        return self._settings

    def set_default_zoom(self) -> None:
        """Pick Fit / a preset / a custom percentage, then persist and apply it."""
        entries = [ListEntry(title=settings_strings.ZOOM_FIT_LABEL, payload=ZoomSettings(fit=True))]
        for pct in _PRESETS:
            title = settings_strings.ZOOM_PERCENT_FMT.format(n=pct)
            entries.append(ListEntry(title=title, payload=ZoomSettings(fit=False, percent=pct)))
        entries.append(ListEntry(title=settings_strings.ZOOM_CUSTOM_LABEL, payload=_CUSTOM))
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=settings_strings.ZOOM_PLACEHOLDER,
                title=settings_strings.DIALOG_DEFAULT_ZOOM_TITLE,
            ),
            parent=self._parent,
        )
        if not dialog.exec() or (chosen := dialog.chosen()) is None:
            return
        settings = self._prompt_custom() if chosen.payload is _CUSTOM else chosen.payload
        if settings is not None:
            self._save(settings)

    # --- internals ----------------------------------------------------------

    def _prompt_custom(self) -> ZoomSettings | None:
        value = number_input_dialog.prompt_int(
            self._parent,
            number_input_dialog.NumberPromptSpec(
                title=settings_strings.DIALOG_DEFAULT_ZOOM_TITLE,
                label=settings_strings.PROMPT_DEFAULT_ZOOM_PCT,
                value=self._settings.percent,
                minimum=ZOOM_PCT_MIN,
                maximum=ZOOM_PCT_MAX,
            ),
        )
        return ZoomSettings(fit=False, percent=value) if value is not None else None

    def _save(self, settings: ZoomSettings) -> None:
        self._settings = settings
        self._store.save(settings)
        self._page_view.set_default_zoom(settings.fit, settings.percent)
