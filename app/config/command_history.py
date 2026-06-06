"""Persistence for the command-palette usage history (global, JSON-backed).

Keeps an ordered, deduplicated list of command ids, most-recent first, capped at
:data:`MAX_HISTORY`. The palette uses it to float recently-run commands to the
top. Tolerant of a missing or corrupt file (treated as empty) so a bad write
never blocks the palette.
"""

from __future__ import annotations

from pathlib import Path

from app.io.json_store import read_versioned_dict, write_versioned

MAX_HISTORY = 50
COMMAND_HISTORY_VERSION = 1


def order_ids(all_ids: list[str], mru: list[str]) -> list[str]:
    """Return ``all_ids`` reordered so ``mru`` entries lead, most-recent first.

    Ids present in ``mru`` come first in ``mru`` order (ignoring any that are not
    in ``all_ids``), followed by the remaining ``all_ids`` in their original
    order. Pure and Qt-free so the ordering rule is unit-testable on its own.
    """
    known = set(all_ids)
    leading = [cid for cid in mru if cid in known]
    leading_set = set(leading)
    trailing = [cid for cid in all_ids if cid not in leading_set]
    return [*leading, *trailing]


class CommandHistoryStore:
    """Reads and writes the command-usage history at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[str]:
        """Return the stored command ids, most-recent first; ``[]`` if absent/corrupt."""
        raw = read_versioned_dict(self._path, COMMAND_HISTORY_VERSION)
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
        write_versioned(self._path, COMMAND_HISTORY_VERSION, {"ids": ids})
