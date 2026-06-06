"""Restore and persist the main window's position/size across runs.

Kept out of :class:`MainWindow` so the window stays a thin coordinator, mirroring
:class:`app.gui.chrome.ChromeController`. Fullscreen/maximized framing is ignored
on save — the underlying windowed rect is stored — so a session that ends in
fullscreen still reopens windowed at the right place.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from app.config.window_geometry import WindowGeometry, WindowGeometryStore

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 900


class WindowGeometryController:
    """Owns restore-on-open and save-on-close for a window's geometry."""

    def __init__(self, window: QMainWindow, store: WindowGeometryStore) -> None:
        self._window = window
        self._store = store

    def restore(self) -> None:
        """Apply the saved position/size, or fall back to the default size."""
        geom = self._store.load()
        if geom is None:
            self._window.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            return
        self._window.move(geom.x, geom.y)
        self._window.resize(geom.width, geom.height)

    def save(self) -> None:
        """Persist the windowed rect (ignoring fullscreen/maximized framing)."""
        # normalGeometry() is the non-maximized/non-fullscreen rect; it can be
        # empty before the window is ever shown — fall back to the live geometry.
        rect = self._window.normalGeometry()
        if rect.isEmpty():
            rect = self._window.geometry()
        self._store.save(
            WindowGeometry(x=rect.x(), y=rect.y(), width=rect.width(), height=rect.height())
        )
