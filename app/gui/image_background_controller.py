"""Owns the transparency backdrop for image documents: the live setting, its
picker command, persistence, and pushing changes to the render seam.

Persists every change via :class:`ImageBackgroundSettingsStore`, pushes it to
:func:`app.gui.render.set_image_background` (which ``render_page`` reads), then
reloads the open document so the new backdrop is composited immediately.
Mirrors :class:`TextViewController` so the window stays a thin coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtWidgets import QWidget

from app.config.image_background_settings import (
    ImageBackground,
    ImageBackgroundSettingsStore,
)
from app.gui import settings_strings
from app.gui.filter_list_dialog import pick_option
from app.gui.render import set_image_background

_BACKGROUND_LABELS: dict[ImageBackground, str] = {
    ImageBackground.WHITE: settings_strings.IMAGE_BACKGROUND_WHITE,
    ImageBackground.BLACK: settings_strings.IMAGE_BACKGROUND_BLACK,
    ImageBackground.GREEN: settings_strings.IMAGE_BACKGROUND_GREEN,
    ImageBackground.BLUE: settings_strings.IMAGE_BACKGROUND_BLUE,
    ImageBackground.CHECKER: settings_strings.IMAGE_BACKGROUND_CHECKER,
}


class ImageBackgroundController:
    """Loads, edits, persists, and applies the transparency-backdrop setting."""

    def __init__(
        self,
        parent: QWidget,
        store: ImageBackgroundSettingsStore,
        reload_document: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._store = store
        self._reload = reload_document
        self._settings = store.load()
        set_image_background(self._settings)

    def set_background(self) -> None:
        """Choose the backdrop behind transparent pixels from a keyboard-driven list."""
        chosen = pick_option(
            self._parent,
            _BACKGROUND_LABELS,
            title=settings_strings.DIALOG_IMAGE_BACKGROUND_TITLE,
            placeholder=settings_strings.IMAGE_BACKGROUND_PLACEHOLDER,
        )
        if chosen is not None:
            self._save(chosen)

    def _save(self, background: ImageBackground) -> None:
        self._settings = replace(self._settings, background=background)
        self._store.save(self._settings)
        set_image_background(self._settings)
        self._reload()
