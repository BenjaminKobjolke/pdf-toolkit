"""Common base for the app's custom dialogs: adopt the shared palette chrome.

Every small dialog inherits font size, opacity, and frameless chrome from the
command-palette appearance (:mod:`app.gui.dialog_appearance`) so the whole app looks
consistent and honours the user's palette font setting.

The chrome is applied in :meth:`exec` — before the native window is created — rather
than in ``showEvent``: toggling ``FramelessWindowHint`` on an already-shown window
makes Qt re-create it (visible flicker), so we set it up front. ``setFont`` cascades
to the child widgets the subclass built in ``__init__``.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog

from app.gui import dialog_appearance


class BaseDialog(QDialog):
    """A ``QDialog`` that adopts the active palette chrome when run modally."""

    def apply_active_chrome(self) -> None:
        """Apply the currently-registered shared palette chrome to this dialog."""
        dialog_appearance.apply_chrome(self, dialog_appearance.active())

    def exec(self) -> int:
        """Adopt the shared chrome, then run the dialog modally."""
        self.apply_active_chrome()
        return super().exec()
