"""Persistence for the main-window geometry (global, JSON-backed).

Remembers the window's position and size so the viewer reopens where the user
left it. Fullscreen/maximized state is intentionally not stored — callers save
the underlying windowed rect. Tolerant of a missing or corrupt file (treated as
absent) so a bad write never blocks startup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.io.json_store import read_versioned_dict, write_versioned

WINDOW_GEOMETRY_VERSION = 1


@dataclass(frozen=True)
class WindowGeometry:
    """A remembered window rectangle."""

    x: int
    y: int
    width: int
    height: int


class WindowGeometryStore:
    """Reads and writes :class:`WindowGeometry` at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> WindowGeometry | None:
        """Return the stored geometry, or ``None`` if absent/corrupt/incomplete."""
        raw = read_versioned_dict(self._path, WINDOW_GEOMETRY_VERSION)
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
        write_versioned(
            self._path,
            WINDOW_GEOMETRY_VERSION,
            {"x": geom.x, "y": geom.y, "width": geom.width, "height": geom.height},
        )
