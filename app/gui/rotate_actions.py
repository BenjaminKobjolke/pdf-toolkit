"""Rotate the current page (deferred to the working copy)."""

from __future__ import annotations

from app.gui.deferred_ops import DeferredOps
from app.pdf.rotator import ROTATE_FLIP, ROTATE_LEFT, ROTATE_RIGHT, rotate_page


class RotateActions:
    """Rotate-current-page commands bound to the open document."""

    def __init__(self, deferred: DeferredOps) -> None:
        self._deferred = deferred
        self._page_view = deferred.page_view

    def rotate_left(self) -> None:
        self._rotate(ROTATE_LEFT)

    def rotate_right(self) -> None:
        self._rotate(ROTATE_RIGHT)

    def rotate_180(self) -> None:
        self._rotate(ROTATE_FLIP)

    def _rotate(self, degrees: int) -> None:
        if self._deferred.working() is None:
            return
        page = self._page_view.current_page_one_based()
        self._deferred.run(lambda p: rotate_page(p, page, degrees))
