"""Persisted, cross-session single-instance preference.

Whether launching the viewer with a file should reuse an already-running
window (forwarded over the local socket in :mod:`app.gui.single_instance`)
or start a fresh instance. Uses the same versioned-dict pattern as
:mod:`app.config.open_filter_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

INSTANCE_VERSION = 1
INSTANCE_KEY = "instance"


@dataclass(frozen=True)
class InstanceSettings:
    """Remembered single-instance preferences (default: reuse + focus the window)."""

    reuse_window: bool = True
    focus_on_forward: bool = True


class InstanceSettingsStore(SettingsRecordStore[InstanceSettings]):
    """Reads and writes :class:`InstanceSettings` via the storage backend."""

    LABEL = "Reuse existing window"
    VERSION = INSTANCE_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, INSTANCE_KEY, InstanceSettings())
