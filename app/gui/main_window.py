"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from app.gui import overlay_selection, strings
from app.gui.window_builder import assemble

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent

    from app.config.command_history import CommandHistoryStore
    from app.config.recent_files import RecentFilesStore
    from app.config.settings import Settings
    from app.config.ui_state import UiStateStore
    from app.gui.chrome import ChromeController
    from app.gui.commands import Command
    from app.gui.controls import OperationBar
    from app.gui.deferred_ops import DeferredOps
    from app.gui.document_actions import DocumentActions
    from app.gui.edit_bar import EditBar
    from app.gui.edit_controller import EditController
    from app.gui.export_actions import ExportActions
    from app.gui.field_actions import FieldActions
    from app.gui.image_actions import ImageActions
    from app.gui.image_controller import ImageController
    from app.gui.mode_status_bar import ModeStatusBar
    from app.gui.move_actions import MoveActions
    from app.gui.operations import GuiOperationRunner, OpResult
    from app.gui.outline_controller import OutlineController
    from app.gui.overlay_actions import OverlayActions
    from app.gui.page_actions import PageActions
    from app.gui.page_view import PageView
    from app.gui.palette_actions import PaletteActions
    from app.gui.palette_controller import PaletteController
    from app.gui.placement import PlacementController
    from app.gui.print_actions import PrintActions
    from app.gui.remembered_settings import RememberedSettingsController
    from app.gui.rotate_actions import RotateActions
    from app.gui.save_controller import SaveController
    from app.gui.search_actions import SearchActions
    from app.gui.window_geometry_controller import WindowGeometryController
    from app.gui.working_document import WorkingDocument
    from app.gui.zoom_settings_controller import ZoomSettingsController


class MainWindow(QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators.

    The collaborators below are constructed and assigned by
    :func:`app.gui.window_builder.assemble`; they are declared here so the public
    API (and the type checker) can see them.
    """

    _runner: GuiOperationRunner
    _recent: RecentFilesStore
    _ui_state: UiStateStore
    _palette: PaletteController
    _outline: OutlineController
    _command_history: CommandHistoryStore
    _geometry: WindowGeometryController
    _working_doc: WorkingDocument
    _page_view: PageView
    _zoom_settings: ZoomSettingsController
    _bar: OperationBar
    _edit_bar: EditBar
    _mode_bar: ModeStatusBar
    _save: SaveController
    _controller: EditController
    _images: ImageController
    _placement: PlacementController
    _field_actions: FieldActions
    _image_actions: ImageActions
    _overlay_actions: OverlayActions
    _remembered: RememberedSettingsController
    _export: ExportActions
    _search_actions: SearchActions
    _deferred: DeferredOps
    _page_actions: PageActions
    _rotate_actions: RotateActions
    _move_actions: MoveActions
    _print_actions: PrintActions
    _registry: list[Command]
    _document_actions: DocumentActions
    _palette_actions: PaletteActions
    _chrome: ChromeController

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._source: Path | None = None
        assemble(self, settings)

    @property
    def page_view(self) -> PageView:
        return self._page_view

    @property
    def controller(self) -> EditController:
        return self._controller

    @property
    def images(self) -> ImageController:
        return self._images

    @property
    def operation_bar(self) -> OperationBar:
        return self._bar

    @property
    def edit_bar(self) -> EditBar:
        return self._edit_bar

    @property
    def mode_bar(self) -> ModeStatusBar:
        return self._mode_bar

    @property
    def field_actions(self) -> FieldActions:
        return self._field_actions

    @property
    def image_actions(self) -> ImageActions:
        return self._image_actions

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
    def print_actions(self) -> PrintActions:
        return self._print_actions

    @property
    def palette_controller(self) -> PaletteController:
        return self._palette

    @property
    def outline_controller(self) -> OutlineController:
        return self._outline

    @property
    def zoom_settings_controller(self) -> ZoomSettingsController:
        return self._zoom_settings

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
        # Asset paths resolve against the original PDF's directory, not the temp
        # working copy; set this before rendering so the first restore can load
        # image pixmaps.
        self._controller.set_base_dir(path.parent)
        self._images.set_base_dir(path.parent)
        # Load saved content before rendering so the first page_changed restores
        # it onto the page (it shows whether or not edit mode is on). The sidecar
        # is keyed to the working copy, seeded from the original on open.
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
        self._mode_bar.clear_zoom_label()
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
        self._overlay_actions.add_text_field()

    def add_image(self) -> None:
        """Add an image, entering edit mode first if needed (palette/button)."""
        self._overlay_actions.add_image()

    def select_next_editable(self) -> None:
        """Select the next editable element on the page (enters edit mode first)."""
        self._overlay_actions.ensure_edit_mode()
        overlay_selection.select_adjacent_editable(self._page_view, forward=True)

    def select_previous_editable(self) -> None:
        """Select the previous editable element on the page (enters edit mode first)."""
        self._overlay_actions.ensure_edit_mode()
        overlay_selection.select_adjacent_editable(self._page_view, forward=False)

    def open_remembered_settings(self) -> None:
        """Show the remembered-settings picker to reset stored preferences."""
        self._remembered.open()

    def export_text(self) -> None:
        """Flatten placed overlay: overwrite the original or write a new file."""
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

    def _original_dir(self) -> Path | None:
        original = self._working_doc.original()
        return original.parent if original is not None else None

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
