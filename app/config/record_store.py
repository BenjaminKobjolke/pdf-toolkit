"""Base class for the small remembered-preference stores.

Every remembered setting persists one versioned JSON object under a fixed string
``key`` in the shared :class:`~app.storage.backend.StorageBackend`. This base
gives them a uniform :meth:`reset` (delete the row, restoring defaults on next
load) and a human-readable :attr:`label`, so the "Remembered settings" command
can list and reset them without a hardcoded table.
"""

from __future__ import annotations

from app.storage.backend import StorageBackend


class RecordStore:
    """A config store persisted as one row in the shared storage backend."""

    LABEL = "setting"

    def __init__(self, backend: StorageBackend, key: str) -> None:
        self._backend = backend
        self._key = key

    @property
    def label(self) -> str:
        """Human-readable name shown in the Remembered-settings command."""
        return self.LABEL

    def reset(self) -> None:
        """Forget the remembered value by deleting its row (no-op if absent)."""
        self._backend.delete_setting(self._key)
