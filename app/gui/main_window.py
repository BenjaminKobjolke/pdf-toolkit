"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import Settings
from app.gui import strings
from app.gui.controls import OperationBar
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_view import PageView
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.merger import merge_folder
from app.pdf.swapper import swap_two_pages


class MainWindow(QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._runner = GuiOperationRunner(settings)
        self._source: Path | None = None

        self._page_view = PageView()
        self._bar = OperationBar()
        self._page_view.page_changed.connect(self._bar.set_page_label)

        self._bar.prev_requested.connect(self._page_view.show_prev)
        self._bar.next_requested.connect(self._page_view.show_next)
        self._bar.swap_requested.connect(self._on_swap)
        self._bar.delete_page_requested.connect(self._on_delete_page)
        self._bar.delete_range_requested.connect(self._on_delete_range)
        self._bar.merge_folder_requested.connect(self._on_merge_folder)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._bar)
        layout.addWidget(self._page_view, 1)
        self.setCentralWidget(central)

        self.setWindowTitle(strings.WINDOW_TITLE)
        self._build_menu()
        self.resize(800, 900)

    def open_pdf(self, path: Path | None = None) -> None:
        """Open ``path`` (or prompt for one) and display its first page."""
        if path is None:
            chosen, _ = QFileDialog.getOpenFileName(
                self, strings.DIALOG_OPEN_TITLE, "", strings.FILE_FILTER_PDF
            )
            if not chosen:
                return
            path = Path(chosen)
        self._source = path
        self._page_view.load(path)
        self._bar.set_enabled_for_doc(True)
        self.setWindowTitle(f"{strings.WINDOW_TITLE} — {path.name}")

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu(strings.MENU_FILE)
        menu.addAction(strings.ACTION_OPEN, lambda: self.open_pdf())
        menu.addAction(strings.ACTION_QUIT, self.close)

    def _on_swap(self) -> None:
        if self._source is None:
            return
        self._run_on_file(swap_two_pages)

    def _on_delete_page(self) -> None:
        if self._source is None:
            return
        page = self._page_view.current_page_one_based()
        total = self._page_view.total_pages()
        confirm = QMessageBox.question(
            self,
            strings.CONFIRM_TITLE,
            strings.CONFIRM_DELETE_PAGE_FMT.format(page=page, total=total),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._run_on_file(lambda p: delete_page(p, page))

    def _on_delete_range(self) -> None:
        if self._source is None:
            return
        total = self._page_view.total_pages()
        start, ok = QInputDialog.getInt(
            self, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_START, 1, 1, total
        )
        if not ok:
            return
        end, ok = QInputDialog.getInt(
            self, strings.DIALOG_RANGE_TITLE, strings.PROMPT_RANGE_END, start, start, total
        )
        if not ok:
            return
        self._run_on_file(lambda p: delete_page_range(p, start, end))

    def _on_merge_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, strings.DIALOG_MERGE_TITLE)
        if not chosen:
            return
        result = self._runner.run_folder_merge(Path(chosen), merge_folder)
        self._report(result)

    def _run_on_file(self, op: Callable[[Path], None]) -> None:
        assert self._source is not None
        result = self._runner.run_on_file(self._source, op)
        if result.ok:
            self._page_view.reload()
        self._report(result)

    def _report(self, result: OpResult) -> None:
        if result.ok:
            QMessageBox.information(self, strings.DIALOG_SUCCESS_TITLE, result.message)
        else:
            QMessageBox.critical(self, strings.DIALOG_ERROR_TITLE, result.message)
