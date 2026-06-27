"""Keyboard-first file browser dialog — our own picker, no native QFileDialog.

A vim-navigable replacement for ``QFileDialog`` that adopts the shared palette
chrome (via :class:`BaseDialog`) so file picking matches the rest of the
keyboard-first app. The public ``prompt_*`` entry points that mirror the native
static methods live in :mod:`app.gui.file_dialogs`; this module owns the widget.

Listing/sorting/filtering is pure and tested in :mod:`app.gui.file_browser_model`;
this module owns the Qt widget and the vim key dispatch (mirroring
:class:`app.gui.select_controller.SelectController`, incl. the ``gg`` two-stroke).
"""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QVBoxLayout, QWidget

from app.gui import file_browser_strings as fbs
from app.gui.base_dialog import BaseDialog
from app.gui.file_browser_model import (
    FileFilter,
    FsEntry,
    drives,
    is_root,
    list_dir,
    parent_of,
    substring_filter,
)


class _Mode(Enum):
    OPEN = auto()
    SAVE = auto()
    DIR = auto()


class FileBrowserDialog(BaseDialog):
    """A directory browser navigated with vim keys; returns the chosen path."""

    def __init__(
        self,
        *,
        mode: _Mode,
        title: str,
        filt: FileFilter,
        start: Path,
        default_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._mode = mode
        self._filt = filt
        self._dir = start
        self._drives_view = False
        self._all: list[FsEntry] = []
        self._entries: list[FsEntry] = []
        self._query = ""
        self._pending_g = False
        self._result: Path | None = None

        self._path_label = QLabel()
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(lambda _item: self._activate())
        self._list.installEventFilter(self)
        self._filter = QLineEdit()
        self._filter.setPlaceholderText(fbs.FILTER_PLACEHOLDER)
        self._filter.textChanged.connect(self._on_query)
        self._filter.returnPressed.connect(self._leave_filter)
        self._filter.installEventFilter(self)
        self._filter.hide()
        self._name = QLineEdit(default_name) if mode is _Mode.SAVE else None

        layout = QVBoxLayout(self)
        layout.addWidget(self._path_label)
        layout.addWidget(self._filter)
        layout.addWidget(self._list)
        if self._name is not None:
            self._name.returnPressed.connect(self._accept_save)
            self._name.installEventFilter(self)
            layout.addWidget(self._name)
        layout.addWidget(QLabel(fbs.SAVE_KEY_HINT if mode is _Mode.SAVE else fbs.KEY_HINT))
        self.resize(560, 460)
        self._reload()
        self._list.setFocus()

    def chosen(self) -> Path | None:
        """The picked path once accepted, else ``None`` (also ``None`` if cancelled)."""
        return self._result

    # --- listing ------------------------------------------------------------

    def _reload(self) -> None:
        """List the current directory (or drive list) and reset the type-ahead filter."""
        self._query = ""
        self._filter.clear()
        self._filter.hide()
        if self._drives_view:
            self._all = drives()
            self._path_label.setText(fbs.DRIVES_LABEL)
        else:
            entries = list_dir(self._dir, self._filt)
            if self._mode is _Mode.DIR:
                entries = [entry for entry in entries if entry.is_dir]
            self._all = entries
            self._path_label.setText(str(self._dir))
        self._render()

    def _render(self) -> None:
        listing = substring_filter(self._all, self._query)
        # A ".." row tops every directory level (drive list is already the top).
        self._entries = listing if self._drives_view else [self._up_entry(), *listing]
        self._list.clear()
        for entry in self._entries:
            self._list.addItem(self._row_label(entry))
        if self._entries:
            self._list.setCurrentRow(0)

    def _up_entry(self) -> FsEntry:
        return FsEntry(fbs.UP_NAME, parent_of(self._dir), True)

    def _row_label(self, entry: FsEntry) -> str:
        if self._drives_view or entry.name == fbs.UP_NAME:
            return entry.name
        return entry.name + "/" if entry.is_dir else entry.name

    def _current(self) -> FsEntry | None:
        row = self._list.currentRow()
        return self._entries[row] if 0 <= row < len(self._entries) else None

    def _is_up(self, entry: FsEntry | None) -> bool:
        return entry is not None and not self._drives_view and entry.name == fbs.UP_NAME

    # --- navigation ---------------------------------------------------------

    def _move(self, delta: int) -> None:
        count = self._list.count()
        if count:
            self._list.setCurrentRow(max(0, min(self._list.currentRow() + delta, count - 1)))

    def _jump(self, row: int) -> None:
        if self._list.count():
            self._list.setCurrentRow(row % self._list.count())

    def _enter_dir(self, directory: Path) -> None:
        self._drives_view = False
        self._dir = directory
        self._reload()

    def _go_up(self) -> None:
        """Up a level: parent dir, or the drive list when already at a drive root."""
        if self._drives_view:
            return  # the drive list is the top; nowhere higher
        if is_root(self._dir):
            self._drives_view = True
            self._reload()
        else:
            self._enter_dir(parent_of(self._dir))

    def _activate(self) -> None:
        """``l`` / double-click: up via ``..``, descend into a dir, or pick a file."""
        entry = self._current()
        if entry is None:
            return
        if self._is_up(entry):
            self._go_up()
        elif entry.is_dir:
            self._enter_dir(entry.path)
        elif self._mode is _Mode.OPEN:
            self._finish(entry.path)
        elif self._mode is _Mode.SAVE and self._name is not None:
            self._name.setText(entry.name)

    def _on_enter(self) -> None:
        """Enter key: ``..``/drive navigation first, then choose-folder / descend / pick."""
        entry = self._current()
        if self._is_up(entry):
            self._go_up()
        elif self._drives_view:
            self._activate()  # pick a drive to enter
        elif self._mode is _Mode.DIR:
            self._finish(self._dir)  # navigate in with l/h, Enter chooses the folder shown
        elif entry is not None and entry.is_dir:
            self._enter_dir(entry.path)
        elif self._mode is _Mode.SAVE:
            self._accept_save() if entry is None else self._finish(self._dir / entry.name)
        elif entry is not None:
            self._finish(entry.path)

    def _finish(self, path: Path) -> None:
        self._result = path
        self.accept()

    def _accept_save(self) -> None:
        name = self._name.text().strip() if self._name is not None else ""
        if name:
            self._finish(self._dir / name)

    # --- type-ahead filter --------------------------------------------------

    def _open_filter(self) -> None:
        self._filter.show()
        self._filter.setFocus()

    def _on_query(self, text: str) -> None:
        self._query = text
        self._render()

    def _leave_filter(self) -> None:
        self._list.setFocus()

    # --- key dispatch -------------------------------------------------------

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Intercept keys on the focused child (list never sees nav keys itself)."""
        if event.type() == QEvent.Type.KeyPress:
            key_event = cast(QKeyEvent, event)
            if watched is self._list:
                return self._handle_nav(key_event)
            if watched is self._filter and key_event.key() == Qt.Key.Key_Escape:
                self._filter.clear()
                self._leave_filter()
                return True
            if watched is self._name and key_event.key() == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(watched, event)

    def _handle_nav(self, event: QKeyEvent) -> bool:
        key = event.key()
        text = event.text()
        alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
        if text != "g":
            self._pending_g = False
        if key == Qt.Key.Key_Escape or text == "q":
            self.reject()
        elif alt and key == Qt.Key.Key_Up:
            self._go_up()
        elif text == "j" or key == Qt.Key.Key_Down:
            self._move(1)
        elif text == "k" or key == Qt.Key.Key_Up:
            self._move(-1)
        elif text == "g":
            self._handle_g()
        elif text == "G":
            self._jump(-1)
        elif text == "h" or key == Qt.Key.Key_Left:
            self._go_up()
        elif text == "l" or key == Qt.Key.Key_Right:
            self._activate()
        elif text == "/":
            self._open_filter()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_enter()
        elif key == Qt.Key.Key_Tab and self._name is not None:
            self._name.setFocus()
        else:
            return False
        return True

    def _handle_g(self) -> None:
        if self._pending_g:
            self._jump(0)
            self._pending_g = False
        else:
            self._pending_g = True
