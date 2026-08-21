"""The OCR: language… command — pick and persist the recognition language.

Mirrors :mod:`app.gui.image_background_controller`, minus a render seam: the
choice only affects the next OCR run, so nothing needs reloading.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from app.gui import ocr_strings
from app.gui.filter_list_dialog import pick_option

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from app.config.ocr_settings import OcrSettingsStore
    from app.ocr.provider import OcrProvider


class OcrLanguageController:
    """Owns the persisted OCR language and its palette picker."""

    def __init__(self, parent: QWidget, store: OcrSettingsStore, provider: OcrProvider) -> None:
        self._parent = parent
        self._store = store
        self._provider = provider

    def current_language(self) -> str | None:
        """The stored language tag, or ``None`` for automatic detection.

        Loaded fresh so external changes (e.g. a settings reset) take effect
        on the next OCR run without a restart.
        """
        return self._store.load().language or None

    def set_language(self) -> None:
        labels: dict[str, str] = {"": ocr_strings.LABEL_OCR_LANG_AUTO}
        for lang in self._provider.available_languages():
            labels[lang.tag] = f"{lang.display_name} ({lang.tag})"
        chosen = pick_option(
            self._parent,
            labels,
            title=ocr_strings.DIALOG_OCR_LANGUAGE_TITLE,
            placeholder=ocr_strings.OCR_LANGUAGE_PLACEHOLDER,
        )
        if chosen is None:
            return
        self._store.save(replace(self._store.load(), language=chosen))
