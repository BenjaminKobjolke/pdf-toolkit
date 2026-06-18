"""Persistence for the main-window geometry (global, JSON-backed).

Remembers the window's position and size so the viewer reopens where the user
left it. Fullscreen/maximized state is intentionally not stored — callers save
the underlying windowed rect. Tolerant of a missing or corrupt file (treated as
absent) so a bad write never blocks startup.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

WINDOW_GEOMETRY_VERSION = 1
WINDOW_GEOMETRY_KEY = "window"


@dataclass(frozen=True)
class WindowGeometry:
    """A remembered window rectangle."""

    x: int
    y: int
    width: int
    height: int


class WindowGeometryStore(RecordStore):
    """Reads and writes :class:`WindowGeometry` via the storage backend."""

    LABEL = "Window position and size"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, WINDOW_GEOMETRY_KEY)

    def load(self) -> WindowGeometry | None:
        """Return the stored geometry, or ``None`` if absent/corrupt/incomplete."""
        raw = self._backend.get_versioned(self._key, WINDOW_GEOMETRY_VERSION)
        if raw is None:
            return None
        try:
            return WindowGeometry(
                x=int(raw["x"]),
                y=int(raw["y"]),
                width=int(raw["width"]),
                height=int(raw["height"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def save(self, geom: WindowGeometry) -> None:
        self._backend.set_versioned(
            self._key,
            WINDOW_GEOMETRY_VERSION,
            {"x": geom.x, "y": geom.y, "width": geom.width, "height": geom.height},
        )
