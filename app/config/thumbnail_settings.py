"""Persisted, cross-session thumbnail size for the thumbnails view.

The edge length (px) of the grid previews in the viewer's thumbnails view.
Uses the same versioned-dict pattern as :mod:`app.config.text_view_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

THUMB_SETTINGS_VERSION = 1
THUMB_KEY = "thumbnails"

# Pixel bounds — single source of truth shared by the zoom stepping and clamp.
THUMB_PX_MIN, THUMB_PX_MAX = 64, 1024


def clamp_thumb_size(value: int) -> int:
    """Clamp a thumbnail edge length to the supported pixel bounds."""
    return max(THUMB_PX_MIN, min(value, THUMB_PX_MAX))


@dataclass(frozen=True)
class ThumbnailSettings:
    """Remembered thumbnails-view preferences."""

    size: int = 256


class ThumbnailSettingsStore(SettingsRecordStore[ThumbnailSettings]):
    """Reads and writes :class:`ThumbnailSettings` via the storage backend."""

    LABEL = "Thumbnail size"
    VERSION = THUMB_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, THUMB_KEY, ThumbnailSettings())
