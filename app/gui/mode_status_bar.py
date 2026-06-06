"""A thin footer bar showing the viewer's current mode.

Presentation only: the window flips it via :meth:`set_edit_mode` from the same
``edit_mode_toggled`` signal that drives the controller and toolbar, so the label
always reflects the real mode without owning any state of its own.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.gui import strings


class ModeStatusBar(QWidget):
    """Footer: mode label on the left, current/total page centred."""

    def __init__(self) -> None:
        super().__init__()
        self._label = QLabel()
        self._page_label = QLabel()
        self._dirty_label = QLabel()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(self._label)
        layout.addStretch(1)
        layout.addWidget(self._page_label)
        layout.addStretch(1)
        layout.addWidget(self._dirty_label)
        self.set_edit_mode(False)
        self.set_dirty(False)

    def set_edit_mode(self, on: bool) -> None:
        """Show the edit-text label when ``on``, otherwise the regular label."""
        self._label.setText(strings.MODE_EDIT if on else strings.MODE_REGULAR)

    def set_hint(self, text: str) -> None:
        """Show a transient hint in place of the mode label (e.g. while placing)."""
        self._label.setText(text)

    def clear_hint(self) -> None:
        """Restore the mode label after a transient hint, reading the toggle state."""
        self.set_edit_mode(True)

    def set_page_label(self, current: int, total: int) -> None:
        """Show ``current/total`` in the centre (e.g. ``5/7``)."""
        self._page_label.setText(strings.PAGE_OF_FMT.format(current=current, total=total))

    def clear_page_label(self) -> None:
        """Blank the page indicator (no document open)."""
        self._page_label.setText("")

    def set_dirty(self, on: bool) -> None:
        """Show the unsaved-changes marker when ``on``, otherwise blank it."""
        self._dirty_label.setText(strings.MODIFIED_MARKER if on else "")

    def dirty_text(self) -> str:
        """Return the currently displayed dirty marker (used by tests)."""
        return self._dirty_label.text()

    def mode_text(self) -> str:
        """Return the currently displayed mode label (used by tests)."""
        return self._label.text()

    def page_text(self) -> str:
        """Return the currently displayed page indicator (used by tests)."""
        return self._page_label.text()
