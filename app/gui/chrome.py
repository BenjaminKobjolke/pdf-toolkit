"""Window-chrome visibility (menu bar, button toolbars, status bar), persisted.

The menu bar and toolbars are hidden by default and the status bar shown; the
command palette (Ctrl+Shift+P) is the primary entry point. Toggles are
remembered via :class:`UiStateStore` and restored on the next launch.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMenuBar, QWidget

from app.config.ui_state import UiState, UiStateStore


class ChromeController:
    """Owns show/hide + persistence for the menu bar, toolbars, and status bar."""

    def __init__(
        self,
        menu_bar: QMenuBar,
        toolbar: QWidget,
        edit_bar: QWidget,
        status_bar: QWidget,
        store: UiStateStore,
    ) -> None:
        self._menu = menu_bar
        self._toolbar = toolbar
        self._edit_bar = edit_bar
        self._status_bar = status_bar
        self._store = store

    def apply_saved(self) -> None:
        """Set initial visibility from the stored state."""
        state = self._store.load()
        self._menu.setVisible(state.menu_visible)
        self._toolbar.setVisible(state.toolbar_visible)
        self._edit_bar.setVisible(state.toolbar_visible)
        self._status_bar.setVisible(state.statusbar_visible)

    def toggle_menu(self) -> None:
        # isHidden() reflects the explicit hide flag even before the window is
        # shown, unlike isVisible() which also tracks the parent's shown state.
        self._menu.setVisible(self._menu.isHidden())
        self.save()

    def toggle_toolbar(self) -> None:
        visible = self._toolbar.isHidden()
        self._toolbar.setVisible(visible)
        self._edit_bar.setVisible(visible)
        self.save()

    def toggle_statusbar(self) -> None:
        self._status_bar.setVisible(self._status_bar.isHidden())
        self.save()

    def save(self) -> None:
        self._store.save(self._current())

    def _current(self) -> UiState:
        return UiState(
            menu_visible=not self._menu.isHidden(),
            toolbar_visible=not self._toolbar.isHidden(),
            statusbar_visible=not self._status_bar.isHidden(),
        )
