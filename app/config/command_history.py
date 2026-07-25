"""Persistence for the command-palette usage history (global, JSON-backed).

Keeps an ordered, deduplicated list of command ids, most-recent first, capped at
:data:`MAX_HISTORY`. The palette uses it to float recently-run commands to the
top. Tolerant of a missing or corrupt file (treated as empty) so a bad write
never blocks the palette.

The pure reordering rule (``order_ids``) now lives in the extracted
``command_palette`` library — re-exported here so the existing import path
keeps working. Only the sqlite-backed store stays app-specific.
"""

from __future__ import annotations

from command_palette.entries import order_ids as order_ids

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

MAX_HISTORY = 50
COMMAND_HISTORY_VERSION = 1
COMMAND_HISTORY_KEY = "command_history"


class CommandHistoryStore(RecordStore):
    """Reads and writes the command-usage history via the storage backend."""

    LABEL = "Command palette usage history"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, COMMAND_HISTORY_KEY)

    def load(self) -> list[str]:
        """Return the stored command ids, most-recent first; ``[]`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, COMMAND_HISTORY_VERSION)
        if raw is None:
            return []
        ids = raw.get("ids", [])
        if not isinstance(ids, list):
            return []
        return [item for item in ids if isinstance(item, str)]

    def add(self, command_id: str) -> None:
        """Record ``command_id`` as the most-recent entry (dedup, move-to-front, cap)."""
        existing = [cid for cid in self.load() if cid != command_id]
        ordered = [command_id, *existing][:MAX_HISTORY]
        self._write(ordered)

    def _write(self, ids: list[str]) -> None:
        self._backend.set_versioned(self._key, COMMAND_HISTORY_VERSION, {"ids": ids})
