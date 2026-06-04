"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
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
from app.config.ui_state import UiStateStore
from app.gui import commands, strings
from app.gui.chrome import ChromeController
from app.gui.commands import Command
from app.gui.controls import OperationBar
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.field_actions import FieldActions
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_actions import PageActions
from app.gui.page_view import PageView
from app.gui.search_actions import SearchActions
from app.pdf.renamer import rename_document

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
    ("Ctrl+F", commands.SEARCH_PDF),
    ("Ctrl+Shift+F", commands.SEARCH_FIELDS),
    ("Ctrl+Shift+H", commands.CLEAR_HIGHLIGHTS),
)
_PALETTE_CHORD = "Ctrl+Shift+P"


class MainWindow(QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._runner = GuiOperationRunner(settings)
        self._recent = RecentFilesStore(settings.recent_file)
        self._ui_state = UiStateStore(settings.ui_state_file)
        self._source: Path | None = None

        self._page_view = PageView()
        self._bar = OperationBar()
        self._edit_bar = EditBar()
        self._controller = EditController(self._page_view)
        self._field_actions = FieldActions(self, self._page_view, self._controller)
        self._search_actions = SearchActions(
            self, self._page_view, self._controller, self._edit_bar, lambda: self._source
        )
        self._page_actions = PageActions(
            self, self._page_view, self._runner, lambda: self._source, self.open_pdf, self._report
        )
        self._page_view.page_changed.connect(self._bar.set_page_label)

        self._bar.prev_requested.connect(self._page_view.show_prev)
        self._bar.next_requested.connect(self._page_view.show_next)
        self._bar.swap_requested.connect(self._page_actions.swap)
        self._bar.delete_page_requested.connect(self._page_actions.delete_current_page)
        self._bar.delete_range_requested.connect(self._page_actions.delete_page_range)
        self._bar.merge_folder_requested.connect(self._page_actions.merge_folder)

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
        self._chrome = ChromeController(self.menuBar(), self._bar, self._edit_bar, self._ui_state)
        self._chrome.apply_saved()
        self.resize(800, 900)

    # --- accessors used by the command registry -----------------------------

    @property
    def page_view(self) -> PageView:
        return self._page_view

    @property
    def controller(self) -> EditController:
        return self._controller

    @property
    def field_actions(self) -> FieldActions:
        return self._field_actions

    @property
    def search_actions(self) -> SearchActions:
        return self._search_actions

    @property
    def page_actions(self) -> PageActions:
        return self._page_actions

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

    def rename_file(self) -> None:
        """Rename the open PDF (and its sidecar) and reopen under the new name."""
        if self._source is None:
            return
        name, ok = QInputDialog.getText(
            self, strings.DIALOG_RENAME_TITLE, strings.PROMPT_RENAME, text=self._source.name
        )
        if not ok or not name.strip():
            return
        target = self._source.with_name(name.strip())
        if target.suffix == "":
            target = target.with_suffix(self._source.suffix)
        self._controller.flush()
        try:
            rename_document(self._source, target)
        except (OSError, ValueError) as err:
            self._report(OpResult(False, str(err)))
            return
        self.open_pdf(target)
        self._report(OpResult(True, strings.MSG_RENAMED_FMT.format(name=target.name)))

    # --- window chrome ------------------------------------------------------

    def toggle_menu_bar(self) -> None:
        """Show/hide the top menu bar (remembered across sessions)."""
        self._chrome.toggle_menu()

    def toggle_toolbar(self) -> None:
        """Show/hide the button toolbars (remembered across sessions)."""
        self._chrome.toggle_toolbar()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Persist pending edits and UI state before the window closes."""
        self._controller.flush()
        self._chrome.save()
        super().closeEvent(event)

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

    def _report(self, result: OpResult) -> None:
        if result.ok:
            QMessageBox.information(self, strings.DIALOG_SUCCESS_TITLE, result.message)
        else:
            QMessageBox.critical(self, strings.DIALOG_ERROR_TITLE, result.message)
