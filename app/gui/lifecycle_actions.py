"""Document lifecycle: open, sibling/directory navigation, close, and shutdown.

Bundles the collaborators the open/close/shutdown flows touch (per "objects for
related values", mirroring :class:`app.gui.deferred_ops.DeferredOps`) so
:class:`MainWindow` stays a thin delegating coordinator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.gui import confirm_dialog, file_browser_model, file_dialogs, strings
from app.pdf.file_format import FileFormat

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from app.config.recent_files import RecentFilesStore
    from app.gui.chrome import ChromeController
    from app.gui.controls import OperationBar
    from app.gui.document_memory_controller import DocumentMemoryGroup
    from app.gui.edit_bar import EditBar
    from app.gui.edit_controller import EditController
    from app.gui.gif_controller import GifController
    from app.gui.image_controller import ImageController
    from app.gui.mode_status_bar import ModeStatusBar
    from app.gui.open_filter_controller import OpenFilterController
    from app.gui.page_view import PageView
    from app.gui.reload_controller import ReloadController
    from app.gui.save_controller import SaveController
    from app.gui.window_geometry_controller import WindowGeometryController
    from app.gui.working_document import WorkingDocument
    from app.storage.backend import StorageBackend


@dataclass(frozen=True)
class LifecycleActions:
    """Open, close, and shut down documents on behalf of the main window."""

    parent: QWidget
    save: SaveController
    open_filter: OpenFilterController
    doc_memories: DocumentMemoryGroup
    working_doc: WorkingDocument
    controller: EditController
    images: ImageController
    gif: GifController
    page_view: PageView
    bar: OperationBar
    mode_bar: ModeStatusBar
    edit_bar: EditBar
    recent: RecentFilesStore
    reload: ReloadController
    chrome: ChromeController
    geometry: WindowGeometryController
    backend: StorageBackend
    source: Callable[[], Path | None]
    set_source: Callable[[Path | None], None]
    set_title: Callable[[str], None]
    # Runs after a document is opened or closed; lets an alternate view (the
    # thumbnails grid) dismiss itself so it never covers a fresh document.
    after_open: Callable[[], None] = lambda: None

    def open_pdf(self, path: Path | None = None) -> None:
        """Open ``path`` (or prompt for one) into a working copy and show page 1."""
        if not self.save.confirm_unsaved():
            return
        if path is None:
            current = self.source()
            chosen = file_dialogs.prompt_open_file(
                self.parent,
                strings.DIALOG_OPEN_TITLE,
                self.open_filter.current_filter(),
                current.parent if current else None,
            )
            if chosen is None:
                return
            path = chosen
        # Boundary: reject a format the viewer can't render (e.g. a path passed on
        # the command line) instead of handing it to fitz and failing obscurely.
        doc_format = FileFormat.of(path)
        if doc_format is None:
            confirm_dialog.show_message(
                self.parent,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_UNSUPPORTED_FORMAT_FMT.format(name=path.name),
                confirm_dialog.Severity.WARNING,
            )
            return
        # Capture the outgoing document's view state before switching away.
        self.doc_memories.capture(self.source())
        # Release any previous animated GIF first: QMovie holds the working copy
        # open, and working_doc.open() deletes it — which fails on Windows while
        # the file is still open.
        self.gif.on_document_closed()
        # Creating the working copy reads the source (PSD converts to PNG here);
        # a corrupt/unreadable file must warn and abort, not crash the open.
        try:
            working = self.working_doc.open(path)
        except OSError as err:
            confirm_dialog.show_message(
                self.parent,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_OPEN_FAILED_FMT.format(name=path.name, error=err),
                confirm_dialog.Severity.WARNING,
            )
            return
        self.set_source(path)
        # Asset paths resolve against the original PDF's directory, not the temp
        # working copy; set this before rendering so the first restore can load
        # image pixmaps.
        self.controller.set_base_dir(path.parent)
        self.images.set_base_dir(path.parent)
        # Load saved content before rendering so the first page_changed restores
        # it onto the page (it shows whether or not edit mode is on). The sidecar
        # is keyed to the working copy, seeded from the original on open.
        self._load_text_fields(working)
        # Before load: the first page_changed from load() must already know
        # whether this format shows a Page row (PDFs) or a bare file counter.
        self.mode_bar.set_paged_document(doc_format is FileFormat.PDF)
        self.page_view.load(working)
        # Autoplay animated GIFs (no-op for every other format); after load so the
        # static first-frame render is in place before the movie takes over.
        self.gif.on_document_opened(working, doc_format)
        # Restore the remembered zoom/page for this document (independent dimensions).
        self.doc_memories.apply_for(path)
        self.bar.update_for(has_doc=True, is_pdf=doc_format is FileFormat.PDF)
        # ponytail: computed once per open — not refreshed on filter changes or
        # external directory changes while the doc stays open; next open fixes it.
        position = file_browser_model.file_position(path, self.open_filter.current_filter())
        if position is None:
            self.mode_bar.clear_file_label()
        else:
            self.mode_bar.set_file_label(position.index, position.total)
        self.mode_bar.set_dirty(False)
        self.recent.add(path)
        self.reload.on_document_opened(path)
        self.set_title(strings.WINDOW_TITLE_OPEN_FMT.format(path=path))
        self.after_open()

    def open_sibling(self, step: int) -> None:
        """Open the alphabetically adjacent openable file in the document's directory."""
        source = self.source()
        if source is None:
            return
        target = file_browser_model.sibling_file(source, self.open_filter.current_filter(), step)
        self._open_or_hint(target, strings.HINT_NO_SIBLING_FILE)

    def open_sibling_or_close(self) -> None:
        """Open the file nearest the (now deleted) source, else the empty state."""
        source = self.source()
        target = (
            None
            if source is None
            else file_browser_model.nearest_file(source, self.open_filter.current_filter())
        )
        if target is None:
            self.close_document()
        else:
            self.open_pdf(target)

    def open_directory(self) -> None:
        """Browse to a folder and open its first openable file."""
        current = self.source()
        chosen = file_dialogs.prompt_directory(
            self.parent,
            strings.DIALOG_OPEN_DIR_TITLE,
            current.parent if current else None,
        )
        if chosen is None:
            return
        target = file_browser_model.first_openable_file(chosen, self.open_filter.current_filter())
        self._open_or_hint(target, strings.HINT_NO_OPENABLE_FILE)

    def _open_or_hint(self, target: Path | None, hint: str) -> None:
        if target is None:
            self.mode_bar.set_hint(hint)
            return
        self.open_pdf(target)

    def close_document(self) -> None:
        """Offer to save pending changes, then return to the empty viewer state."""
        if not self.save.confirm_unsaved():
            return
        self.doc_memories.capture(self.source())
        self.gif.on_document_closed()
        self.working_doc.close()
        self.page_view.reset()
        self.bar.update_for(has_doc=False, is_pdf=False)
        self.mode_bar.clear_file_label()
        self.mode_bar.clear_page_label()
        self.mode_bar.clear_zoom_label()
        self.mode_bar.set_dirty(False)
        if self.edit_bar.is_edit_mode():
            self.edit_bar.toggle_edit_mode()
        self.reload.on_document_closed()
        self.set_source(None)
        self.set_title(strings.WINDOW_TITLE)
        self.after_open()

    def shutdown(self) -> bool:
        """Confirm unsaved changes, then persist UI + window state; False to veto close."""
        if not self.save.confirm_unsaved():
            return False
        self.doc_memories.capture(self.source())
        self.gif.on_document_closed()
        self.working_doc.close()
        self.chrome.save()
        self.geometry.save()
        self.backend.close()
        return True

    def _load_text_fields(self, path: Path) -> None:
        try:
            self.controller.on_document_loaded(path)
        except ValueError as err:
            confirm_dialog.show_message(
                self.parent,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_SIDECAR_LOAD_FAILED_FMT.format(error=err),
                confirm_dialog.Severity.WARNING,
            )
