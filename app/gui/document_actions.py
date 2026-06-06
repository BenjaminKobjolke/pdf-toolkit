"""Document-level dialogs for history, rename, and saved text fields."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget

from app.config.recent_files import RecentFilesStore
from app.gui import strings
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.operations import OpResult
from app.gui.save_controller import SaveController
from app.pdf.renamer import rename_document


class DocumentActions:
    """Own document dialogs that do not belong to rendering or page operations."""

    def __init__(
        self,
        parent: QWidget,
        recent: RecentFilesStore,
        controller: EditController,
        save: SaveController,
        source: Callable[[], Path | None],
        open_pdf: Callable[[Path | None], None],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._recent = recent
        self._controller = controller
        self._save = save
        self._source = source
        self._open_pdf = open_pdf
        self._report = report

    def open_from_history(self) -> None:
        """Pick a recently-opened PDF from the history list and open it."""
        entries = [
            ListEntry(title=path.name, subtitle=str(path), payload=path)
            for path in self._recent.load()
        ]
        if not entries:
            QMessageBox.information(
                self._parent, strings.HISTORY_TITLE, strings.LABEL_HISTORY_EMPTY
            )
            return
        dialog = FilterListDialog(
            entries,
            placeholder=strings.HISTORY_PLACEHOLDER,
            title=strings.HISTORY_TITLE,
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._open_pdf(chosen.payload)

    def delete_saved_text_fields(self) -> None:
        if self._source() is None:
            return
        confirm = QMessageBox.question(
            self._parent, strings.CONFIRM_TITLE, strings.CONFIRM_DELETE_SAVED_FIELDS
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._controller.clear_saved_fields()

    def rename_file(self) -> None:
        """Rename the open PDF and its sidecar, then reopen under the new name."""
        source = self._source()
        if source is None:
            return
        name, ok = QInputDialog.getText(
            self._parent,
            strings.DIALOG_RENAME_TITLE,
            strings.PROMPT_RENAME,
            text=source.name,
        )
        if not ok or not name.strip():
            return
        target = source.with_name(name.strip())
        if target.suffix == "":
            target = target.with_suffix(source.suffix)
        if not self._save.confirm_unsaved():
            return
        try:
            rename_document(source, target)
        except (OSError, ValueError) as err:
            self._report(OpResult(False, str(err)))
            return
        self._open_pdf(target)
        self._report(OpResult(True, strings.MSG_RENAMED_FMT.format(name=target.name)))
