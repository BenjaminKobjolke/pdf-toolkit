"""Persisted, cross-session default zoom applied when a PDF first loads.

Remembers whether the viewer opens pages fit-to-window or at a fixed percentage.
Persisted via the shared storage backend, like the other config stores.

The :func:`zoom_to_dict` / :func:`zoom_from_dict` helpers are the single
(de)serialization for a :class:`ZoomSettings`, reused by both this global store
and the per-document zoom store so their on-disk shape and clamp can never drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

ZOOM_SETTINGS_VERSION = 1
ZOOM_KEY = "zoom"

# Percentage bounds — single source of truth shared by the edit prompt
# (ZoomSettingsController) and the load clamp, so the two can never drift apart.
ZOOM_PCT_MIN, ZOOM_PCT_MAX = 10, 800


def _clamp_percent(value: int) -> int:
    return max(ZOOM_PCT_MIN, min(value, ZOOM_PCT_MAX))


@dataclass(frozen=True)
class ZoomSettings:
    """Remembered default zoom. ``percent`` is ignored while ``fit`` is True."""

    fit: bool = True
    percent: int = 100


def zoom_to_dict(settings: ZoomSettings) -> dict[str, Any]:
    """Serialize ``settings`` to a plain dict (percent clamped to bounds)."""
    return {"fit": settings.fit, "percent": _clamp_percent(settings.percent)}


def zoom_from_dict(raw: dict[str, Any]) -> ZoomSettings:
    """Rebuild :class:`ZoomSettings` from ``raw``, filling gaps with defaults."""
    default = ZoomSettings()
    return ZoomSettings(
        fit=bool(raw.get("fit", default.fit)),
        percent=_clamp_percent(int(raw.get("percent", default.percent))),
    )


class ZoomSettingsStore(RecordStore):
    """Reads and writes :class:`ZoomSettings` via the storage backend."""

    LABEL = "Default zoom"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, ZOOM_KEY)

    def load(self) -> ZoomSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, ZOOM_SETTINGS_VERSION)
        if raw is None:
            return ZoomSettings()
        return zoom_from_dict(raw)

    def save(self, settings: ZoomSettings) -> None:
        self._backend.set_versioned(self._key, ZOOM_SETTINGS_VERSION, zoom_to_dict(settings))
