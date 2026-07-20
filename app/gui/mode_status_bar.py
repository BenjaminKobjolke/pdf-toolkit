"""A thin footer bar showing the viewer's current mode.

Presentation only: the window flips it via :meth:`set_edit_mode` from the same
``edit_mode_toggled`` signal that drives the controller and toolbar, so the label
always reflects the real mode without owning any state of its own.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.gui import strings

_FLASH_MS = 3000


class ModeStatusBar(QWidget):
    """Footer: mode label on the left, current/total page centred."""

    def __init__(self) -> None:
        super().__init__()
        self._label = QLabel()
        self._flash_label = QLabel()
        self._page_label = QLabel()
        self._zoom_label = QLabel()
        self._dirty_label = QLabel()
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.setInterval(_FLASH_MS)
        self._flash_timer.timeout.connect(self._end_flash)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(self._label)
        layout.addStretch(1)
        layout.addWidget(self._flash_label)
        layout.addWidget(self._page_label)
        layout.addStretch(1)
        layout.addWidget(self._zoom_label)
        layout.addWidget(self._dirty_label)
        self.set_edit_mode(False)
        self.set_dirty(False)

    def set_edit_mode(self, on: bool) -> None:
        """Show the edit-text label when ``on``, otherwise the regular label."""
        self._label.setText(strings.MODE_EDIT if on else strings.MODE_REGULAR)

    def set_hint(self, text: str) -> None:
        """Show a transient hint in place of the mode label (e.g. while placing)."""
        self._label.setText(text)

    def flash(self, text: str) -> None:
        """Show ``text`` centred in the bar for a few seconds, then clear it.

        Non-blocking success feedback for commands (vs. the modal error dialog).
        Independent of the mode label — flashing never disturbs the mode text.
        """
        self._flash_label.setText(text)
        self._flash_timer.start()

    def _end_flash(self) -> None:
        self._flash_label.setText("")

    def flash_text(self) -> str:
        """Return the currently displayed flash message (used by tests)."""
        return self._flash_label.text()

    def clear_hint(self) -> None:
        """Restore the mode label after a transient hint, reading the toggle state."""
        self.set_edit_mode(True)

    def set_page_label(self, current: int, total: int) -> None:
        """Show ``current/total`` in the centre (e.g. ``5/7``)."""
        self._page_label.setText(strings.PAGE_OF_FMT.format(current=current, total=total))

    def clear_page_label(self) -> None:
        """Blank the page indicator (no document open)."""
        self._page_label.setText("")

    def set_zoom_label(self, percent: int) -> None:
        """Show the current zoom as ``150%`` (right of the page indicator)."""
        self._zoom_label.setText(strings.ZOOM_FMT.format(percent=percent))

    def clear_zoom_label(self) -> None:
        """Blank the zoom indicator (no document open)."""
        self._zoom_label.setText("")

    def zoom_text(self) -> str:
        """Return the currently displayed zoom indicator (used by tests)."""
        return self._zoom_label.text()

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
