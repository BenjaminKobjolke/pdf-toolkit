"""Persisted, cross-session UI state (window chrome preferences).

Currently just the menu-bar visibility, which is hidden by default and toggled
from the command palette. Stored as JSON next to the recent-files store.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.io.json_store import read_versioned_dict, write_versioned

UI_STATE_VERSION = 1


@dataclass(frozen=True)
class UiState:
    """Remembered window-chrome preferences."""

    menu_visible: bool = False
    toolbar_visible: bool = False


class UiStateStore:
    """Reads and writes :class:`UiState` at a fixed JSON path."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> UiState:
        """Return the stored state, or defaults if absent/corrupt."""
        raw = read_versioned_dict(self._path, UI_STATE_VERSION)
        if raw is None:
            return UiState()
        return UiState(
            menu_visible=bool(raw.get("menu_visible", False)),
            toolbar_visible=bool(raw.get("toolbar_visible", False)),
        )

    def save(self, state: UiState) -> None:
        write_versioned(
            self._path,
            UI_STATE_VERSION,
            {"menu_visible": state.menu_visible, "toolbar_visible": state.toolbar_visible},
        )
