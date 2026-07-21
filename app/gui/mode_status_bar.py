"""A thin footer bar showing the viewer's current mode.

Presentation only: the window flips it via :meth:`set_edit_mode` from the same
``edit_mode_toggled`` signal that drives the controller and toolbar, so the label
always reflects the real mode without owning any state of its own.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.gui import strings

_FLASH_MS = 3000


class ModeStatusBar(QWidget):
    """Footer: mode label on the left, file position / page stacked centred."""

    def __init__(self) -> None:
        super().__init__()
        self._label = QLabel()
        self._flash_label = QLabel()
        self._file_label = QLabel()
        self._page_label = QLabel()
        self._zoom_label = QLabel()
        self._dirty_label = QLabel()
        self._paged = True
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.setInterval(_FLASH_MS)
        self._flash_timer.timeout.connect(self._end_flash)
        # Empty rows are hidden so the bar collapses to one row without a doc.
        self._file_label.hide()
        self._page_label.hide()
        position = QVBoxLayout()
        position.setContentsMargins(0, 0, 0, 0)
        position.setSpacing(0)
        position.addWidget(self._file_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        position.addWidget(self._page_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(self._label)
        layout.addStretch(1)
        layout.addWidget(self._flash_label)
        layout.addLayout(position)
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

    def set_paged_document(self, on: bool) -> None:
        """Paged documents (PDFs) get labeled File/Page rows; the rest a bare counter.

        While off, ``set_page_label`` is a no-op — the ``page_changed`` signal
        still fires for single-page formats, and a ``Page 1/1`` row is noise.
        """
        self._paged = on
        if not on:
            self.clear_page_label()

    def set_file_label(self, current: int, total: int) -> None:
        """Show the file position in the centre's top row (``File 2/5`` or ``2/5``)."""
        fmt = strings.FILE_OF_FMT if self._paged else strings.FILE_COMPACT_FMT
        self._file_label.setText(fmt.format(current=current, total=total))
        self._file_label.show()

    def clear_file_label(self) -> None:
        """Blank and hide the file-position row (no document open)."""
        self._file_label.setText("")
        self._file_label.hide()

    def set_page_label(self, current: int, total: int) -> None:
        """Show ``Page current/total`` in the centre's bottom row (paged docs only)."""
        if not self._paged:
            return
        self._page_label.setText(strings.LABEL_PAGE_FMT.format(current=current, total=total))
        self._page_label.show()

    def clear_page_label(self) -> None:
        """Blank and hide the page row (no document open)."""
        self._page_label.setText("")
        self._page_label.hide()

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

    def file_text(self) -> str:
        """Return the currently displayed file-position indicator (used by tests)."""
        return self._file_label.text()
