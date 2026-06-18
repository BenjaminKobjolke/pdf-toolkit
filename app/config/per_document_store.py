"""Base for per-document remembered values (one dimension per subclass).

Each subclass remembers one kind of value (zoom, page, …) keyed by document
path, backed by the storage backend's ``document_memory`` table so a single
remember/forget touches one indexed row and the store scales with the number of
PDFs a user opens. An ``auto_all`` flag (a normal setting row) records whether the
value should be captured automatically for every document.

Subclasses provide ``_encode`` / ``_decode`` for their value type; everything
else — keying, the auto flag, and reset — lives here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, TypeVar

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

T = TypeVar("T")

_AUTO_VERSION = 1


class PerDocumentStore(RecordStore, Generic[T]):
    """Remembers one per-document value type plus an ``auto_all`` toggle."""

    def __init__(self, backend: StorageBackend, namespace: str) -> None:
        # The RecordStore key holds the auto-all flag; per-document values live in
        # the document table under ``namespace``.
        super().__init__(backend, f"{namespace}.auto_all")
        self._namespace = namespace

    # --- per-document values ------------------------------------------------

    def value_for(self, path: Path) -> T | None:
        """Return the remembered value for ``path``, or ``None`` if none."""
        raw = self._backend.document_value(self._namespace, _doc_key(path))
        return None if raw is None else self._decode(raw)

    def remember(self, path: Path, value: T) -> None:
        """Persist ``value`` as the remembered value for ``path``."""
        self._backend.put_document(self._namespace, _doc_key(path), self._encode(value))

    def forget(self, path: Path) -> None:
        """Drop the remembered value for ``path`` (the auto flag is kept)."""
        self._backend.delete_document(self._namespace, _doc_key(path))

    def forget_all(self) -> None:
        """Drop every remembered value (the auto flag is kept)."""
        self._backend.clear_namespace(self._namespace)

    # --- auto-all toggle ----------------------------------------------------

    def auto_all(self) -> bool:
        """Whether the value is captured automatically for every document."""
        raw = self._backend.get_versioned(self._key, _AUTO_VERSION)
        return bool(raw["enabled"]) if raw else False

    def set_auto_all(self, enabled: bool) -> None:
        self._backend.set_versioned(self._key, _AUTO_VERSION, {"enabled": enabled})

    # --- reset (Remembered-settings command) --------------------------------

    def reset(self) -> None:
        """Clear all remembered values *and* the auto flag for this dimension."""
        self._backend.clear_namespace(self._namespace)
        self._backend.delete_setting(self._key)

    # --- subclass hooks -----------------------------------------------------

    def _encode(self, value: T) -> Any:
        raise NotImplementedError

    def _decode(self, raw: Any) -> T:
        raise NotImplementedError


def _doc_key(path: Path) -> str:
    """Stable, absolute key for a document path (cross-session matching)."""
    return str(path.resolve())
