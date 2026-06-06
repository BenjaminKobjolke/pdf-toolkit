"""Page-level PDF operations (swap, delete, merge) for the viewer window.

Swap/delete run on the temp working copy through :class:`DeferredOps`, so they
only reach the original file when the user saves. Merge is different — it builds
a new ``merged.pdf`` and reopens it — so it stays immediate via the runner. Kept
out of ``MainWindow`` so the window stays a thin coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from app.gui import strings
from app.gui.deferred_ops import DeferredOps
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_view import PageView
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.merger import MERGED_FILENAME, merge_folder
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
    ) -> None:
        self._parent = parent
        self._deferred = deferred
        self._page_view: PageView = deferred.page_view
        self._runner = runner
        self._open_pdf = open_pdf
        self._report = report

    def swap(self) -> None:
        self._deferred.run(swap_two_pages)

    def delete_current_page(self) -> None:
        if self._deferred.working() is None:
            return
        page = self._page_view.current_page_one_based()
        total = self._page_view.total_pages()
        confirm = QMessageBox.question(
            self._parent,
            strings.CONFIRM_TITLE,
            strings.CONFIRM_DELETE_PAGE_FMT.format(page=page, total=total),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._deferred.run(lambda p: delete_page(p, page))

    def delete_page_range(self) -> None:
        if self._deferred.working() is None:
            return
        total = self._page_view.total_pages()
        start, ok = QInputDialog.getInt(
            self._parent, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_START, 1, 1, total
        )
        if not ok:
            return
        end, ok = QInputDialog.getInt(
            self._parent, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_END, start, start, total
        )
        if not ok:
            return
        self._deferred.run(lambda p: delete_page_range(p, start, end))

    def merge_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self._parent, strings.DIALOG_MERGE_TITLE)
        if not chosen:
            return
        result = self._runner.run_folder_merge(Path(chosen), merge_folder)
        if result.ok:
            self._open_pdf(Path(chosen) / MERGED_FILENAME)
        self._report(result)
