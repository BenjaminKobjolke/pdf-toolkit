"""The live, shared appearance of the selected-item outline.

A single :class:`OutlineStyle` holder is created at startup and registered as the
module ``active()`` instance. Scene items (:class:`~app.gui.text_item.TextFieldItem`,
:class:`~app.gui.image_item.ImageItem`) read it at paint time to draw their own
selection rectangle, and the :class:`~app.gui.outline_controller.OutlineController`
mutates it when the user changes a setting — so a repaint, not a rebuild, applies
the new look. Pure view: no persistence here.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from app.config.outline_settings import OutlineLineStyle, OutlineSettings

_PEN_STYLES: dict[OutlineLineStyle, Qt.PenStyle] = {
    OutlineLineStyle.SOLID: Qt.PenStyle.SolidLine,
    OutlineLineStyle.DASHED: Qt.PenStyle.DashLine,
}


class OutlineStyle:
    """Holds the current :class:`OutlineSettings` and renders the outline."""

    def __init__(self, settings: OutlineSettings | None = None) -> None:
        self._settings = settings or OutlineSettings()

    def set(self, settings: OutlineSettings) -> None:
        self._settings = settings

    def settings(self) -> OutlineSettings:
        return self._settings

    def pen(self) -> QPen:
        """Build a cosmetic pen so the width stays constant under zoom."""
        pen = QPen(QColor(self._settings.color))
        pen.setWidthF(float(self._settings.width_px))
        pen.setStyle(_PEN_STYLES.get(self._settings.style, Qt.PenStyle.DashLine))
        pen.setCosmetic(True)
        return pen

    def draw(self, painter: QPainter, rect: QRectF) -> None:
        """Stroke ``rect`` with the current pen (no fill)."""
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)


_active = OutlineStyle()


def active() -> OutlineStyle:
    """Return the shared outline holder used by all scene items."""
    return _active


def set_active(holder: OutlineStyle) -> None:
    """Register ``holder`` as the shared instance returned by :func:`active`."""
    global _active
    _active = holder
