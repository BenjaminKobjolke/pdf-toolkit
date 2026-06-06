"""Persisted, cross-session default zoom applied when a PDF first loads.

Remembers whether the viewer opens pages fit-to-window or at a fixed percentage.
Stored as JSON next to the other config stores, using the same versioned-dict
pattern as :mod:`app.config.palette_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.file_backed_store import FileBackedStore
from app.io.json_store import read_versioned_dict, write_versioned

ZOOM_SETTINGS_VERSION = 1

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


class ZoomSettingsStore(FileBackedStore):
    """Reads and writes :class:`ZoomSettings` at a fixed JSON path."""

    LABEL = "Default zoom"

    def load(self) -> ZoomSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = read_versioned_dict(self._path, ZOOM_SETTINGS_VERSION)
        if raw is None:
            return ZoomSettings()
        default = ZoomSettings()
        return ZoomSettings(
            fit=bool(raw.get("fit", default.fit)),
            percent=_clamp_percent(int(raw.get("percent", default.percent))),
        )

    def save(self, settings: ZoomSettings) -> None:
        write_versioned(
            self._path,
            ZOOM_SETTINGS_VERSION,
            {"fit": settings.fit, "percent": _clamp_percent(settings.percent)},
        )
