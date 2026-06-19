"""Typed collaborator attributes and their read-only accessors for MainWindow.

Mixed into :class:`~app.gui.main_window.MainWindow`. The attributes are assigned
by :func:`app.gui.window_builder.assemble`; they are declared here so the public
API (and the type checker) can see them. Split out of ``main_window`` so that
file stays a thin action coordinator under the file-length cap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from app.config.command_history import CommandHistoryStore
    from app.config.key_bindings import KeyBindingStore, KeyMap
    from app.config.recent_files import RecentFilesStore
    from app.config.ui_state import UiStateStore
    from app.gui.chrome import ChromeController
    from app.gui.commands import Command
    from app.gui.controls import OperationBar
    from app.gui.default_app_actions import DefaultAppActions
    from app.gui.deferred_ops import DeferredOps
    from app.gui.document_actions import DocumentActions
    from app.gui.document_memory_controller import (
        DocumentMemoryController,
        DocumentMemoryGroup,
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
    from app.gui.shortcut_installer import ShortcutInstaller
    from app.gui.window_geometry_controller import WindowGeometryController
    from app.gui.working_document import WorkingDocument
    from app.gui.zoom_settings_controller import ZoomSettingsController
    from app.storage.backend import StorageBackend


class CollaboratorAccessors:
    """The window's collaborators (assigned by ``assemble``) and their accessors."""

    _backend: StorageBackend
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
    _doc_zoom: DocumentMemoryController[Any]
    _doc_page: DocumentMemoryController[Any]
    _doc_memories: DocumentMemoryGroup
    _remembered: RememberedSettingsController
    _export: ExportActions
    _search_actions: SearchActions
    _deferred: DeferredOps
    _page_actions: PageActions
    _rotate_actions: RotateActions
    _move_actions: MoveActions
    _print_actions: PrintActions
    _default_app_actions: DefaultAppActions
    _registry: list[Command]
    _document_actions: DocumentActions
    _palette_actions: PaletteActions
    _key_bindings: KeyBindingStore
    _keymap: KeyMap
    _shortcut_installer: ShortcutInstaller
    _keybinding_actions: KeybindingActions
    _chrome: ChromeController
    _source: Path | None

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
    def default_app_actions(self) -> DefaultAppActions:
        return self._default_app_actions

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
