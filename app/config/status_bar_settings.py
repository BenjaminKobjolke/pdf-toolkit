"""Persisted, cross-session appearance for the footer status bar.

Currently just the font size of :class:`~app.gui.mode_status_bar.ModeStatusBar`
(``0`` = inherit the default font). Uses the same versioned-dict pattern as
:mod:`app.config.text_view_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

STATUS_BAR_SETTINGS_VERSION = 1
STATUS_BAR_KEY = "status_bar"

# Font-size bounds — single source of truth shared by the edit prompt and clamp.
FONT_PT_MIN, FONT_PT_MAX = 0, 40  # 0 = inherit the default font size


@dataclass(frozen=True)
class StatusBarSettings:
    """Remembered status-bar appearance preferences (defaults = built-ins)."""

    font_pt: int = 0


class StatusBarSettingsStore(SettingsRecordStore[StatusBarSettings]):
    """Reads and writes :class:`StatusBarSettings` via the storage backend."""

    LABEL = "Status bar appearance"
    VERSION = STATUS_BAR_SETTINGS_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, STATUS_BAR_KEY, StatusBarSettings())
