"""Persistence for the last-used text-field placement mode (global, JSON-backed).

Stores a single mode id (a ``PlacementMode`` value) so the placement chooser can
float the last pick to the top across restarts. Kept Qt-free — it deals in raw
strings and leaves the enum conversion to the GUI layer — so config never depends
on ``app.gui``.
"""

from __future__ import annotations

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

PLACEMENT_VERSION = 1
PLACEMENT_KEY = "placement"


class PlacementStore(RecordStore):
    """Reads and writes the last placement-mode id via the storage backend."""

    LABEL = "Last overlay placement choice"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, PLACEMENT_KEY)

    def load(self) -> str | None:
        """Return the stored mode id, or ``None`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, PLACEMENT_VERSION)
        if raw is None:
            return None
        value = raw.get("last_mode")
        return value if isinstance(value, str) else None

    def save(self, last_mode: str) -> None:
        self._backend.set_versioned(self._key, PLACEMENT_VERSION, {"last_mode": last_mode})
