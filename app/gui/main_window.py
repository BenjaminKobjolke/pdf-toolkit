"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.config.command_history import CommandHistoryStore
from app.config.palette_settings import PaletteSettingsStore
from app.config.placement_settings import PlacementStore
from app.config.recent_files import RecentFilesStore
from app.config.settings import Settings
from app.config.ui_state import UiStateStore
from app.config.window_geometry import WindowGeometryStore
from app.gui import commands, strings
from app.gui.chrome import ChromeController
from app.gui.controls import OperationBar
from app.gui.deferred_ops import DeferredOps
from app.gui.document_actions import DocumentActions
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.export_actions import ExportActions
from app.gui.field_actions import FieldActions
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.move_actions import MoveActions
from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_actions import PageActions
from app.gui.page_view import PageView
from app.gui.palette_actions import PaletteActions
from app.gui.palette_controller import PaletteController
from app.gui.placement import PlacementController
from app.gui.rotate_actions import RotateActions
from app.gui.save_controller import SaveController
from app.gui.search_actions import SearchActions
from app.gui.window_geometry_controller import WindowGeometryController
from app.gui.window_input import build_file_menu, install_shortcuts
from app.gui.working_document import WorkingDocument


class MainWindow(QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._runner = GuiOperationRunner(settings)
        self._recent = RecentFilesStore(settings.recent_file)
        self._ui_state = UiStateStore(settings.ui_state_file)
        self._palette = PaletteController(self, PaletteSettingsStore(settings.palette_file))
        self._command_history = CommandHistoryStore(settings.command_history_file)
        self._geometry = WindowGeometryController(self, WindowGeometryStore(settings.window_file))
        self._working_doc = WorkingDocument(settings)
        self._source: Path | None = None

        self._page_view = PageView()
        self._bar = OperationBar()
        self._edit_bar = EditBar()
        self._mode_bar = ModeStatusBar()
        self._save = SaveController(
            self, self._working_doc, self._mode_bar, self._report, lambda: self._controller.flush()
        )
        self._controller = EditController(self._page_view, self._save.mark_dirty)
        self._placement = PlacementController(
            self,
            self._page_view,
            self._controller,
            self._mode_bar,
            PlacementStore(settings.placement_file),
        )
        self._field_actions = FieldActions(self, self._page_view, self._controller)
        self._export = ExportActions(
            self, self._controller, self._working_doc, self._save, self._page_view, self._report
        )
        self._page_view.edit_text_requested.connect(self._field_actions.change_text)
        self._search_actions = SearchActions(
            self, self._page_view, self._controller, self._edit_bar, self._working_doc.working
        )
        self._deferred = DeferredOps(
            self._runner,
            self._page_view,
            self._working_doc.working,
            self._save.mark_dirty,
            self._report,
        )
        self._page_actions = PageActions(
            self, self._deferred, self._runner, self.open_pdf, self._report
        )
        self._rotate_actions = RotateActions(self._deferred)
        self._move_actions = MoveActions(self._deferred)
        self._page_view.page_changed.connect(self._bar.set_page_label)
        self._page_view.page_changed.connect(self._mode_bar.set_page_label)

        self._bar.prev_requested.connect(self._page_view.show_prev)
        self._bar.next_requested.connect(self._page_view.show_next)
        self._bar.swap_requested.connect(self._page_actions.swap)
        self._bar.delete_page_requested.connect(self._page_actions.delete_current_page)
        self._bar.delete_range_requested.connect(self._page_actions.delete_page_range)
        self._bar.merge_folder_requested.connect(self._page_actions.merge_folder)

        self._edit_bar.edit_mode_toggled.connect(self._controller.set_edit_mode)
        self._edit_bar.edit_mode_toggled.connect(self._mode_bar.set_edit_mode)
        self._edit_bar.add_field_requested.connect(self.add_text_field)
        self._edit_bar.delete_field_requested.connect(self._controller.delete_selected)
        self._edit_bar.style_changed.connect(self._controller.apply_style)
        self._edit_bar.export_text_requested.connect(self.export_text)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._bar)
        layout.addWidget(self._edit_bar)
        layout.addWidget(self._page_view, 1)
        layout.addWidget(self._mode_bar)
        self.setCentralWidget(central)

        self.setWindowTitle(strings.WINDOW_TITLE)
        self._registry = commands.build_commands(self)
        self._document_actions = DocumentActions(
            self,
            self._recent,
            self._controller,
            self._save,
            lambda: self._source,
            self.open_pdf,
            self._report,
        )
        self._palette_actions = PaletteActions(
            self, self._registry, self._palette, self._command_history
        )
        build_file_menu(self)
        install_shortcuts(self, self._registry)
        self._chrome = ChromeController(
            self.menuBar(), self._bar, self._edit_bar, self._mode_bar, self._ui_state
        )
        self._chrome.apply_saved()
        self._geometry.restore()

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

    @property
    def rotate_actions(self) -> RotateActions:
        return self._rotate_actions

    @property
    def move_actions(self) -> MoveActions:
        return self._move_actions

    @property
    def palette_controller(self) -> PaletteController:
        return self._palette

    def has_document(self) -> bool:
        return self._source is not None

    def open_pdf(self, path: Path | None = None) -> None:
        """Open ``path`` (or prompt for one) into a working copy and show page 1."""
        if not self._save.confirm_unsaved():
            return
        if path is None:
            chosen, _ = QFileDialog.getOpenFileName(
                self, strings.DIALOG_OPEN_TITLE, "", strings.FILE_FILTER_PDF
            )
            if not chosen:
                return
            path = Path(chosen)
        self._source = path
        working = self._working_doc.open(path)
        # Load saved fields before rendering so the first page_changed restores
        # them onto the page (fields show whether or not edit mode is on). The
        # sidecar is keyed to the working copy, seeded from the original on open.
        self._load_text_fields(working)
        self._page_view.load(working)
        self._bar.set_enabled_for_doc(True)
        self._mode_bar.set_dirty(False)
        self._recent.add(path)
        self.setWindowTitle(f"{strings.WINDOW_TITLE} — {path.name}")

    def open_from_history(self) -> None:
        self._document_actions.open_from_history()

    def close_document(self) -> None:
        """Offer to save pending changes, then return to the empty viewer state."""
        if not self._save.confirm_unsaved():
            return
        self._working_doc.close()
        self._page_view.reset()
        self._bar.set_enabled_for_doc(False)
        self._mode_bar.clear_page_label()
        self._mode_bar.set_dirty(False)
        if self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()
        self._source = None
        self.setWindowTitle(strings.WINDOW_TITLE)

    def exit_app(self) -> None:
        self.close()

    def save_changes(self) -> None:
        """Write the working copy's changes back to the original file (with a backup)."""
        self._save.save()

    def open_command_palette(self) -> None:
        self._palette_actions.open_commands()

    def show_keyboard_shortcuts(self) -> None:
        self._palette_actions.show_shortcuts()

    def toggle_edit_mode(self) -> None:
        self._edit_bar.toggle_edit_mode()

    def add_text_field(self) -> None:
        """Add a text field, entering edit mode first if needed (palette/button)."""
        if self._source is None:
            return
        if not self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()  # syncs toolbar + controller + footer
        self._placement.choose_and_place()

    def export_text(self) -> None:
        """Flatten placed text fields: overwrite the original or write a new file."""
        self._export.export()

    def delete_saved_text_fields(self) -> None:
        self._document_actions.delete_saved_text_fields()

    def rename_file(self) -> None:
        self._document_actions.rename_file()

    def toggle_menu_bar(self) -> None:
        """Show/hide the top menu bar (remembered across sessions)."""
        self._chrome.toggle_menu()

    def toggle_toolbar(self) -> None:
        """Show/hide the button toolbars (remembered across sessions)."""
        self._chrome.toggle_toolbar()

    def toggle_statusbar(self) -> None:
        """Show/hide the mode footer bar (remembered across sessions)."""
        self._chrome.toggle_statusbar()

    def toggle_fullscreen(self) -> None:
        """Flip fullscreen for the current session (not remembered across runs)."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Confirm unsaved changes, then persist UI + window state before closing."""
        if not self._save.confirm_unsaved():
            event.ignore()
            return
        self._working_doc.close()
        self._chrome.save()
        self._geometry.save()
        super().closeEvent(event)

    def _load_text_fields(self, path: Path) -> None:
        try:
            self._controller.on_document_loaded(path)
        except ValueError as err:
            QMessageBox.warning(
                self,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_SIDECAR_LOAD_FAILED_FMT.format(error=err),
            )

    def _report(self, result: OpResult) -> None:
        if result.ok:
            QMessageBox.information(self, strings.DIALOG_SUCCESS_TITLE, result.message)
        else:
            QMessageBox.critical(self, strings.DIALOG_ERROR_TITLE, result.message)
