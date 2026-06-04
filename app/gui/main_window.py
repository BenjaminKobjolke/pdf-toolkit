"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.config.recent_files import RecentFilesStore
from app.config.settings import Settings
from app.gui import commands, strings
from app.gui.commands import Command
from app.gui.controls import OperationBar
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_view import PageView
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.merger import MERGED_FILENAME, merge_folder
from app.pdf.swapper import swap_two_pages

# Direct keyboard shortcuts -> command id. The palette has its own chord below.
_SHORTCUTS: tuple[tuple[str, str], ...] = (
    ("PgDown", commands.NEXT_PAGE),
    ("PgUp", commands.PREV_PAGE),
    ("Home", commands.FIRST_PAGE),
    ("End", commands.LAST_PAGE),
    ("Ctrl++", commands.ZOOM_IN),
    ("Ctrl+=", commands.ZOOM_IN),
    ("Ctrl+-", commands.ZOOM_OUT),
    ("Ctrl+0", commands.ZOOM_ACTUAL),
    ("Ctrl+F", commands.ZOOM_FIT),
)
_PALETTE_CHORD = "Ctrl+Shift+P"


class MainWindow(QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._runner = GuiOperationRunner(settings)
        self._recent = RecentFilesStore(settings.recent_file)
        self._source: Path | None = None

        self._page_view = PageView()
        self._bar = OperationBar()
        self._edit_bar = EditBar()
        self._controller = EditController(self._page_view)
        self._page_view.page_changed.connect(self._bar.set_page_label)

        self._bar.prev_requested.connect(self._page_view.show_prev)
        self._bar.next_requested.connect(self._page_view.show_next)
        self._bar.swap_requested.connect(self.swap_pages)
        self._bar.delete_page_requested.connect(self.delete_current_page)
        self._bar.delete_range_requested.connect(self.delete_page_range)
        self._bar.merge_folder_requested.connect(self.merge_folder)

        self._edit_bar.edit_mode_toggled.connect(self._controller.set_edit_mode)
        self._edit_bar.add_field_requested.connect(self._controller.add_field)
        self._edit_bar.delete_field_requested.connect(self._controller.delete_selected)
        self._edit_bar.style_changed.connect(self._controller.apply_style)
        self._edit_bar.export_text_requested.connect(self.export_text)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._bar)
        layout.addWidget(self._edit_bar)
        layout.addWidget(self._page_view, 1)
        self.setCentralWidget(central)

        self.setWindowTitle(strings.WINDOW_TITLE)
        self._registry = commands.build_commands(self)
        self._build_menu()
        self._install_shortcuts()
        self.resize(800, 900)

    # --- accessors used by the command registry -----------------------------

    @property
    def page_view(self) -> PageView:
        return self._page_view

    @property
    def controller(self) -> EditController:
        return self._controller

    def has_document(self) -> bool:
        return self._source is not None

    # --- document lifecycle -------------------------------------------------

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
        # Load saved fields before rendering so the first page_changed restores
        # them onto the page (fields show whether or not edit mode is on).
        self._load_text_fields(path)
        self._page_view.load(path)
        self._bar.set_enabled_for_doc(True)
        self._recent.add(path)
        self.setWindowTitle(f"{strings.WINDOW_TITLE} — {path.name}")

    def open_from_history(self) -> None:
        """Pick a recently-opened PDF from the history list and open it."""
        recent = self._recent.load()
        entries = [ListEntry(title=p.name, subtitle=str(p), payload=p) for p in recent]
        if not entries:
            QMessageBox.information(self, strings.HISTORY_TITLE, strings.LABEL_HISTORY_EMPTY)
            return
        dialog = FilterListDialog(
            entries,
            placeholder=strings.HISTORY_PLACEHOLDER,
            title=strings.HISTORY_TITLE,
            parent=self,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self.open_pdf(chosen.payload)

    def close_document(self) -> None:
        """Persist pending edits and return to the empty viewer state."""
        self._controller.flush()
        self._page_view.reset()
        self._bar.set_enabled_for_doc(False)
        if self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()
        self._source = None
        self.setWindowTitle(strings.WINDOW_TITLE)

    def exit_app(self) -> None:
        self.close()

    # --- command palette ----------------------------------------------------

    def open_command_palette(self) -> None:
        """Show the type-to-filter palette over all enabled commands."""
        entries = [
            ListEntry(title=cmd.title, enabled=cmd.is_enabled(), payload=cmd)
            for cmd in self._registry
        ]
        dialog = FilterListDialog(
            entries,
            placeholder=strings.PALETTE_PLACEHOLDER,
            title=strings.PALETTE_TITLE,
            parent=self,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            command: Command = chosen.payload
            command.run()

    # --- text-field actions -------------------------------------------------

    def toggle_edit_mode(self) -> None:
        self._edit_bar.toggle_edit_mode()

    def export_text(self) -> None:
        if self._source is None:
            return
        self._report(self._controller.export(self._source))

    def delete_saved_text_fields(self) -> None:
        if self._source is None:
            return
        confirm = QMessageBox.question(
            self, strings.CONFIRM_TITLE, strings.CONFIRM_DELETE_SAVED_FIELDS
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._controller.clear_saved_fields()

    # --- page operations ----------------------------------------------------

    def swap_pages(self) -> None:
        if self._source is None:
            return
        self._run_on_file(swap_two_pages)

    def delete_current_page(self) -> None:
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

    def delete_page_range(self) -> None:
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

    def merge_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, strings.DIALOG_MERGE_TITLE)
        if not chosen:
            return
        result = self._runner.run_folder_merge(Path(chosen), merge_folder)
        if result.ok:
            self.open_pdf(Path(chosen) / MERGED_FILENAME)
        self._report(result)

    # --- internals ----------------------------------------------------------

    def _load_text_fields(self, path: Path) -> None:
        try:
            self._controller.on_document_loaded(path)
        except ValueError as err:
            QMessageBox.warning(
                self,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_SIDECAR_LOAD_FAILED_FMT.format(error=err),
            )

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu(strings.MENU_FILE)
        menu.addAction(strings.ACTION_COMMAND_PALETTE, self.open_command_palette)
        menu.addAction(strings.ACTION_OPEN, lambda: self.open_pdf())
        menu.addAction(strings.ACTION_OPEN_HISTORY, self.open_from_history)
        menu.addSeparator()
        menu.addAction(strings.ACTION_QUIT, self.close)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence(_PALETTE_CHORD), self, self.open_command_palette)
        for chord, command_id in _SHORTCUTS:
            command = commands.find(self._registry, command_id)
            QShortcut(QKeySequence(chord), self, self._guarded(command))

    @staticmethod
    def _guarded(command: Command) -> Callable[[], None]:
        """Wrap a command so a shortcut is a no-op when the command is disabled."""

        def trigger() -> None:
            if command.is_enabled():
                command.run()

        return trigger

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
