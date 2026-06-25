"""A movable, scalable image for the page scene.

Pure view object: it draws a pixmap (honouring PNG alpha and an opacity factor),
scales uniformly (aspect-ratio locked) via corner handles or an explicit factor,
and exposes its on-page size. It holds the source path metadata needed to persist
it, but no PDF or persistence logic.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem

from app.gui.image_resize import CORNERS, ResizeHandleItem, anchor_point, top_left_for
from app.gui.resizable_item import ResizableItemMixin

_MIN_SCALE = 0.05
_MAX_SCALE = 50.0


class ImageItem(ResizableItemMixin, QGraphicsPixmapItem):
    """Drag to move, drag a corner to scale; keeps its aspect ratio."""

    def __init__(
        self,
        pixmap: QPixmap,
        path_str: str,
        absolute: bool,
        opacity: float = 1.0,
        scale_factor: float = 1.0,
    ) -> None:
        super().__init__()
        self._base = pixmap
        self._path_str = path_str
        self._absolute = absolute
        self._opacity = opacity
        self._scale = 1.0
        self._editable = False
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setOpacity(opacity)
        self._handles = [ResizeHandleItem(self, corner) for corner in CORNERS]
        self.set_scale_factor(scale_factor)
        self._set_handles_visible(False)

    # --- metadata -----------------------------------------------------------

    def path_str(self) -> str:
        return self._path_str

    def is_absolute(self) -> bool:
        return self._absolute

    def opacity_value(self) -> float:
        return self._opacity

    # --- scale --------------------------------------------------------------

    def scale_factor(self) -> float:
        return self._scale

    def set_scale_factor(self, factor: float) -> None:
        """Scale the image uniformly to ``factor`` of its native size."""
        factor = max(_MIN_SCALE, min(_MAX_SCALE, factor))
        self._scale = factor
        width = max(1, round(self._base.width() * factor))
        height = max(1, round(self._base.height() * factor))
        self.setPixmap(
            self._base.scaled(
                width,
                height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._reposition_handles()

    def scale_about_center(self, factor: float) -> None:
        """Scale uniformly to ``factor`` while keeping the on-page center fixed.

        Used by the keyboard / palette scale paths so the image grows or shrinks
        in place instead of drifting toward the bottom-right (corner-drag uses
        its own opposite-corner anchor via :meth:`resize_from_handle`).
        """
        center = self.pos() + QPointF(self.current_width() / 2, self.current_height() / 2)
        self.set_scale_factor(factor)
        self.setPos(
            center.x() - self.current_width() / 2,
            center.y() - self.current_height() / 2,
        )

    def current_width(self) -> float:
        return float(self.pixmap().width())

    def current_height(self) -> float:
        return float(self.pixmap().height())

    def resize_from_handle(self, corner: str, scene_pt: Any) -> None:
        """Resize so the dragged ``corner`` follows ``scene_pt`` (aspect-locked)."""
        anchor = anchor_point(corner, self.pos(), self.current_width(), self.current_height())
        new_width = abs(scene_pt.x() - anchor.x())
        base_width = self._base.width() or 1
        factor = max(_MIN_SCALE, min(_MAX_SCALE, new_width / base_width))
        new_w = self._base.width() * factor
        new_h = self._base.height() * factor
        self.setPos(top_left_for(corner, anchor, new_w, new_h))
        self.set_scale_factor(factor)

    # --- internals (selection/handles come from ResizableItemMixin) ----------

    def _reposition_handles(self) -> None:
        width = self.current_width()
        height = self.current_height()
        positions = {
            "tl": (0.0, 0.0),
            "tr": (width, 0.0),
            "bl": (0.0, height),
            "br": (width, height),
        }
        for handle in self._handles:
            x, y = positions[handle.corner]
            handle.setPos(x, y)
