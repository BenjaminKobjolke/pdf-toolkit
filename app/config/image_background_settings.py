"""Persisted, cross-session backdrop for transparent image documents.

What shows behind transparent pixels when an image with an alpha channel is
rendered: white (the historical default), black, greenscreen green/blue, or a
checkered pattern. Stored via the same versioned pattern as
:mod:`app.config.outline_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

IMAGE_BACKGROUND_SETTINGS_VERSION = 1
IMAGE_BACKGROUND_KEY = "image_background"


class ImageBackground(StrEnum):
    """The backdrop drawn behind transparent pixels of image documents."""

    WHITE = "white"
    BLACK = "black"
    GREEN = "green"
    BLUE = "blue"
    CHECKER = "checker"


@dataclass(frozen=True)
class ImageBackgroundSettings:
    """Remembered transparency-backdrop preference."""

    background: ImageBackground = ImageBackground.WHITE


class ImageBackgroundSettingsStore(SettingsRecordStore[ImageBackgroundSettings]):
    """Reads and writes :class:`ImageBackgroundSettings` via the storage backend."""

    LABEL = "Image transparency background"
    VERSION = IMAGE_BACKGROUND_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, IMAGE_BACKGROUND_KEY, ImageBackgroundSettings())
