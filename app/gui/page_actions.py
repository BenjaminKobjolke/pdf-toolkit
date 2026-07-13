"""Page-level PDF operations (swap, delete, merge) for the viewer window.

Swap/delete run on the temp working copy through :class:`DeferredOps`, so they
only reach the original file when the user saves. Merge is different — it builds
a new ``merged.pdf`` and reopens it — so it stays immediate via the runner. Kept
out of ``MainWindow`` so the window stays a thin coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.gui import (
    confirm_dialog,
    file_browser_strings,
    file_dialogs,
    number_input_dialog,
    strings,
)
from app.gui.deferred_ops import DeferredOps
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_view import PageView
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.extractor import default_extract_dest, extract_page
from app.pdf.inserter import insert_after
from app.pdf.merger import merge_folder, merged_output_path
from app.pdf.swapper import swap_two_pages


class PageActions:
    """Swap/delete (deferred) and merge (immediate) commands for the open document."""

    def __init__(
        self,
        parent: QWidget,
        deferred: DeferredOps,
        runner: GuiOperationRunner,
        open_pdf: Callable[[Path], None],
        report: Callable[[OpResult], None],
        current_source: Callable[[], Path | None],
    ) -> None:
        self._parent = parent
        self._deferred = deferred
        self._page_view: PageView = deferred.page_view
        self._runner = runner
        self._open_pdf = open_pdf
        self._report = report
        self._current_source = current_source

    def swap(self) -> None:
        self._deferred.run(swap_two_pages)

    def delete_current_page(self) -> None:
        if self._deferred.working() is None:
            return
        page = self._page_view.current_page_one_based()
        total = self._page_view.total_pages()
        choice = confirm_dialog.confirm(
            self._parent,
            strings.CONFIRM_TITLE,
            strings.CONFIRM_DELETE_PAGE_FMT.format(page=page, total=total),
            primary=strings.BTN_YES,
            secondary=strings.BTN_NO,
        )
        if choice is not confirm_dialog.DialogResult.PRIMARY:
            return
        self._deferred.run(lambda p: delete_page(p, page))

    def delete_page_range(self) -> None:
        if self._deferred.working() is None:
            return
        total = self._page_view.total_pages()
        start = number_input_dialog.prompt_int(
            self._parent, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_START, 1, 1, total
        )
        if start is None:
            return
        end = number_input_dialog.prompt_int(
            self._parent, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_END, start, start, total
        )
        if end is None:
            return
        self._deferred.run(lambda p: delete_page_range(p, start, end))

    def insert_pages(self) -> None:
        """Insert a chosen PDF or image after the current page (deferred until save)."""
        if self._deferred.working() is None:
            return
        source = self._current_source()
        chosen = file_dialogs.prompt_open_file(
            self._parent,
            strings.DIALOG_INSERT_TITLE,
            file_browser_strings.FILTER_INSERT,
            source.parent if source is not None else None,
        )
        if chosen is None:
            return
        insert = chosen
        after = self._page_view.current_page_one_based()
        self._deferred.run(lambda p: insert_after(p, insert, after), follow_page=after + 1)

    def extract_current_page(self) -> None:
        """Write the current page to a new file; the open document is left unchanged."""
        working = self._deferred.working()
        original = self._current_source()
        if working is None or original is None:
            return
        page = self._page_view.current_page_one_based()
        default = default_extract_dest(original, page)
        dest = file_dialogs.prompt_save_file(
            self._parent, strings.DIALOG_EXTRACT_TITLE, default, file_browser_strings.FILTER_PDF
        )
        if dest is None:
            return
        self._report(self._runner.run_to_new_file(working, lambda p: extract_page(p, page, dest)))

    def merge_folder(self) -> None:
        source = self._current_source()
        chosen = file_dialogs.prompt_directory(
            self._parent,
            strings.DIALOG_MERGE_TITLE,
            source.parent if source is not None else None,
        )
        if chosen is None:
            return
        result = self._runner.run_folder_merge(chosen, merge_folder)
        if result.ok:
            self._open_pdf(merged_output_path(chosen))
        self._report(result)
