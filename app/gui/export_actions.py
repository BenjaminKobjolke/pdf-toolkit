"""The 'Export text to PDF' flow: flatten placed fields onto a PDF.

Extracted from ``MainWindow`` so the window stays a thin coordinator (and under
the 300-line cap). Exporting asks whether to overwrite the original or write a
new file:

* **Overwrite** bakes the text into the working copy and reuses the normal save
  (backup + atomic write + sidecar drop), so the text is no longer editable.
* **New file** writes a flattened copy elsewhere and leaves the edit session
  intact, so the original stays editable.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QWidget

from app.gui import strings
from app.gui.edit_controller import EditController
from app.gui.operations import OpResult
from app.gui.page_view import PageView
from app.gui.save_controller import SaveController
from app.gui.working_document import WorkingDocument


class ExportActions:
    """Owns the export-text command: overwrite the original or write a new file."""

    def __init__(
        self,
        parent: QWidget,
        controller: EditController,
        working_doc: WorkingDocument,
        save: SaveController,
        page_view: PageView,
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._controller = controller
        self._doc = working_doc
        self._save = save
        self._page_view = page_view
        self._report = report

    def export(self) -> None:
        """Prompt overwrite/new-file/cancel, then flatten the placed fields."""
        working = self._doc.working()
        source = self._doc.original()
        if working is None or source is None:
            return
        if not self._controller.has_placed_fields():
            self._report(OpResult(True, strings.MSG_NO_TEXT_TO_EXPORT))
            return
        choice = QMessageBox.question(
            self._parent,
            strings.CONFIRM_EXPORT_TITLE,
            strings.CONFIRM_EXPORT_OVERWRITE,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self._overwrite(working)
        elif choice == QMessageBox.StandardButton.No:
            self._new_file(working, source)
        # Cancel: leave the fields in place and do nothing.

    def _overwrite(self, working: Path) -> None:
        """Bake the text into the original on disk (with backup) and drop the sidecar."""
        baked = self._controller.embed_into_document(working)
        if not baked.ok:
            self._report(baked)
            return
        self._save.mark_dirty()
        self._page_view.reload()
        self._save.save()  # flush + backup + write original + drop sidecar + report

    def _new_file(self, working: Path, source: Path) -> None:
        """Write a flattened copy to a new file; the original stays editable."""
        name = self._prompt_export_name(source.name)
        if name is None:
            return
        target = source.with_name(name)
        if target.suffix == "":
            target = target.with_suffix(".pdf")
        self._report(self._controller.export_to_file(working, target))

    def _prompt_export_name(self, default: str) -> str | None:
        """Ask for the new file name, pre-filled with ``default`` and caret at the end."""
        dialog = QInputDialog(self._parent)
        dialog.setWindowTitle(strings.DIALOG_EXPORT_NAME_TITLE)
        dialog.setLabelText(strings.PROMPT_EXPORT_NAME)
        dialog.setTextValue(default)
        edit = dialog.findChild(QLineEdit)
        if edit is not None:
            edit.deselect()
            edit.end(False)
        if not dialog.exec():
            return None
        value = dialog.textValue().strip()
        return value or None
