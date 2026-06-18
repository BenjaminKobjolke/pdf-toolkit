"""The storage seam every config store depends on.

:class:`StorageBackend` is the *only* persistence surface stores see. Anything
engine-specific — SQL text, parameter placeholders, upsert syntax, DDL column
types — lives inside an implementation and never leaks past this boundary, so
adding a new backend (MySQL, Postgres, …) is a new class plus a factory branch
with no changes to stores.

Two kinds of data:

* **Settings** — one versioned JSON object per string ``key`` (the global
  preferences: zoom, outline, window geometry, …).
* **Documents** — rows keyed by ``(namespace, doc_key)``, one JSON value each.
  This is the per-document table that grows with the number of PDFs a user has
  opened; lookups and writes touch a single indexed row.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Persistence operations shared by every remembered-settings store."""

    # --- settings: one versioned JSON object per key ------------------------

    def get_versioned(self, key: str, version: int) -> dict[str, Any] | None:
        """Return the stored object for ``key``, or ``None``.

        ``None`` when the key is absent, the stored value is not a JSON object,
        or its ``"version"`` does not match ``version``. A corrupt value is
        treated as absent (logged, not raised) so a bad write never blocks the
        app.
        """
        ...

    def set_versioned(self, key: str, version: int, payload: dict[str, Any]) -> None:
        """Upsert ``payload`` for ``key`` with ``version`` injected as ``"version"``."""
        ...

    def delete_setting(self, key: str) -> None:
        """Remove ``key`` (no-op if absent)."""
        ...

    # --- documents: rows keyed by (namespace, doc_key) ----------------------

    def document_value(self, namespace: str, doc_key: str) -> Any | None:
        """Return the stored value for ``(namespace, doc_key)``, or ``None`` if absent."""
        ...

    def put_document(self, namespace: str, doc_key: str, value: Any) -> None:
        """Upsert ``value`` (any JSON-serializable object) for ``(namespace, doc_key)``."""
        ...

    def delete_document(self, namespace: str, doc_key: str) -> None:
        """Remove a single document row (no-op if absent)."""
        ...

    def clear_namespace(self, namespace: str) -> None:
        """Remove every document row in ``namespace``."""
        ...

    def close(self) -> None:
        """Release the underlying connection/handles."""
        ...
