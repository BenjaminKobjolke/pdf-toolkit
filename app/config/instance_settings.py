"""Persisted, cross-session single-instance preference.

Whether launching the viewer with a file should reuse an already-running
window (forwarded over the local socket in :mod:`app.gui.single_instance`)
or start a fresh instance. Uses the same versioned-dict pattern as
:mod:`app.config.open_filter_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

INSTANCE_VERSION = 1
INSTANCE_KEY = "instance"


@dataclass(frozen=True)
class InstanceSettings:
    """Remembered single-instance preference (default: reuse the window)."""

    reuse_window: bool = True


class InstanceSettingsStore(RecordStore):
    """Reads and writes :class:`InstanceSettings` via the storage backend."""

    LABEL = "Reuse existing window"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, INSTANCE_KEY)

    def load(self) -> InstanceSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, INSTANCE_VERSION)
        if raw is None:
            return InstanceSettings()
        default = InstanceSettings()
        return InstanceSettings(reuse_window=bool(raw.get("reuse_window", default.reuse_window)))

    def save(self, settings: InstanceSettings) -> None:
        self._backend.set_versioned(
            self._key,
            INSTANCE_VERSION,
            {"reuse_window": settings.reuse_window},
        )
