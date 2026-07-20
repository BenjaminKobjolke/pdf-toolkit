"""Persistence for the user's "Open with" application list (versioned, backend-backed).

Keeps an ordered, deduplicated list of executable paths the user opens the current
document with. Tolerant of a missing or corrupt row (treated as empty) so a bad
write never blocks the picker.
"""

from __future__ import annotations

from pathlib import Path

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

OPEN_WITH_VERSION = 1
OPEN_WITH_KEY = "open_with"


class OpenWithStore(RecordStore):
    """Reads and writes the open-with application list via the storage backend."""

    LABEL = "Open-with applications"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, OPEN_WITH_KEY)

    def load(self) -> list[Path]:
        """Return the stored app paths in order; ``[]`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, OPEN_WITH_VERSION)
        if raw is None:
            return []
        apps = raw.get("apps", [])
        if not isinstance(apps, list):
            return []
        return [Path(item) for item in apps if isinstance(item, str)]

    def add(self, app: Path) -> None:
        """Append ``app`` (dedup, keeping existing order — it's a menu, not a recency list)."""
        apps = self.load()
        if app not in apps:
            apps.append(app)
            self._write(apps)

    def remove(self, app: Path) -> None:
        """Drop ``app`` from the list (no-op if absent)."""
        self._write([p for p in self.load() if p != app])

    def _write(self, apps: list[Path]) -> None:
        self._backend.set_versioned(self._key, OPEN_WITH_VERSION, {"apps": [str(p) for p in apps]})
