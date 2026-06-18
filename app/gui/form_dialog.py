"""Shared skeleton for the small custom dialogs: message, content, button row.

Confirm/alert/number/text dialogs all stack the same way on top of
:class:`BaseDialog`: an optional word-wrapped message, an optional value-editing
widget, and a button row. Building it here — plus the run-and-return-or-``None``
helper :func:`exec_value` — keeps the layout and modal plumbing in one place
instead of in four near-identical files.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from PySide6.QtWidgets import QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from app.gui.base_dialog import BaseDialog

T = TypeVar("T")


class FormDialog(BaseDialog):
    """A dialog laid out as: message → optional content widget → button row."""

    def __init__(
        self, *, title: str = "", message: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        if title:
            self.setWindowTitle(title)
        self._layout = QVBoxLayout(self)
        if message:
            label = QLabel(message)
            label.setWordWrap(True)
            self._layout.addWidget(label)

    def add_content(self, widget: QWidget) -> None:
        """Insert the value-editing widget below the message."""
        self._layout.addWidget(widget)

    def add_buttons(self, box: QDialogButtonBox) -> None:
        """Add the button row at the bottom of the dialog."""
        self._layout.addWidget(box)

    def add_ok_cancel(self) -> QDialogButtonBox:
        """Add a standard OK/Cancel row wired to accept/reject; return it."""
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        self.add_buttons(box)
        return box


def exec_value(dialog: BaseDialog, reader: Callable[[], T]) -> T | None:
    """Run ``dialog`` modally; return ``reader()`` when accepted, else ``None``."""
    if dialog.exec():
        return reader()
    return None
