"""A multi-line text editor dialog accepted with Ctrl+Enter.

``QInputDialog.getMultiLineText`` treats Enter as a newline and only submits via
the OK button, which is awkward for keyboard use. This dialog keeps Enter for
newlines but commits on **Ctrl+Enter** (and Ctrl+Return), Esc to cancel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui import strings


class TextInputDialog(QDialog):
    """Edit multi-line text; submit with Ctrl+Enter."""

    def __init__(
        self,
        *,
        initial: str = "",
        title: str = "",
        label: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or strings.DIALOG_FIELD_TEXT_TITLE)

        self._edit = QPlainTextEdit()
        self._edit.setPlainText(initial)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label or strings.PROMPT_FIELD_TEXT))
        layout.addWidget(self._edit)
        layout.addWidget(QLabel(strings.HINT_CTRL_ENTER))
        layout.addWidget(buttons)
        self.resize(420, 260)

        for sequence in (Qt.Modifier.CTRL | Qt.Key.Key_Return, Qt.Modifier.CTRL | Qt.Key.Key_Enter):
            QShortcut(QKeySequence(sequence), self, self.submit)

        self._edit.setFocus()

    def text(self) -> str:
        return self._edit.toPlainText()

    def set_text(self, value: str) -> None:
        self._edit.setPlainText(value)

    def submit(self) -> None:
        """Accept the dialog (what Ctrl+Enter / OK trigger)."""
        self.accept()
