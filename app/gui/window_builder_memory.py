"""Per-document memory and remembered-settings wiring for the main window.

Extracted from :mod:`app.gui.window_builder` to keep that wiring module under the
300-line cap. Both helpers take the window (and ``settings`` where needed) and set
attributes on it exactly as the inline versions did.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.document_page import DocumentPageStore
from app.config.document_zoom import DocumentZoomStore
from app.config.image_background_settings import ImageBackgroundSettingsStore
from app.config.image_choice_settings import ImageChoiceStore
from app.config.instance_settings import InstanceSettingsStore
from app.config.key_bindings import KeyBindingStore
from app.config.link_hint_settings import LinkHintSettingsStore
from app.config.open_filter_settings import OpenFilterSettingsStore
from app.config.open_with import OpenWithStore
from app.config.outline_settings import OutlineSettingsStore
from app.config.palette_settings import PaletteSettingsStore
from app.config.placement_settings import PlacementStore
from app.config.record_store import RecordStore
from app.config.reload_settings import ReloadSettingsStore
from app.config.settings import Settings
from app.config.status_bar_settings import StatusBarSettingsStore
from app.config.text_view_settings import TextViewSettingsStore
from app.config.thumbnail_settings import ThumbnailSettingsStore
from app.config.window_geometry import WindowGeometryStore
from app.config.zoom_settings import ZoomSettingsStore
from app.gui import settings_strings
from app.gui.document_memory_controller import (
    DocumentMemoryController,
    DocumentMemoryGroup,
    MemoryHooks,
    MemoryStrings,
)

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def build_document_memory(window: MainWindow) -> None:
    """Construct the per-document zoom and page memory controllers."""
    pv = window._page_view

    def apply_global_zoom() -> None:
        default = window._zoom_settings.current()
        pv.set_default_zoom(default.fit, default.percent)

    window._doc_zoom = DocumentMemoryController(
        window,
        DocumentZoomStore(window._backend),
        MemoryHooks(
            current_path=lambda: window._source,
            capture_value=pv.current_zoom,
            apply_value=lambda zoom: pv.set_default_zoom(zoom.fit, zoom.percent),
            report=window._report,
            fallback=apply_global_zoom,
        ),
        MemoryStrings.for_noun(settings_strings.DOC_MEM_NOUN_ZOOM),
    )
    window._doc_page = DocumentMemoryController(
        window,
        DocumentPageStore(window._backend),
        MemoryHooks(
            current_path=lambda: window._source,
            capture_value=pv.current_page_index,
            apply_value=pv.go_to_page,
            report=window._report,
        ),
        MemoryStrings.for_noun(settings_strings.DOC_MEM_NOUN_PAGE),
    )
    window._doc_memories = DocumentMemoryGroup([window._doc_zoom, window._doc_page])


def remembered_stores(window: MainWindow, settings: Settings) -> list[RecordStore]:
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
        TextViewSettingsStore(backend),
        StatusBarSettingsStore(backend),
        ImageBackgroundSettingsStore(backend),
        OpenFilterSettingsStore(backend),
        OpenWithStore(backend),
        InstanceSettingsStore(backend),
        ReloadSettingsStore(backend),
        LinkHintSettingsStore(backend),
        ThumbnailSettingsStore(backend),
        ZoomSettingsStore(backend),
        KeyBindingStore(backend),
        DocumentZoomStore(backend),
        DocumentPageStore(backend),
    ]
