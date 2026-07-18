"""Persisted, cross-session reload-on-changes preference.

Whether the viewer should watch every opened document for on-disk changes and
reload it automatically (:mod:`app.gui.reload_controller`). Uses the same
versioned-dict pattern as :mod:`app.config.instance_settings`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

RELOAD_VERSION = 1
RELOAD_KEY = "reload"


@dataclass(frozen=True)
class ReloadSettings:
    """Remembered reload preference (default: no automatic reload)."""

    watch_by_default: bool = False


class ReloadSettingsStore(RecordStore):
    """Reads and writes :class:`ReloadSettings` via the storage backend."""

    LABEL = "Reload on file changes"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, RELOAD_KEY)

    def load(self) -> ReloadSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, RELOAD_VERSION)
        if raw is None:
            return ReloadSettings()
        default = ReloadSettings()
        return ReloadSettings(
            watch_by_default=bool(raw.get("watch_by_default", default.watch_by_default)),
        )

    def save(self, settings: ReloadSettings) -> None:
        self._backend.set_versioned(self._key, RELOAD_VERSION, asdict(settings))
