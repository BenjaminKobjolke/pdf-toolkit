"""The text-editing toolbar: emit-only widgets for the edit controller.

Holds no logic beyond translating widget state into a :class:`TextStyle` and
firing signals; the window wires it to the :class:`EditController`.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from app.gui import strings, text_style
from app.gui.text_style import TextStyle

_MIN_SIZE = 4.0
_MAX_SIZE = 400.0


class EditBar(QWidget):
    """Edit-mode toggle plus font/size/colour controls and add/export actions."""

    edit_mode_toggled = Signal(bool)
    add_field_requested = Signal()
    delete_field_requested = Signal()
    export_text_requested = Signal()
    style_changed = Signal(object)  # TextStyle

    def __init__(self) -> None:
        super().__init__()
        self._text_color = text_style.DEFAULT_STYLE.color
        self._bg_color: str | None = text_style.DEFAULT_STYLE.bg_color

        self._toggle = QPushButton(strings.BTN_EDIT_MODE)
        self._toggle.setCheckable(True)
        self._toggle.toggled.connect(self._on_toggle)

        self._add = QPushButton(strings.BTN_ADD_FIELD)
        self._add.clicked.connect(self.add_field_requested.emit)

        self._delete = QPushButton(strings.BTN_DELETE_FIELD)
        self._delete.clicked.connect(self.delete_field_requested.emit)

        self._font = QFontComboBox()
        self._font.currentFontChanged.connect(self._emit_style)

        self._size = QDoubleSpinBox()
        self._size.setRange(_MIN_SIZE, _MAX_SIZE)
        self._size.setValue(text_style.DEFAULT_STYLE.font_size)
        self._size.valueChanged.connect(self._emit_style)

        self._bold = QPushButton(strings.BTN_BOLD)
        self._bold.setCheckable(True)
        self._bold.toggled.connect(self._emit_style)
        self._italic = QPushButton(strings.BTN_ITALIC)
        self._italic.setCheckable(True)
        self._italic.toggled.connect(self._emit_style)

        self._text_color_btn = QPushButton(strings.BTN_TEXT_COLOR)
        self._text_color_btn.clicked.connect(self._pick_text_color)
        self._bg_btn = QPushButton(strings.BTN_BG_COLOR)
        self._bg_btn.setCheckable(True)
        self._bg_btn.toggled.connect(self._on_bg_toggle)

        self._export = QPushButton(strings.BTN_EXPORT_TEXT)
        self._export.clicked.connect(self.export_text_requested.emit)

        self._edit_widgets: list[QWidget] = [
            self._add,
            self._delete,
            QLabel(strings.LABEL_FONT),
            self._font,
            QLabel(strings.LABEL_SIZE),
            self._size,
            self._bold,
            self._italic,
            self._text_color_btn,
            self._bg_btn,
            self._export,
        ]

        layout = QHBoxLayout(self)
        layout.addWidget(self._toggle)
        for widget in self._edit_widgets:
            layout.addWidget(widget)
        layout.addStretch(1)

        self.set_edit_widgets_visible(False)

    def set_edit_widgets_visible(self, visible: bool) -> None:
        for widget in self._edit_widgets:
            widget.setVisible(visible)

    def toggle_edit_mode(self) -> None:
        """Flip the edit-mode button (emits ``edit_mode_toggled`` via its handler)."""
        self._toggle.toggle()

    def is_edit_mode(self) -> bool:
        return self._toggle.isChecked()

    def current_style(self) -> TextStyle:
        return TextStyle(
            font_family=self._font.currentFont().family(),
            font_size=self._size.value(),
            color=self._text_color,
            bg_color=self._bg_color,
            bold=self._bold.isChecked(),
            italic=self._italic.isChecked(),
        )

    # --- handlers -----------------------------------------------------------

    def _on_toggle(self, checked: bool) -> None:
        self.set_edit_widgets_visible(checked)
        self.edit_mode_toggled.emit(checked)

    def _emit_style(self, *_args: object) -> None:
        self.style_changed.emit(self.current_style())

    def _pick_text_color(self) -> None:
        color = QColorDialog.getColor(
            QColor(self._text_color), self, strings.DIALOG_TEXT_COLOR_TITLE
        )
        if color.isValid():
            self._text_color = text_style.color_to_hex(color)
            self._emit_style()

    def _on_bg_toggle(self, checked: bool) -> None:
        if not checked:
            self._bg_color = None
            self._emit_style()
            return
        color = QColorDialog.getColor(QColor("#ffffff"), self, strings.DIALOG_BG_COLOR_TITLE)
        if color.isValid():
            self._bg_color = text_style.color_to_hex(color)
            self._emit_style()
        else:
            self._bg_btn.setChecked(False)
