"""Keyboard-first editing of the currently selected rectangle: fill, size, delete.

Mirrors :class:`~app.gui.field_actions.FieldActions`: each method prompts with a
keyboard-navigable dialog and applies the change through the
:class:`~app.gui.rect_controller.RectController`.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from app.gui import number_input_dialog, overlay_strings
from app.gui.color_picker_dialog import ColorPickerDialog
from app.gui.page_view import PageView
from app.gui.rect_controller import RectController

_MIN_DIM = 1.0
_MAX_DIM = 4000.0


class RectActions:
    """Active-rectangle commands. Enabled only while a rectangle is selected."""

    def __init__(self, parent: QWidget, page_view: PageView, rects: RectController) -> None:
        self._parent = parent
        self._page_view = page_view
        self._rects = rects
        self._recent_colors: list[str] = []

    def change_fill_color(self) -> None:
        item = self._page_view.selected_rect_item()
        if item is None:
            return
        dialog = ColorPickerDialog(recent=self._recent_colors, parent=self._parent)
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._remember_color(chosen)
            item.set_fill_color(QColor(chosen))
            self._rects.notify_changed()

    def change_width(self) -> None:
        item = self._page_view.selected_rect_item()
        if item is None:
            return
        value = number_input_dialog.prompt_float(
            self._parent,
            overlay_strings.DIALOG_RECT_WIDTH_TITLE,
            overlay_strings.PROMPT_RECT_WIDTH,
            item.current_width(),
            _MIN_DIM,
            _MAX_DIM,
        )
        if value is not None:
            self._rects.set_selected_size(value, item.current_height())

    def change_height(self) -> None:
        item = self._page_view.selected_rect_item()
        if item is None:
            return
        value = number_input_dialog.prompt_float(
            self._parent,
            overlay_strings.DIALOG_RECT_HEIGHT_TITLE,
            overlay_strings.PROMPT_RECT_HEIGHT,
            item.current_height(),
            _MIN_DIM,
            _MAX_DIM,
        )
        if value is not None:
            self._rects.set_selected_size(item.current_width(), value)

    def delete(self) -> None:
        self._rects.delete_selected()

    def _remember_color(self, hex_value: str) -> None:
        if hex_value in self._recent_colors:
            self._recent_colors.remove(hex_value)
        self._recent_colors.insert(0, hex_value)
        del self._recent_colors[8:]
