"""Checklist dialog for picking which file types to associate with the viewer.

One checkable row per :class:`~app.pdf.file_format.FileFormat`; the caller
passes the currently-registered extensions and gets back the full desired set
(or ``None`` on cancel) to feed to
:func:`app.os_integration.file_association.set_associations`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QWidget

from app.gui import default_app_strings as ds
from app.gui.form_dialog import FormDialog, exec_value
from app.pdf.file_format import FileFormat

_EXT_ROLE = Qt.ItemDataRole.UserRole


def _kind(fmt: FileFormat) -> str:
    if fmt is FileFormat.PDF:
        return ds.KIND_PDF
    if fmt is FileFormat.TXT:
        return ds.KIND_TEXT
    if fmt is FileFormat.MD:
        return ds.KIND_MARKDOWN
    return ds.KIND_IMAGE  # everything else is IMAGE_FORMATS


class FileAssociationDialog(FormDialog):
    """Checkbox list of all supported file types."""

    def __init__(self, *, checked: frozenset[str], parent: QWidget | None = None) -> None:
        super().__init__(title=ds.TITLE, message=ds.DIALOG_MESSAGE, parent=parent)
        self.add_content(self._build_all_buttons())
        self._list = QListWidget(self)
        for fmt in FileFormat:
            item = QListWidgetItem(f"{fmt.value} — {_kind(fmt)}")
            item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable  # arrow keys need a selectable row
            )
            item.setData(_EXT_ROLE, fmt.value)
            state = Qt.CheckState.Checked if fmt.value in checked else Qt.CheckState.Unchecked
            item.setCheckState(state)
            self._list.addItem(item)
        self._list.setCurrentRow(0)  # keyboard-only: arrows + Space work immediately
        self.add_content(self._list)
        self.add_ok_cancel()
        self._list.setFocus()

    def _build_all_buttons(self) -> QWidget:
        """Row with the Select all / Unselect all buttons."""
        self._select_all = QPushButton(ds.BTN_SELECT_ALL, self)
        self._unselect_all = QPushButton(ds.BTN_UNSELECT_ALL, self)
        self._select_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        self._unselect_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._select_all)
        layout.addWidget(self._unselect_all)
        return row

    def _set_all(self, state: Qt.CheckState) -> None:
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def selected(self) -> frozenset[str]:
        """The extensions currently checked."""
        return frozenset(
            item.data(_EXT_ROLE)
            for i in range(self._list.count())
            if (item := self._list.item(i)).checkState() is Qt.CheckState.Checked
        )


def ask_associations(parent: QWidget | None, *, checked: frozenset[str]) -> frozenset[str] | None:
    """Run the dialog modally; return the desired set, or ``None`` on cancel."""
    dialog = FileAssociationDialog(checked=checked, parent=parent)
    return exec_value(dialog, dialog.selected)
