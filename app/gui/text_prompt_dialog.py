"""Keyboard-first single-line text prompt built on :class:`FormDialog`.

Drop-in replacement for ``QInputDialog.getText`` that adopts the shared palette
chrome. Returns the trimmed text, or ``None`` when cancelled or left empty.
``select_all=False`` puts the caret at the end instead of selecting (used by the
export-name prompt, which pre-fills the current file name).
"""

from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QWidget

from app.gui.form_dialog import FormDialog, exec_value


class TextPromptDialog(FormDialog):
    """A label plus a single-line text field with an OK/Cancel row."""

    def __init__(
        self,
        *,
        title: str,
        label: str,
        text: str = "",
        select_all: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title=title, message=label, parent=parent)
        self._edit = QLineEdit(text)
        self.add_content(self._edit)
        self.add_ok_cancel()
        self._edit.setFocus()
        if select_all:
            self._edit.selectAll()
        else:
            self._edit.end(False)

    def value(self) -> str:
        return self._edit.text()


def prompt_text(
    parent: QWidget | None,
    title: str,
    label: str,
    text: str = "",
    *,
    select_all: bool = True,
) -> str | None:
    """Prompt for one line of text; return it trimmed, or ``None`` if empty/cancelled."""
    dialog = TextPromptDialog(
        title=title, label=label, text=text, select_all=select_all, parent=parent
    )
    result = exec_value(dialog, dialog.value)
    if result is None:
        return None
    trimmed = result.strip()
    return trimmed or None
