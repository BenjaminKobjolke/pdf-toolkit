"""Rotate or flip the current page (deferred to the working copy).

The working copy keeps the original filename, so the lambda dispatches on
``FileFormat.of`` at run time: image documents transform their pixels, PDFs
their current page. Other formats are unreachable — the commands are gated
to ``TRANSFORMABLE`` in the registry.
"""

from __future__ import annotations

from app.gui.deferred_ops import DeferredOps
from app.pdf.file_format import IMAGE_FORMATS, FileFormat
from app.pdf.flipper import flip_page
from app.pdf.image_transform import flip_image, rotate_image
from app.pdf.rotator import ROTATE_FLIP, ROTATE_LEFT, ROTATE_RIGHT, rotate_page


class RotateActions:
    """Rotate/flip-current-page commands bound to the open document."""

    def __init__(self, deferred: DeferredOps) -> None:
        self._deferred = deferred
        self._page_view = deferred.page_view

    def rotate_left(self) -> None:
        self._rotate(ROTATE_LEFT)

    def rotate_right(self) -> None:
        self._rotate(ROTATE_RIGHT)

    def rotate_180(self) -> None:
        self._rotate(ROTATE_FLIP)

    def flip_horizontal(self) -> None:
        self._flip(horizontal=True)

    def flip_vertical(self) -> None:
        self._flip(horizontal=False)

    def _rotate(self, degrees: int) -> None:
        if self._deferred.working() is None:
            return
        page = self._page_view.current_page_one_based()
        self._deferred.run(
            lambda p: (
                rotate_image(p, degrees)
                if FileFormat.of(p) in IMAGE_FORMATS
                else rotate_page(p, page, degrees)
            )
        )

    def _flip(self, *, horizontal: bool) -> None:
        if self._deferred.working() is None:
            return
        page = self._page_view.current_page_one_based()
        self._deferred.run(
            lambda p: (
                flip_image(p, horizontal=horizontal)
                if FileFormat.of(p) in IMAGE_FORMATS
                else flip_page(p, page, horizontal=horizontal)
            )
        )
