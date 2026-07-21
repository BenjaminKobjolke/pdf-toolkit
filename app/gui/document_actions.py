"""Document-level dialogs for history, rename, and saved text fields."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget
from send2trash import send2trash

from app.config.recent_files import RecentFilesStore
from app.gui import (
    confirm_dialog,
    file_browser_model,
    file_browser_strings,
    file_dialogs,
    file_strings,
    strings,
    text_prompt_dialog,
)
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.operations import OpResult
from app.gui.save_controller import SaveController
from app.gui.thumbnails_controller import ThumbnailsController
from app.pdf.file_format import FileFormat
from app.pdf.renamer import rename_document
from app.pdf.sidecar import sidecar_path


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
        grid: ThumbnailsController,
        advance: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._recent = recent
        self._controller = controller
        self._save = save
        self._source = source
        self._open_pdf = open_pdf
        self._report = report
        self._grid = grid
        self._advance = advance

    def open_from_history(self) -> None:
        """Pick a recently-opened document from the history list and open it."""
        entries = [
            ListEntry(title=path.name, subtitle=str(path), payload=path)
            for path in self._recent.load()
        ]
        self._pick_and_open(entries, strings.HISTORY_TITLE, strings.HISTORY_PLACEHOLDER)

    def open_folder_from_history(self) -> None:
        """Pick a recently-used folder and reopen its last-opened document."""
        # First occurrence of each parent is that folder's most recent file
        # (history is most-recent-first; dict insertion order keeps recency).
        last_per_folder: dict[Path, Path] = {}
        for path in self._recent.load():
            last_per_folder.setdefault(path.parent, path)
        entries = [
            ListEntry(title=folder.name, subtitle=str(folder), payload=last_file)
            for folder, last_file in last_per_folder.items()
        ]
        self._pick_and_open(
            entries, strings.FOLDER_HISTORY_TITLE, strings.FOLDER_HISTORY_PLACEHOLDER
        )

    def _pick_and_open(self, entries: list[ListEntry], title: str, placeholder: str) -> None:
        if not entries:
            confirm_dialog.show_message(self._parent, title, strings.LABEL_HISTORY_EMPTY)
            return
        dialog = FilterListDialog(
            entries,
            FilterListOptions(placeholder=placeholder, title=title),
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._open_pdf(chosen.payload)

    def _target(self) -> Path | None:
        """The file to act on: the selected thumbnail while the grid shows, else the open doc."""
        return self._grid.selected_path() or self._source()

    def _confirm_yes_no(self, message: str) -> bool:
        choice = confirm_dialog.confirm(
            self._parent,
            confirm_dialog.ConfirmSpec(
                title=strings.CONFIRM_TITLE,
                message=message,
                primary=strings.BTN_YES,
                secondary=strings.BTN_NO,
            ),
        )
        return choice is confirm_dialog.DialogResult.PRIMARY

    def delete_saved_text_fields(self) -> None:
        target = self._target()
        if target is None:
            return
        if not self._confirm_yes_no(strings.CONFIRM_DELETE_SAVED_FIELDS):
            return
        if target == self._source():
            self._controller.clear_saved_fields()
        else:
            # Another file's sidecar: disk only — the open doc's overlay stays.
            sidecar_path(target).unlink(missing_ok=True)
            self._report(
                OpResult(True, strings.MSG_SAVED_FIELDS_DELETED_FMT.format(name=target.name))
            )

    def delete_file(self) -> None:
        """Move the target file and its sidecar to the recycle bin.

        Deleting the open document advances to the next file in the folder
        (empty state if none); deleting another file refreshes the grid onto
        its next sibling.
        """
        target = self._target()
        if target is None:
            return
        if not self._confirm_yes_no(file_strings.CONFIRM_DELETE_FILE_FMT.format(name=target.name)):
            return
        is_open_doc = target == self._source()
        if is_open_doc:
            # The file is going away; a save prompt would write into the trash.
            self._save.discard_unsaved()
        if not self._try_trash(target):
            return
        if is_open_doc:
            self._advance()  # next sibling or empty state; after_open dismisses the grid
        else:
            self._grid.refresh(
                select=file_browser_model.nearest_file(target, self._grid.current_filter())
            )
        self._report(OpResult(True, file_strings.MSG_FILE_DELETED_FMT.format(name=target.name)))

    def _try_trash(self, target: Path) -> bool:
        try:
            send2trash(target)
            sidecar = sidecar_path(target)
            if sidecar.exists():  # send2trash has no missing_ok
                send2trash(sidecar)
        except OSError as err:
            self._report(OpResult(False, str(err)))
            return False
        return True

    def save_as(self) -> None:
        """Write the open document to a chosen new file and switch to it."""
        source = self._source()
        if source is None:
            return
        fmt = FileFormat.of(source)
        filt = (
            file_browser_strings.FILTER_PDF
            if fmt is FileFormat.PDF
            else file_browser_strings.FILTER_VIEWER_IMAGES
        )
        # A PSD's working copy is a PNG conversion; the suggested name must match
        # the bytes Save-As will actually copy.
        suggestion = source.with_suffix(".png") if fmt is FileFormat.PSD else source
        dest = file_dialogs.prompt_save_file(
            self._parent, file_strings.DIALOG_SAVE_AS_TITLE, suggestion, filt
        )
        if dest is None:
            return
        result = self._save.save_as(dest)
        self._report(result)
        if result.ok:
            self._open_pdf(dest)

    def rename_file(self) -> None:
        """Rename the target file and its sidecar.

        The target is the selected thumbnail while the grid shows, else the
        open document. The open document is reopened under its new name; any
        other file is renamed in place and the grid refreshed.
        """
        source = self._target()
        if source is None:
            return
        name = text_prompt_dialog.prompt_text(
            self._parent,
            strings.DIALOG_RENAME_TITLE,
            strings.PROMPT_RENAME,
            source.name,
        )
        if name is None:
            return
        target = source.with_name(name)
        if target.suffix == "":
            target = target.with_suffix(source.suffix)
        if source == self._source():
            self._rename_open_document(source, target)
        else:
            self._rename_other_file(source, target)

    def _rename_open_document(self, source: Path, target: Path) -> None:
        if not self._save.confirm_unsaved():
            return
        if not self._try_rename(source, target):
            return
        self._open_pdf(target)  # after_open dismisses the grid if it was showing
        self._report(OpResult(True, strings.MSG_RENAMED_FMT.format(name=target.name)))

    def _rename_other_file(self, source: Path, target: Path) -> None:
        if not self._try_rename(source, target):
            return
        self._grid.refresh(select=target)
        self._report(OpResult(True, strings.MSG_RENAMED_FMT.format(name=target.name)))

    def _try_rename(self, source: Path, target: Path) -> bool:
        try:
            rename_document(source, target)
        except (OSError, ValueError) as err:
            self._report(OpResult(False, str(err)))
            return False
        return True
