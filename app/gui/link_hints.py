"""Link-hint overlays: a box plus a vim-style letter label per link.

Mirrors :class:`PageHighlights`. Link coordinates arrive in PDF points and are
scaled to render-time scene pixels by ``render.DEFAULT_ZOOM`` — the same mapping
every other overlay uses. Drawn above the select-mode cursor (z=4). Colors and
font size are read from the shared :class:`LinkHintStyle` holder on every redraw.
"""

from __future__ import annotations

from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from app.config.link_hint_settings import LinkHintSettings
from app.gui import render
from app.gui.link_hint_style import LinkHintStyle
from app.pdf.links import LinkBox

_HINT_Z = 5.0  # above page (0), overlays (1), search (2), select span (3)/cursor (4)


class LinkHints:
    """Draws and clears the link boxes and their letter labels on a scene."""

    def __init__(self, scene: QGraphicsScene, style: LinkHintStyle) -> None:
        self._scene = scene
        self._style = style
        self._items: list[QGraphicsItem] = []

    def set(self, pairs: list[tuple[LinkBox, str]]) -> None:
        """Draw a box + ``label`` chip for each (link, label) pair (PDF points)."""
        self.clear()
        settings = self._style.settings()
        z = render.DEFAULT_ZOOM
        pen = QPen(QColor(settings.box_color))
        pen.setWidth(2)
        for link, label in pairs:
            box = self._scene.addRect(
                link.x0 * z, link.y0 * z, (link.x1 - link.x0) * z, (link.y1 - link.y0) * z, pen
            )
            box.setZValue(_HINT_Z)
            self._items.append(box)
            self._add_label(link.x0 * z, link.y0 * z, label, settings)

    def _add_label(self, x: float, y: float, label: str, settings: LinkHintSettings) -> None:
        font = QFont()
        font.setPointSize(settings.font_pt)
        font.setBold(True)
        text = self._scene.addSimpleText(label, font)
        text.setBrush(QBrush(QColor(settings.text_color)))
        text.setPos(x, y)
        text.setZValue(_HINT_Z + 0.1)
        bounds = text.boundingRect()
        chip_color = QColor(settings.background_color)
        chip = self._scene.addRect(
            x, y, bounds.width(), bounds.height(), QPen(chip_color), QBrush(chip_color)
        )
        chip.setZValue(_HINT_Z)
        self._items.extend([chip, text])

    def clear(self) -> None:
        for item in self._items:
            self._scene.removeItem(item)
        self._items.clear()
