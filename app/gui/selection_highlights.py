"""Text-selection overlays for the page scene (vim-style select mode).

Owns the cursor outline (the current word) and the filled span (the visual
selection). Word coordinates arrive in PDF points and are scaled to render-time
scene pixels by ``render.DEFAULT_ZOOM`` — the same mapping :class:`PageHighlights`
uses for search matches.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene

from app.gui import render
from app.pdf.words import WordBox

_CURSOR_COLOR = "#1565c0"  # blue outline for the word the cursor is on
_SPAN_COLOR = QColor(21, 101, 192, 70)  # translucent blue fill for the selection
_SPAN_Z = 3.0  # above page (0), overlays (1) and search highlights (2)
_CURSOR_Z = 4.0  # above the span so the cursor stays visible inside a selection


class SelectionHighlights:
    """Draws and clears the select-mode cursor outline and selection fill."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._cursor_item: QGraphicsRectItem | None = None
        self._span_items: list[QGraphicsRectItem] = []

    def set_cursor(self, word: WordBox) -> None:
        """Outline the current word (in PDF points)."""
        self._clear_cursor()
        pen = QPen(QColor(_CURSOR_COLOR))
        pen.setWidth(2)
        self._cursor_item = self._add_rect(word, pen, QBrush(Qt.BrushStyle.NoBrush))
        self._cursor_item.setZValue(_CURSOR_Z)

    def set_span(self, words: Sequence[WordBox]) -> None:
        """Fill the selected span; an empty sequence clears the fill."""
        self._clear_span()
        brush = QBrush(_SPAN_COLOR)
        pen = QPen(Qt.PenStyle.NoPen)
        for word in words:
            item = self._add_rect(word, pen, brush)
            item.setZValue(_SPAN_Z)
            self._span_items.append(item)

    def clear(self) -> None:
        self._clear_cursor()
        self._clear_span()

    def _add_rect(self, word: WordBox, pen: QPen, brush: QBrush) -> QGraphicsRectItem:
        z = render.DEFAULT_ZOOM
        return self._scene.addRect(
            word.x0 * z,
            word.y0 * z,
            (word.x1 - word.x0) * z,
            (word.y1 - word.y0) * z,
            pen,
            brush,
        )

    def _clear_cursor(self) -> None:
        if self._cursor_item is not None:
            self._scene.removeItem(self._cursor_item)
            self._cursor_item = None

    def _clear_span(self) -> None:
        for item in self._span_items:
            self._scene.removeItem(item)
        self._span_items.clear()
