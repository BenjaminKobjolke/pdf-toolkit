"""Persisted OCR settings (recognition language).

An empty ``language`` means automatic — the engine picks from the Windows user
profile languages. Otherwise it is a BCP-47 tag of an installed OCR language
pack (e.g. ``"de-DE"``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config.record_store import SettingsRecordStore

if TYPE_CHECKING:
    from app.storage.backend import StorageBackend

OCR_SETTINGS_VERSION = 1
OCR_KEY = "ocr"


@dataclass(frozen=True)
class OcrSettings:
    """The user's OCR preferences; ``language=""`` selects automatic detection."""

    language: str = ""


class OcrSettingsStore(SettingsRecordStore[OcrSettings]):
    """Versioned sqlite persistence for :class:`OcrSettings`."""

    LABEL = "OCR language"
    VERSION = OCR_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, OCR_KEY, OcrSettings())
