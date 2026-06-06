"""Persistence for the last-used text-field placement mode (global, JSON-backed).

Stores a single mode id (a ``PlacementMode`` value) so the placement chooser can
float the last pick to the top across restarts. Kept Qt-free — it deals in raw
strings and leaves the enum conversion to the GUI layer — so config never depends
on ``app.gui``.
"""

from __future__ import annotations

from pathlib import Path

from app.io.json_store import read_versioned_dict, write_versioned

PLACEMENT_VERSION = 1


class PlacementStore:
    """Reads and writes the last placement-mode id at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> str | None:
        """Return the stored mode id, or ``None`` if absent/corrupt."""
        raw = read_versioned_dict(self._path, PLACEMENT_VERSION)
        if raw is None:
            return None
        value = raw.get("last_mode")
        return value if isinstance(value, str) else None

    def save(self, last_mode: str) -> None:
        write_versioned(self._path, PLACEMENT_VERSION, {"last_mode": last_mode})
