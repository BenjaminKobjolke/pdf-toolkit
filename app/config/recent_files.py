"""Persistence for the recently-opened PDF list (global, JSON-backed).

The store keeps an ordered, deduplicated list of absolute PDF paths, most-recent
first, capped at :data:`MAX_RECENT`. It is tolerant of a missing or corrupt file
(treated as empty) so a bad write never blocks opening documents.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.io.json_store import write_json_atomic

log = logging.getLogger("pdf_toolkit")

MAX_RECENT = 100
RECENT_VERSION = 1


class RecentFilesStore:
    """Reads and writes the recent-documents list at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[Path]:
        """Return the stored paths, most-recent first; ``[]`` if absent/corrupt."""
        if not self._path.is_file():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            log.warning("ignoring unreadable recent-files store %s: %s", self._path, err)
            return []
        if not isinstance(raw, dict) or raw.get("version") != RECENT_VERSION:
            log.warning("ignoring recent-files store %s with bad shape/version", self._path)
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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": RECENT_VERSION, "paths": [str(p) for p in paths]}
        write_json_atomic(self._path, payload)
