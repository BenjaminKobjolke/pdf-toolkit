"""Persisted, cross-session appearance for the selected-item outline.

Tunes the rectangle drawn around the selected text field / image in edit mode:
its stroke width, line type (dashed / solid), and color. Stored as JSON next to
the other config stores, using the same versioned-dict pattern as
:mod:`app.config.palette_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.record_store import RecordStore
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

    @classmethod
    def from_value(cls, value: str) -> OutlineLineStyle:
        """Return the matching member, or the default on an unknown value."""
        try:
            return cls(value)
        except ValueError:
            return OutlineSettings().style


@dataclass(frozen=True)
class OutlineSettings:
    """Remembered selection-outline appearance preferences."""

    width_px: int = 2
    style: OutlineLineStyle = OutlineLineStyle.DASHED
    color: str = "#FF0000"  # "#rrggbb"


class OutlineSettingsStore(RecordStore):
    """Reads and writes :class:`OutlineSettings` via the storage backend."""

    LABEL = "Field outline appearance"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, OUTLINE_KEY)

    def load(self) -> OutlineSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, OUTLINE_SETTINGS_VERSION)
        if raw is None:
            return OutlineSettings()
        default = OutlineSettings()
        return OutlineSettings(
            width_px=int(raw.get("width_px", default.width_px)),
            style=OutlineLineStyle.from_value(str(raw.get("style", default.style.value))),
            color=str(raw.get("color", default.color)),
        )

    def save(self, settings: OutlineSettings) -> None:
        self._backend.set_versioned(
            self._key,
            OUTLINE_SETTINGS_VERSION,
            {
                "width_px": settings.width_px,
                "style": settings.style.value,
                "color": settings.color,
            },
        )
