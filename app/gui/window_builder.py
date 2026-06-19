"""Builds and wires the main window's collaborators.

Extracted from :class:`MainWindow.__init__` so the window file stays a thin
public-API coordinator under the 300-line cap. :func:`assemble` constructs every
sub-controller / action, lays out the central widget, and installs menus,
shortcuts, and signal connections onto the window.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.config.command_history import CommandHistoryStore
from app.config.document_page import DocumentPageStore
from app.config.document_zoom import DocumentZoomStore
from app.config.image_choice_settings import ImageChoiceStore
from app.config.key_bindings import KeyBindingStore, effective_keymap
from app.config.outline_settings import OutlineSettingsStore
from app.config.palette_settings import PaletteSettingsStore
from app.config.placement_settings import PlacementStore
from app.config.recent_files import RecentFilesStore
from app.config.record_store import RecordStore
from app.config.settings import Settings
from app.config.ui_state import UiStateStore
from app.config.window_geometry import WindowGeometryStore
from app.config.zoom_settings import ZoomSettingsStore
from app.gui import commands, strings
from app.gui.chrome import ChromeController
from app.gui.controls import OperationBar
from app.gui.default_app_actions import DefaultAppActions
from app.gui.deferred_ops import DeferredOps
from app.gui.document_actions import DocumentActions
from app.gui.document_memory_controller import (
    DocumentMemoryController,
    DocumentMemoryGroup,
    MemoryStrings,
)
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.export_actions import ExportActions
from app.gui.field_actions import FieldActions
from app.gui.image_actions import ImageActions
from app.gui.image_controller import ImageController
from app.gui.keybinding_actions import KeybindingActions
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.move_actions import MoveActions
from app.gui.operations import GuiOperationRunner
from app.gui.outline_controller import OutlineController
from app.gui.outline_style import OutlineStyle, set_active
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
from app.gui.window_input import (
    build_file_menu,
    default_shortcut_pairs,
    install_control_signals,
    install_shortcuts,
)
from app.gui.working_document import WorkingDocument
from app.gui.zoom_settings_controller import ZoomSettingsController
from app.storage.factory import make_backend

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def assemble(window: MainWindow, settings: Settings) -> None:
    """Construct, lay out, and wire every collaborator onto ``window``."""
    _build_core(window, settings)
    _build_overlay(window, settings)
    _build_operations(window)
    install_control_signals(window)
    _lay_out(window)
    _finish(window, settings)


def _build_core(window: MainWindow, settings: Settings) -> None:
    window._backend = make_backend(settings.database_url)
    backend = window._backend
    window._runner = GuiOperationRunner(settings)
    window._recent = RecentFilesStore(backend)
    window._ui_state = UiStateStore(backend)
    window._palette = PaletteController(window, PaletteSettingsStore(backend))
    window._command_history = CommandHistoryStore(backend)
    window._geometry = WindowGeometryController(window, WindowGeometryStore(backend))
    window._working_doc = WorkingDocument(settings)
    window._page_view = PageView()
    window._zoom_settings = ZoomSettingsController(
        window, ZoomSettingsStore(backend), window._page_view
    )
    outline_holder = OutlineStyle()
    set_active(outline_holder)
    window._outline = OutlineController(
        window,
        OutlineSettingsStore(backend),
        outline_holder,
        lambda: window._page_view.graphics_scene().update(),
    )
    window._bar = OperationBar()
    window._edit_bar = EditBar()
    window._mode_bar = ModeStatusBar()
    window._save = SaveController(
        window,
        window._working_doc,
        window._mode_bar,
        window._report,
        lambda: window._controller.flush(),
    )


def _build_overlay(window: MainWindow, settings: Settings) -> None:
    window._controller = EditController(window._page_view, window._save.mark_dirty)
    window._images = ImageController(
        window._page_view, window._controller.store, window._controller.schedule_autosave
    )
    window._controller.attach_images(window._images)
    window._placement = PlacementController(
        window, window._page_view, window._mode_bar, PlacementStore(window._backend)
    )
    window._field_actions = FieldActions(window, window._page_view, window._controller)
    window._image_actions = ImageActions(
        window,
        window._images,
        window._placement,
        ImageChoiceStore(window._backend),
        window._original_dir,
        window._report,
    )
    window._overlay_actions = OverlayActions(
        window._edit_bar,
        window._controller,
        window._placement,
        window._image_actions,
        window.has_document,
    )
    _build_document_memory(window)
    window._remembered = RememberedSettingsController(
        window, _remembered_stores(window, settings), window._report
    )


def _build_document_memory(window: MainWindow) -> None:
    """Construct the per-document zoom and page memory controllers."""
    pv = window._page_view

    def apply_global_zoom() -> None:
        default = window._zoom_settings.current()
        pv.set_default_zoom(default.fit, default.percent)

    window._doc_zoom = DocumentMemoryController(
        window,
        DocumentZoomStore(window._backend),
        lambda: window._source,
        pv.current_zoom,
        lambda zoom: pv.set_default_zoom(zoom.fit, zoom.percent),
        window._report,
        MemoryStrings.for_noun(strings.DOC_MEM_NOUN_ZOOM),
        fallback=apply_global_zoom,
    )
    window._doc_page = DocumentMemoryController(
        window,
        DocumentPageStore(window._backend),
        lambda: window._source,
        pv.current_page_index,
        pv.go_to_page,
        window._report,
        MemoryStrings.for_noun(strings.DOC_MEM_NOUN_PAGE),
    )
    window._doc_memories = DocumentMemoryGroup([window._doc_zoom, window._doc_page])


def _build_operations(window: MainWindow) -> None:
    window._export = ExportActions(
        window,
        window._controller,
        window._working_doc,
        window._save,
        window._page_view,
        window._report,
    )
    window._search_actions = SearchActions(
        window,
        window._page_view,
        window._controller,
        window._edit_bar,
        window._working_doc.working,
    )
    window._deferred = DeferredOps(
        window._runner,
        window._page_view,
        window._working_doc.working,
        window._save.mark_dirty,
        window._report,
    )
    window._page_actions = PageActions(
        window,
        window._deferred,
        window._runner,
        window.open_pdf,
        window._report,
        window._working_doc.original,
    )
    window._rotate_actions = RotateActions(window._deferred)
    window._move_actions = MoveActions(window._deferred)
    window._print_actions = PrintActions(window, window._working_doc.working)
    window._default_app_actions = DefaultAppActions(window)


def _lay_out(window: MainWindow) -> None:
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(window._bar)
    layout.addWidget(window._edit_bar)
    layout.addWidget(window._page_view, 1)
    layout.addWidget(window._mode_bar)
    window.setCentralWidget(central)


def _finish(window: MainWindow, settings: Settings) -> None:
    window.setWindowTitle(strings.WINDOW_TITLE)
    window._registry = commands.build_commands(window)
    window._document_actions = DocumentActions(
        window,
        window._recent,
        window._controller,
        window._save,
        lambda: window._source,
        window.open_pdf,
        window._report,
    )
    defaults = default_shortcut_pairs()
    window._key_bindings = KeyBindingStore(window._backend)
    window._keymap = effective_keymap(window._key_bindings, defaults)
    window._palette_actions = PaletteActions(
        window, window._registry, window._palette, window._command_history, window.current_keymap
    )
    build_file_menu(window)
    window._shortcut_installer = install_shortcuts(window, window._registry, window._keymap)
    window._keybinding_actions = KeybindingActions(
        window,
        window._registry,
        window._palette,
        window._key_bindings,
        defaults,
        window.apply_keymap,
        window._report,
    )
    window._chrome = ChromeController(
        window.menuBar(), window._bar, window._edit_bar, window._mode_bar, window._ui_state
    )
    window._chrome.apply_saved()
    window._geometry.restore()


def _remembered_stores(window: MainWindow, settings: Settings) -> list[RecordStore]:
    """The remembered-setting stores offered by the Remembered-settings command."""
    backend = window._backend
    return [
        window._recent,
        window._ui_state,
        PaletteSettingsStore(backend),
        window._command_history,
        PlacementStore(backend),
        WindowGeometryStore(backend),
        ImageChoiceStore(backend),
        OutlineSettingsStore(backend),
        ZoomSettingsStore(backend),
        KeyBindingStore(backend),
        DocumentZoomStore(backend),
        DocumentPageStore(backend),
    ]
