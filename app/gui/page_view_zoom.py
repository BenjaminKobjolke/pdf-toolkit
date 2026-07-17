"""Zoom delegation for :class:`~app.gui.page_view.PageView`.

A mixin with the thin wrappers around :class:`ZoomController`. Split out so
``page_view`` stays under the file-length cap; the controller itself is created
in ``PageView.__init__``.
"""

from __future__ import annotations

from app.config.zoom_settings import ZoomSettings
from app.gui.page_navigator import PageNavigator
from app.gui.zoom_controller import ZoomController


class ZoomDelegateMixin:
    """Zoom queries and actions delegated to the zoom controller."""

    _zoom_ctl: ZoomController
    _nav: PageNavigator

    def zoom(self) -> float:
        """Return the current scene-to-view scale factor."""
        return self._zoom_ctl.zoom()

    def current_zoom(self) -> ZoomSettings:
        """Return the current zoom as a remembered default (fit vs. percentage)."""
        return self._zoom_ctl.current_default()

    def zoom_actual(self) -> None:
        self._zoom_ctl.actual()

    def zoom_in(self) -> None:
        self._zoom_ctl.zoom_in()

    def zoom_out(self) -> None:
        self._zoom_ctl.zoom_out()

    def zoom_fit(self) -> None:
        if self._nav.source() is not None:
            self._zoom_ctl.fit()

    def set_default_zoom(self, fit: bool, percent: int) -> None:
        """Set the start zoom mode; apply it now if a document is already open."""
        self._zoom_ctl.set_default(fit, percent)
        if self._nav.source() is not None:
            self._zoom_ctl.reapply()
