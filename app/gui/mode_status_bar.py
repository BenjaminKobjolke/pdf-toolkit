"""A thin footer bar showing the viewer's current mode.

Presentation only: the window flips it via :meth:`set_edit_mode` from the same
``edit_mode_toggled`` signal that drives the controller and toolbar, so the label
always reflects the real mode without owning any state of its own.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.gui import strings


class ModeStatusBar(QWidget):
    """Footer label reading ``Regular Mode`` or ``Edit Text Mode``."""

    def __init__(self) -> None:
        super().__init__()
        self._label = QLabel()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(self._label)
        layout.addStretch(1)
        self.set_edit_mode(False)

    def set_edit_mode(self, on: bool) -> None:
        """Show the edit-text label when ``on``, otherwise the regular label."""
        self._label.setText(strings.MODE_EDIT_TEXT if on else strings.MODE_REGULAR)

    def mode_text(self) -> str:
        """Return the currently displayed mode label (used by tests)."""
        return self._label.text()
