"""A movable, inline-editable text field for the page scene.

Pure view object: it knows how to draw itself (including an optional background
fill) and expose its font/colour state, but holds no PDF or persistence logic.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QStyle,
    QStyleOptionGraphicsItem,
    QWidget,
)

from app.gui import outline_style, strings
from app.gui.gui_items import set_item_editable


class TextFieldItem(QGraphicsTextItem):
    """Drag to move, double-click to edit; paints an optional background."""

    def __init__(self, text: str = strings.EDIT_DEFAULT_TEXT) -> None:
        super().__init__(text)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.document().setDocumentMargin(0)
        self._bg_color: QColor | None = None

    def set_editable(self, on: bool) -> None:
        """Toggle move/select/edit interaction; fields stay visible either way."""
        set_item_editable(self, on)
        if not on:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    # --- style setters/getters ---------------------------------------------

    def set_font_family(self, family: str) -> None:
        font = self.font()
        font.setFamily(family)
        self.setFont(font)

    def set_font_pixel_size(self, size_px: float) -> None:
        font = self.font()
        font.setPixelSize(max(1, round(size_px)))
        self.setFont(font)

    def font_pixel_size(self) -> float:
        size = self.font().pixelSize()
        return float(size) if size > 0 else float(self.font().pointSize())

    def set_text_color(self, color: QColor) -> None:
        self.setDefaultTextColor(color)

    def text_color(self) -> QColor:
        return self.defaultTextColor()

    def set_bg_color(self, color: QColor | None) -> None:
        self._bg_color = color
        self.update()

    def bg_color(self) -> QColor | None:
        return self._bg_color

    def set_bold(self, on: bool) -> None:
        font = self.font()
        font.setBold(on)
        self.setFont(font)

    def set_italic(self, on: bool) -> None:
        font = self.font()
        font.setItalic(on)
        self.setFont(font)

    def is_bold(self) -> bool:
        return self.font().bold()

    def is_italic(self) -> bool:
        return self.font().italic()

    def font_family(self) -> str:
        return self.font().family()

    # --- interaction --------------------------------------------------------

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event: object) -> None:
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        super().focusOutEvent(event)  # type: ignore[arg-type]

    def paint(
        self,
        painter: object,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        if self._bg_color is not None:
            painter.fillRect(self.boundingRect(), self._bg_color)  # type: ignore[attr-defined]
        # Suppress Qt's faint default selection marquee and draw our own
        # configurable outline instead (see app.gui.outline_style).
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        option.state &= ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)  # type: ignore[arg-type]
        if selected:
            outline_style.active().draw(painter, self.boundingRect())  # type: ignore[arg-type]

    @staticmethod
    def default_font(family: str, size_px: float, bold: bool, italic: bool) -> QFont:
        font = QFont(family)
        font.setPixelSize(max(1, round(size_px)))
        font.setBold(bold)
        font.setItalic(italic)
        return font
