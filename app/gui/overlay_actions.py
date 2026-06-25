"""Add-overlay entry points (text field / image), extracted from MainWindow.

Each ensures edit mode is on, then routes through the shared placement chooser:
text fields create directly via the edit controller; images first run the
file/copy prompt in :class:`ImageActions`. Keeping these here lets the window
stay a thin coordinator under the 300-line cap.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF

from app.gui import rect_style
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.image_actions import ImageActions
from app.gui.placement import PlacementController
from app.gui.rect_controller import RectController


class OverlayActions:
    """Ensure edit mode, then place a new text field, image, or rectangle."""

    def __init__(
        self,
        edit_bar: EditBar,
        controller: EditController,
        placement: PlacementController,
        image_actions: ImageActions,
        rects: RectController,
        has_doc: Callable[[], bool],
    ) -> None:
        self._edit_bar = edit_bar
        self._controller = controller
        self._placement = placement
        self._image_actions = image_actions
        self._rects = rects
        self._has_doc = has_doc

    def add_text_field(self) -> None:
        if not self._has_doc():
            return
        self._ensure_edit_mode()

        def create(anchor: QPointF | None, centered: bool) -> None:
            self._controller.add_field(anchor, centered=centered)

        self._placement.choose_and_place(create)

    def add_image(self) -> None:
        if not self._has_doc():
            return
        self._ensure_edit_mode()
        self._image_actions.add()

    def add_rect(self) -> None:
        if not self._has_doc():
            return
        self._ensure_edit_mode()
        width, height = rect_style.DEFAULT_SIZE

        def create(anchor: QPointF | None, centered: bool) -> None:
            self._rects.add_rect(width, height, rect_style.DEFAULT_FILL, anchor, centered=centered)

        self._placement.choose_and_place(create)

    def ensure_edit_mode(self) -> None:
        """Turn edit mode on if it is not already (public for selection commands)."""
        self._ensure_edit_mode()

    def _ensure_edit_mode(self) -> None:
        if not self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()  # syncs toolbar + controllers + footer
