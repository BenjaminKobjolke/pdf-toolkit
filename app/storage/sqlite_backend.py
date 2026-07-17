"""SQLite implementation of :class:`~app.storage.backend.StorageBackend`.

The default (and currently only) backend: a single local database file holding
both the ``settings`` and ``document_memory`` tables. SQLite gives atomic commits,
so writes need no temp-file dance. All SQLite-specific SQL (``?`` placeholders,
``ON CONFLICT`` upserts) is confined to this module.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.logging_setup import log

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_memory (
    namespace TEXT NOT NULL,
    doc_key   TEXT NOT NULL,
    value     TEXT NOT NULL,
    PRIMARY KEY (namespace, doc_key)
);
"""

__all__ = ["SqliteBackend", "log"]


class SqliteBackend:
    """A :class:`StorageBackend` backed by one local SQLite file."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False is safe: the GUI uses one thread, and tests
        # may construct on a different thread than they call from.
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # --- settings -----------------------------------------------------------

    def get_versioned(self, key: str, version: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        try:
            raw = json.loads(row[0])
        except json.JSONDecodeError as err:
            log.warning("ignoring unreadable setting %s: %s", key, err)
            return None
        if not isinstance(raw, dict) or raw.get("version") != version:
            log.warning("ignoring setting %s with bad shape/version", key)
            return None
        return raw

    def set_versioned(self, key: str, version: int, payload: dict[str, Any]) -> None:
        value = json.dumps({"version": version, **payload})
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()

    def delete_setting(self, key: str) -> None:
        self._conn.execute("DELETE FROM settings WHERE key = ?", (key,))
        self._conn.commit()

    # --- documents ----------------------------------------------------------

    def document_value(self, namespace: str, doc_key: str) -> Any | None:
        row = self._conn.execute(
            "SELECT value FROM document_memory WHERE namespace = ? AND doc_key = ?",
            (namespace, doc_key),
        ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError as err:
            log.warning("ignoring unreadable document %s/%s: %s", namespace, doc_key, err)
            return None

    def put_document(self, namespace: str, doc_key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT INTO document_memory (namespace, doc_key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(namespace, doc_key) DO UPDATE SET value = excluded.value",
            (namespace, doc_key, json.dumps(value)),
        )
        self._conn.commit()

    def delete_document(self, namespace: str, doc_key: str) -> None:
        self._conn.execute(
            "DELETE FROM document_memory WHERE namespace = ? AND doc_key = ?",
            (namespace, doc_key),
        )
        self._conn.commit()

    def clear_namespace(self, namespace: str) -> None:
        self._conn.execute("DELETE FROM document_memory WHERE namespace = ?", (namespace,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
