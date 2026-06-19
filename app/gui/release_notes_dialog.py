"""A dialog that shows release notes, newest first, with Older/Newer navigation.

The notes arrive already sorted newest-first (index 0 is the latest release);
the Older button walks to higher indices (further back in time) and Newer walks
back toward the latest. Reads only the typed :class:`ReleaseNote` objects, so it
has no knowledge of the on-disk JSON layout.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
)

from app.gui import release_strings
from app.gui.form_dialog import FormDialog
from app.release.notes_loader import ReleaseNote


class ReleaseNotesDialog(FormDialog):
    """Browse release notes one release at a time, latest shown first."""

    def __init__(self, notes: Sequence[ReleaseNote], parent: QWidget | None = None) -> None:
        super().__init__(title=release_strings.TITLE, parent=parent)
        self._notes = list(notes)
        self._index = 0

        self._heading = QLabel()
        self._heading.setWordWrap(True)
        self._body = QTextEdit()
        self._body.setReadOnly(True)
        self.add_content(self._heading)
        self.add_content(self._body)

        self._older = QPushButton(release_strings.OLDER)
        self._newer = QPushButton(release_strings.NEWER)
        self._older.clicked.connect(self._show_older)
        self._newer.clicked.connect(self._show_newer)
        nav = QHBoxLayout()
        nav.addWidget(self._older)
        nav.addWidget(self._newer)
        nav.addStretch(1)
        nav_row = QWidget()
        nav_row.setLayout(nav)
        self.add_content(nav_row)

        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        close.accepted.connect(self.accept)
        self.add_buttons(close)

        self.resize(480, 380)
        self._render()

    def _show_older(self) -> None:
        self._index = min(self._index + 1, len(self._notes) - 1)
        self._render()

    def _show_newer(self) -> None:
        self._index = max(self._index - 1, 0)
        self._render()

    def _render(self) -> None:
        if not self._notes:
            self._heading.setText(release_strings.EMPTY)
            self._body.setPlainText("")
            self._older.setEnabled(False)
            self._newer.setEnabled(False)
            return
        note = self._notes[self._index]
        self._heading.setText(
            release_strings.HEADER_FMT.format(
                title=note.title,
                label=note.label,
                date=note.date,
                position=self._index + 1,
                total=len(self._notes),
            )
        )
        self._body.setPlainText(
            "\n".join(release_strings.BULLET.format(note=line) for line in note.notes)
        )
        self._newer.setEnabled(self._index > 0)
        self._older.setEnabled(self._index < len(self._notes) - 1)
