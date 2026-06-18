"""Persistence for the recently-opened PDF list (global, JSON-backed).

The store keeps an ordered, deduplicated list of absolute PDF paths, most-recent
first, capped at :data:`MAX_RECENT`. It is tolerant of a missing or corrupt file
(treated as empty) so a bad write never blocks opening documents.
"""

from __future__ import annotations

from pathlib import Path

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

MAX_RECENT = 100
RECENT_VERSION = 1
RECENT_KEY = "recent"


class RecentFilesStore(RecordStore):
    """Reads and writes the recent-documents list via the storage backend."""

    LABEL = "Recent documents list"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, RECENT_KEY)

    def load(self) -> list[Path]:
        """Return the stored paths, most-recent first; ``[]`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, RECENT_VERSION)
        if raw is None:
            return []
        paths = raw.get("paths", [])
        if not isinstance(paths, list):
            return []
        return [Path(item) for item in paths if isinstance(item, str)]

    def add(self, pdf: Path) -> None:
        """Record ``pdf`` as the most-recent entry (dedup, move-to-front, cap)."""
        existing = [p for p in self.load() if p != pdf]
        ordered = [pdf, *existing][:MAX_RECENT]
        self._write(ordered)

    def clear(self) -> None:
        """Drop all recent entries."""
        self._write([])

    def _write(self, paths: list[Path]) -> None:
        self._backend.set_versioned(self._key, RECENT_VERSION, {"paths": [str(p) for p in paths]})
