"""Persisted, cross-session UI state (window chrome preferences).

Currently just the menu-bar visibility, which is hidden by default and toggled
from the command palette. Stored as JSON next to the recent-files store.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import SettingsRecordStore
from app.storage.backend import StorageBackend

UI_STATE_VERSION = 1
UI_STATE_KEY = "ui_state"


@dataclass(frozen=True)
class UiState:
    """Remembered window-chrome preferences."""

    menu_visible: bool = False
    toolbar_visible: bool = False
    statusbar_visible: bool = True


class UiStateStore(SettingsRecordStore[UiState]):
    """Reads and writes :class:`UiState` via the storage backend."""

    LABEL = "Window chrome preferences"
    VERSION = UI_STATE_VERSION

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, UI_STATE_KEY, UiState())
