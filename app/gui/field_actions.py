"""Keyboard-first editing of the currently selected text field.

Each method prompts with a keyboard-navigable dialog and applies the change
through the :class:`EditController`, reusing the existing style bridge. Colour
uses the custom :class:`ColorPickerDialog`; a small most-recently-used list is
kept so the last colours are one keystroke away.
"""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QInputDialog, QWidget

from app.gui import strings
from app.gui.color_picker_dialog import ColorPickerDialog
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.page_view import PageView
from app.gui.text_input_dialog import TextInputDialog

_MAX_RECENT_COLORS = 8
_MIN_FONT_SIZE = 4.0
_MAX_FONT_SIZE = 400.0


class FieldActions:
    """Active-field commands. Enabled only while a field is selected."""

    def __init__(self, parent: QWidget, page_view: PageView, controller: EditController) -> None:
        self._parent = parent
        self._page_view = page_view
        self._controller = controller
        self._recent_colors: list[str] = []

    def change_text(self) -> None:
        item = self._page_view.selected_text_item()
        if item is None:
            return
        dialog = TextInputDialog(initial=item.toPlainText(), parent=self._parent)
        if dialog.exec():
            self._controller.set_selected_text(dialog.text())

    def change_size(self) -> None:
        style = self._controller.selected_style()
        if style is None:
            return
        size, ok = QInputDialog.getDouble(
            self._parent,
            strings.DIALOG_FIELD_SIZE_TITLE,
            strings.PROMPT_FIELD_SIZE,
            style.font_size,
            1,
            400,
        )
        if ok:
            self._controller.apply_style(replace(style, font_size=size))

    def scale_font(self, factor: float) -> None:
        """Multiply the selected field's font size by ``factor`` (clamped). For Ctrl+↑/↓."""
        style = self._controller.selected_style()
        if style is None:
            return
        size = max(_MIN_FONT_SIZE, min(_MAX_FONT_SIZE, style.font_size * factor))
        self._controller.apply_style(replace(style, font_size=size))

    def change_font(self) -> None:
        style = self._controller.selected_style()
        if style is None:
            return
        entries = [ListEntry(title=family, payload=family) for family in QFontDatabase.families()]
        dialog = FilterListDialog(
            entries,
            placeholder=strings.FONT_PLACEHOLDER,
            title=strings.FONT_DIALOG_TITLE,
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._controller.apply_style(replace(style, font_family=chosen.payload))

    def change_text_color(self) -> None:
        style = self._controller.selected_style()
        if style is None:
            return
        picked = self._pick_color()
        if picked is not None:
            self._controller.apply_style(replace(style, color=picked))

    def change_bg_color(self) -> None:
        style = self._controller.selected_style()
        if style is None:
            return
        picked = self._pick_color(allow_transparent=True)
        if picked is None:
            return  # cancelled
        bg = None if picked == ColorPickerDialog.TRANSPARENT else picked
        self._controller.apply_style(replace(style, bg_color=bg))

    def toggle_bold(self) -> None:
        style = self._controller.selected_style()
        if style is not None:
            self._controller.apply_style(replace(style, bold=not style.bold))

    def toggle_italic(self) -> None:
        style = self._controller.selected_style()
        if style is not None:
            self._controller.apply_style(replace(style, italic=not style.italic))

    def delete(self) -> None:
        self._controller.delete_selected()

    def _pick_color(self, *, allow_transparent: bool = False) -> str | None:
        dialog = ColorPickerDialog(
            recent=self._recent_colors, allow_transparent=allow_transparent, parent=self._parent
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            if chosen != ColorPickerDialog.TRANSPARENT:
                self._remember_color(chosen)  # only real colours are recent-listed
            return chosen
        return None

    def _remember_color(self, hex_value: str) -> None:
        if hex_value in self._recent_colors:
            self._recent_colors.remove(hex_value)
        self._recent_colors.insert(0, hex_value)
        del self._recent_colors[_MAX_RECENT_COLORS:]
