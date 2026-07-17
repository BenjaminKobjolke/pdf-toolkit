"""Shared base for the keyboard-first filter dialogs.

Owns the common chrome and interaction — a filter line edit above a list, with
Up/Down to move the selection, Enter to accept, Esc to cancel. Subclasses supply
the rows (``_apply_filter``) and what acceptance returns (``accept_current``);
the color picker also slots a preview swatch between the two widgets.
"""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QListWidget, QVBoxLayout, QWidget

from app.gui import dialog_appearance
from app.gui.base_dialog import BaseDialog


class FilterableListDialog(BaseDialog):
    """Filter box + list with shared Up/Down/Enter/Esc navigation."""

    def __init__(
        self,
        *,
        placeholder: str = "",
        title: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if title:
            self.setWindowTitle(title)
        self._filter = QLineEdit()
        self._filter.setPlaceholderText(placeholder)
        self._filter.textChanged.connect(self._apply_filter)
        self._filter.returnPressed.connect(self.accept_current)
        self._filter.installEventFilter(self)

        self._list = QListWidget()
        self._list.itemActivated.connect(lambda _item: self.accept_current())
        self._list.currentRowChanged.connect(lambda _row: self._on_row_changed())

    def _finish_layout(self, *middle: QWidget, size: tuple[int, int] = (520, 420)) -> None:
        """Lay out filter, any ``middle`` widgets, then the list; show initial rows.

        Parented dialogs size to the user's dialog-size % of the window;
        ``size`` is the fixed fallback when there is no parent.
        """
        layout = QVBoxLayout(self)
        layout.addWidget(self._filter)
        for widget in middle:
            layout.addWidget(widget)
        layout.addWidget(self._list)
        dialog_appearance.resize_for_parent(self, size)
        self._apply_filter("")
        self._filter.setFocus()

    # --- shared interaction -------------------------------------------------

    def set_query(self, text: str) -> None:
        self._filter.setText(text)

    def move_selection(self, delta: int) -> None:
        """Move the highlight by ``delta`` rows, wrapping at the ends."""
        count = self._list.count()
        if count == 0:
            return
        row = (self._list.currentRow() + delta) % count
        self._list.setCurrentRow(row)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Route Up/Down from the filter box to the list selection."""
        if watched is self._filter and event.type() == QEvent.Type.KeyPress:
            key = cast(QKeyEvent, event).key()
            if key == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            if key == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
            if key == Qt.Key.Key_Delete and self._on_delete_key():
                return True
        return super().eventFilter(watched, event)

    # --- hooks subclasses implement / override ------------------------------

    def _on_delete_key(self) -> bool:
        """Handle a Del keypress in the filter box (default: not handled)."""
        return False

    def _on_row_changed(self) -> None:
        """Called when the highlighted row changes (default: nothing)."""

    def _apply_filter(self, text: str) -> None:
        raise NotImplementedError

    def accept_current(self) -> None:
        raise NotImplementedError
