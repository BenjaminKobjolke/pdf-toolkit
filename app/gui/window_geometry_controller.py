"""Restore and persist the main window's position/size across runs.

Kept out of :class:`MainWindow` so the window stays a thin coordinator, mirroring
:class:`app.gui.chrome.ChromeController`. Fullscreen/maximized framing is ignored
on save — the underlying windowed rect is stored — so a session that ends in
fullscreen still reopens windowed at the right place.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow

from app.config.window_geometry import WindowGeometry, WindowGeometryStore

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 900
_MIN_VISIBLE = 80  # px of the window that must stay on a screen to count as visible


def _onscreen_rect(rect: QRect) -> QRect:
    """Return ``rect`` unchanged if enough of it sits on a connected screen;
    otherwise relocate it onto the primary screen. Handles a saved monitor that
    no longer exists (e.g. after a display change)."""
    screens = QGuiApplication.screens()
    if not screens:
        return rect
    for screen in screens:
        inter = screen.availableGeometry().intersected(rect)
        if inter.width() >= _MIN_VISIBLE and inter.height() >= _MIN_VISIBLE:
            return rect  # still reachable — leave intentional off-edge placement alone
    avail = (QGuiApplication.primaryScreen() or screens[0]).availableGeometry()
    width = min(rect.width(), avail.width())
    height = min(rect.height(), avail.height())
    x = min(max(rect.x(), avail.left()), avail.right() - width + 1)
    y = min(max(rect.y(), avail.top()), avail.bottom() - height + 1)
    return QRect(x, y, width, height)


class WindowGeometryController:
    """Owns restore-on-open and save-on-close for a window's geometry."""

    def __init__(self, window: QMainWindow, store: WindowGeometryStore) -> None:
        self._window = window
        self._store = store
        self._fullscreen_snapshot: QByteArray | None = None

    def enter_fullscreen(self) -> None:
        """Snapshot the windowed rect, then go fullscreen.

        Qt's implicit showNormal() restore is unreliable on Windows when the
        geometry was set programmatically, so we capture and restore it ourselves.
        """
        self._fullscreen_snapshot = self._window.saveGeometry()
        self._window.showFullScreen()

    def exit_fullscreen(self) -> None:
        """Leave fullscreen, restoring the rect captured by enter_fullscreen()."""
        self._window.showNormal()  # clear the fullscreen flag first
        if self._fullscreen_snapshot is not None:
            self._window.restoreGeometry(self._fullscreen_snapshot)

    def restore(self) -> None:
        """Apply the saved position/size, or fall back to the default size."""
        geom = self._store.load()
        if geom is None:
            self._window.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            return
        rect = _onscreen_rect(QRect(geom.x, geom.y, geom.width, geom.height))
        self._window.move(rect.x(), rect.y())
        self._window.resize(rect.width(), rect.height())

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
