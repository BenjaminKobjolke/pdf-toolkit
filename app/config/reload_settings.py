"""Persisted, cross-session reload-on-changes preference.

Whether the viewer should watch every opened document for on-disk changes and
reload it automatically (:mod:`app.gui.reload_controller`). Uses the same
versioned-dict pattern as :mod:`app.config.instance_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

RELOAD_VERSION = 1
RELOAD_KEY = "reload"


@dataclass(frozen=True)
class ReloadSettings:
    """Remembered reload preference (default: no automatic reload)."""

    watch_by_default: bool = False


class ReloadSettingsStore(SettingsRecordStore[ReloadSettings]):
    """Reads and writes :class:`ReloadSettings` via the storage backend."""

    LABEL = "Reload on file changes"
    VERSION = RELOAD_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, RELOAD_KEY, ReloadSettings())
