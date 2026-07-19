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
    from app.gui import field_actions as field_actions_mod
    from app.gui import file_actions as file_actions_mod
    from app.gui import image_actions as image_actions_mod
    from app.gui import image_controller as image_controller_mod
    from app.gui import layer_actions as layer_actions_mod
    from app.gui import move_actions as move_actions_mod
    from app.gui import overlay_actions as overlay_actions_mod
    from app.gui import page_actions as page_actions_mod
    from app.gui import print_actions as print_actions_mod
    from app.gui import rect_actions as rect_actions_mod
    from app.gui import rect_controller as rect_controller_mod
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
    from app.gui.instance_controller import InstanceController
    from app.gui.keybinding_actions import KeybindingActions
    from app.gui.lifecycle_actions import LifecycleActions
    from app.gui.link_hint_controller import LinkHintController
    from app.gui.link_hint_settings_controller import LinkHintSettingsController
    from app.gui.mode_status_bar import ModeStatusBar
    from app.gui.operations import GuiOperationRunner
    from app.gui.outline_controller import OutlineController
    from app.gui.page_view import PageView
    from app.gui.palette_actions import PaletteActions
    from app.gui.palette_controller import PaletteController
    from app.gui.placement import PlacementController
    from app.gui.reload_controller import ReloadController
    from app.pdf.file_format import FileFormat

if TYPE_CHECKING:
    from app.gui import rotate_actions as rotate_actions_mod
    from app.gui.open_filter_controller import OpenFilterController
    from app.gui.remembered_settings import RememberedSettingsController
    from app.gui.save_controller import SaveController
    from app.gui.search_actions import SearchActions
    from app.gui.select_controller import SelectController
    from app.gui.shortcut_installer import ShortcutInstaller
    from app.gui.text_view_controller import TextViewController
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
    _text_view: TextViewController
    _open_filter: OpenFilterController
    _instance: InstanceController
    _reload: ReloadController
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
    _images: image_controller_mod.ImageController
    _rects: rect_controller_mod.RectController
    _select: SelectController
    _link_hints: LinkHintController
    _link_hint_settings: LinkHintSettingsController
    _placement: PlacementController
    _field_actions: field_actions_mod.FieldActions
    _image_actions: image_actions_mod.ImageActions
    _rect_actions: rect_actions_mod.RectActions
    _layer_actions: layer_actions_mod.LayerActions
    _overlay_actions: overlay_actions_mod.OverlayActions
    _doc_zoom: DocumentMemoryController[Any]
    _doc_page: DocumentMemoryController[Any]
    _doc_memories: DocumentMemoryGroup
    _remembered: RememberedSettingsController
    _export: ExportActions
    _search_actions: SearchActions
    _deferred: DeferredOps
    _page_actions: page_actions_mod.PageActions
    _rotate_actions: rotate_actions_mod.RotateActions
    _move_actions: move_actions_mod.MoveActions
    _print_actions: print_actions_mod.PrintActions
    _default_app_actions: DefaultAppActions
    _file_actions: file_actions_mod.FileActions
    _registry: list[Command]
    _document_actions: DocumentActions
    _palette_actions: PaletteActions
    _key_bindings: KeyBindingStore
    _keymap: KeyMap
    _shortcut_installer: ShortcutInstaller
    _keybinding_actions: KeybindingActions
    _chrome: ChromeController
    _lifecycle: LifecycleActions
    _source: Path | None

    @property
    def page_view(self) -> PageView:
        return self._page_view

    @property
    def controller(self) -> EditController:
        return self._controller

    @property
    def images(self) -> image_controller_mod.ImageController:
        return self._images

    @property
    def rects(self) -> rect_controller_mod.RectController:
        return self._rects

    @property
    def select_controller(self) -> SelectController:
        return self._select

    @property
    def link_hint_controller(self) -> LinkHintController:
        return self._link_hints

    @property
    def link_hint_settings(self) -> LinkHintSettingsController:
        return self._link_hint_settings

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
    def field_actions(self) -> field_actions_mod.FieldActions:
        return self._field_actions

    @property
    def image_actions(self) -> image_actions_mod.ImageActions:
        return self._image_actions

    @property
    def rect_actions(self) -> rect_actions_mod.RectActions:
        return self._rect_actions

    @property
    def layer_actions(self) -> layer_actions_mod.LayerActions:
        return self._layer_actions

    @property
    def search_actions(self) -> SearchActions:
        return self._search_actions

    @property
    def page_actions(self) -> page_actions_mod.PageActions:
        return self._page_actions

    @property
    def rotate_actions(self) -> rotate_actions_mod.RotateActions:
        return self._rotate_actions

    @property
    def move_actions(self) -> move_actions_mod.MoveActions:
        return self._move_actions

    @property
    def print_actions(self) -> print_actions_mod.PrintActions:
        return self._print_actions

    @property
    def default_app_actions(self) -> DefaultAppActions:
        return self._default_app_actions

    @property
    def document_actions(self) -> DocumentActions:
        return self._document_actions

    @property
    def file_actions(self) -> file_actions_mod.FileActions:
        return self._file_actions

    @property
    def palette_controller(self) -> PaletteController:
        return self._palette

    @property
    def outline_controller(self) -> OutlineController:
        return self._outline

    @property
    def text_view_controller(self) -> TextViewController:
        return self._text_view

    @property
    def open_filter_controller(self) -> OpenFilterController:
        return self._open_filter

    @property
    def instance_controller(self) -> InstanceController:
        return self._instance

    @property
    def reload_controller(self) -> ReloadController:
        return self._reload

    @property
    def zoom_settings_controller(self) -> ZoomSettingsController:
        return self._zoom_settings

    def has_document(self) -> bool:
        return self._source is not None

    def current_format(self) -> FileFormat | None:
        """The format of the open document, or ``None`` when none is open."""
        from app.pdf.file_format import FileFormat

        return FileFormat.of(self._source)
