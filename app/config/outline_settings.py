"""Persisted, cross-session appearance for the selected-item outline.

Tunes the rectangle drawn around the selected text field / image in edit mode:
its stroke width, line type (dashed / solid), and color. Stored as JSON next to
the other config stores, using the same versioned-dict pattern as
:mod:`app.config.palette_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

OUTLINE_SETTINGS_VERSION = 1
OUTLINE_KEY = "outline"

# Stroke-width bounds — single source of truth shared by the edit prompt
# (OutlineController) and any clamp, so the two can never drift apart.
WIDTH_PX_MIN, WIDTH_PX_MAX = 1, 12


class OutlineLineStyle(StrEnum):
    """The pen style offered for the selection outline."""

    SOLID = "solid"
    DASHED = "dashed"


@dataclass(frozen=True)
class OutlineSettings:
    """Remembered selection-outline appearance preferences."""

    width_px: int = 2
    style: OutlineLineStyle = OutlineLineStyle.DASHED
    color: str = "#FF0000"  # "#rrggbb"


class OutlineSettingsStore(SettingsRecordStore[OutlineSettings]):
    """Reads and writes :class:`OutlineSettings` via the storage backend."""

    LABEL = "Field outline appearance"
    VERSION = OUTLINE_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, OUTLINE_KEY, OutlineSettings())
