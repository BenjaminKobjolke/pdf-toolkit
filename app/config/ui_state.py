"""Persisted, cross-session UI state (window chrome preferences).

Currently just the menu-bar visibility, which is hidden by default and toggled
from the command palette. Stored as JSON next to the recent-files store.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

UI_STATE_VERSION = 1
UI_STATE_KEY = "ui_state"


@dataclass(frozen=True)
class UiState:
    """Remembered window-chrome preferences."""

    menu_visible: bool = False
    toolbar_visible: bool = False
    statusbar_visible: bool = True


class UiStateStore(RecordStore):
    """Reads and writes :class:`UiState` via the storage backend."""

    LABEL = "Window chrome preferences"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, UI_STATE_KEY)

    def load(self) -> UiState:
        """Return the stored state, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, UI_STATE_VERSION)
        if raw is None:
            return UiState()
        return UiState(
            menu_visible=bool(raw.get("menu_visible", False)),
            toolbar_visible=bool(raw.get("toolbar_visible", False)),
            statusbar_visible=bool(raw.get("statusbar_visible", True)),
        )

    def save(self, state: UiState) -> None:
        self._backend.set_versioned(
            self._key,
            UI_STATE_VERSION,
            {
                "menu_visible": state.menu_visible,
                "toolbar_visible": state.toolbar_visible,
                "statusbar_visible": state.statusbar_visible,
            },
        )
