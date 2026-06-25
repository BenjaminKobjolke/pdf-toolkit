"""Owns the overlay editing model: per-page specs, autosave, and export.

This controller plus the shared :class:`PageItemStore` are the source of truth
across pages (the view holds only on-screen items). It owns text fields directly,
delegates images/rects to satellite controllers, and is the single persistence
owner: one autosave timer writes every kind to the JSON sidecar; one flatten bakes
them onto the PDF. ``_source`` is the working copy; ``_base_dir`` is the original
PDF's directory (where relative asset paths resolve).
"""

from __future__ import annotations

import contextlib
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer

from app.gui import strings, text_style
from app.gui.image_controller import ImageController
from app.gui.operations import OpResult
from app.gui.overlay_selection import place_new_item
from app.gui.page_item_store import PageItemStore
from app.gui.page_view import PageView
from app.gui.rect_controller import RectController
from app.gui.text_item import TextFieldItem
from app.gui.text_style import TextStyle
from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_overlay import apply_overlay

log = logging.getLogger("pdf_toolkit")

_AUTOSAVE_MS = 400


@dataclass(frozen=True)
class FieldHit:
    """A text-field search match: its page, position in that page, and text."""

    page_index: int
    field_index: int
    text: str


class EditController:
    """Coordinates overlay editing between the page view and persistence."""

    def __init__(self, page_view: PageView, mark_dirty: Callable[[], None] = lambda: None) -> None:
        self._page_view = page_view
        self._mark_dirty = mark_dirty
        self._source: Path | None = None
        self._base_dir: Path | None = None
        self._store = PageItemStore()
        # Satellites (images, rects) share this store + timer; driven generically.
        self._satellites: list[ImageController | RectController] = []
        self._edit_mode = False
        self._style = text_style.DEFAULT_STYLE

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(_AUTOSAVE_MS)
        self._timer.timeout.connect(self._save)

        page_view.page_will_change.connect(self._harvest_page)
        page_view.page_changed.connect(self._on_page_shown)
        page_view.delete_requested.connect(self.delete_selected)
        page_view.graphics_scene().changed.connect(self._on_scene_changed)

    # --- wiring -------------------------------------------------------------

    @property
    def store(self) -> PageItemStore:
        """The shared store, so the image controller persists into the same doc."""
        return self._store

    def attach_images(self, images: ImageController) -> None:
        """Register the image controller this controller persists alongside text."""
        self._satellites.append(images)

    def attach_rects(self, rects: RectController) -> None:
        """Register the rect controller this controller persists alongside text."""
        self._satellites.append(rects)

    def set_base_dir(self, base_dir: Path) -> None:
        """Set the original PDF's directory (asset paths + flatten resolve here)."""
        self._base_dir = base_dir

    def schedule_autosave(self) -> None:
        """Public autosave trigger, shared with the image controller."""
        self._schedule_autosave()

    # --- public API ---------------------------------------------------------

    def on_document_loaded(self, pdf: Path) -> None:
        """Load the sidecar for ``pdf``. Content shows whether editing or not.

        Call before the page view renders; the resulting ``page_changed`` signal
        restores this page. Raises ``ValueError`` on a malformed sidecar.
        """
        self._edit_mode = False
        self._store.clear()
        for satellite in self._satellites:
            satellite.reset_edit_mode()
        try:
            doc = load_sidecar(pdf)
        finally:
            self._source = pdf  # set even on failure so stale specs are dropped
        self._store.load(doc)

    def set_edit_mode(self, on: bool) -> None:
        """Toggle whether the (always-visible) fields can be moved/edited."""
        if not on:
            self._harvest_page(self._page_view.current_page_index())
        self._edit_mode = on
        for item in self._page_view.text_items():
            item.set_editable(on)

    def add_field(self, anchor: QPointF | None = None, *, centered: bool = False) -> None:
        """Add a new text field (edit mode only).

        ``anchor`` (scene px): ``None`` = top-left default; else placed at — or
        centred on, when ``centered`` — ``anchor``.
        """
        if not self._edit_mode or self._source is None:
            return
        item = TextFieldItem()
        text_style.apply_style(item, self._style)
        place_new_item(
            self._page_view, item, anchor, centered=centered, add=self._page_view.add_text_item
        )
        self._schedule_autosave()

    def delete_selected(self) -> None:
        """Remove the selected text fields from the current page (edit mode only)."""
        if not self._edit_mode:
            return
        for item in self._page_view.text_items():
            if item.isSelected():
                self._page_view.remove_text_item(item)
        self._schedule_autosave()

    def apply_style(self, style: TextStyle) -> None:
        """Store ``style`` for new fields and apply it to selected ones."""
        self._style = style
        for item in self._page_view.text_items():
            if item.isSelected():
                text_style.apply_style(item, style)
        self._schedule_autosave()

    # --- search + active-field editing --------------------------------------

    def field_hits(self, query: str) -> list[FieldHit]:
        """Return text fields whose text contains ``query`` (case-insensitive)."""
        needle = query.strip().casefold()
        if not needle:
            return []
        self._harvest_page(self._page_view.current_page_index())  # include unsaved edits
        hits: list[FieldHit] = []
        pages = sorted({field.page_index for field in self._store.all_fields()})
        for page_index in pages:
            for field_index, spec in enumerate(self._store.fields_on(page_index)):
                if needle in spec.text.casefold():
                    hits.append(FieldHit(page_index, field_index, spec.text))
        return hits

    def activate_field(self, page_index: int, field_index: int) -> None:
        """Navigate to ``page_index`` and select that page's ``field_index`` field."""
        if not self._edit_mode:
            self.set_edit_mode(True)
        self._page_view.go_to_page(page_index)
        items = self._page_view.text_items()
        if 0 <= field_index < len(items):
            item = items[field_index]
            item.setSelected(True)
            item.ensureVisible()

    def selected_style(self) -> TextStyle | None:
        """Return the style of the selected field, or ``None`` if none selected."""
        item = self._page_view.selected_text_item()
        return text_style.item_to_style(item) if item is not None else None

    def set_selected_text(self, text: str) -> None:
        item = self._page_view.selected_text_item()
        if item is not None:
            item.setPlainText(text)
            self._schedule_autosave()

    def clear_saved_fields(self) -> None:
        """Delete this document's saved overlay content and its sidecar file."""
        self._drop_overlay(mark_dirty=True)

    def flush(self) -> None:
        """Persist any pending edits immediately (e.g. before closing a doc)."""
        self._timer.stop()
        self._save()

    def embed_into_document(self, target: Path) -> OpResult:
        """Flatten the placed overlay into ``target`` in place, then drop it."""
        error = self._flatten(target)
        if error is not None:
            return OpResult(False, error)
        self._drop_overlay()
        return OpResult(True, strings.MSG_TEXT_EMBEDDED)

    def _drop_overlay(self, *, mark_dirty: bool = False) -> None:
        """Stop autosave, clear every live + stored item, and remove the sidecar."""
        self._timer.stop()
        self._store.clear()
        self._page_view.clear_text_items()
        for satellite in self._satellites:
            satellite.clear()
        if self._source is not None:
            with contextlib.suppress(FileNotFoundError):
                os.remove(sidecar_path(self._source))
            if mark_dirty:
                self._mark_dirty()

    def has_overlay(self) -> bool:
        """Return whether any page has a text field or image (incl. unsaved)."""
        return not self._current_document_is_empty()

    def export_to_file(self, source: Path, output: Path) -> OpResult:
        """Bake the placed overlay from ``source`` into ``output``, keeping the session."""
        error = self._flatten(source, output)
        if error is not None:
            return OpResult(False, error)
        return OpResult(True, strings.MSG_TEXT_EXPORTED_FMT.format(name=output.name))

    def _flatten(self, source: Path, output: Path | None = None) -> str | None:
        """Bake all overlay from ``source`` onto ``output`` (or ``source`` in place)."""
        self._harvest_all()
        doc = self._store.document()
        base = self._base_dir or source.parent
        try:
            apply_overlay(source, doc.fields, doc.images, doc.rects, base_dir=base, output=output)
        except (ValueError, OSError) as err:
            log.error("%s", err)
            return str(err)
        return None

    # --- internals ----------------------------------------------------------

    def _on_page_shown(self, _current: int, _total: int) -> None:
        self._restore_page(self._page_view.current_page_index())

    def _on_scene_changed(self, *_args: object) -> None:
        if self._edit_mode:
            self._schedule_autosave()

    def _harvest_page(self, index: int) -> None:
        self._store.set_fields(
            index,
            [text_style.item_to_spec(item, index) for item in self._page_view.text_items()],
        )

    def _harvest_all(self) -> None:  # current page, every kind, before save/flatten
        self._harvest_page(self._page_view.current_page_index())
        for satellite in self._satellites:
            satellite.harvest_current()

    def _restore_page(self, index: int) -> None:
        self._page_view.clear_text_items()
        for spec in self._store.fields_on(index):
            item = text_style.spec_to_item(spec)
            item.set_editable(self._edit_mode)
            self._page_view.add_text_item(item)
            item.setZValue(spec.z)  # re-assert: ItemLayer.add forces the layer default

    def _current_document_is_empty(self) -> bool:
        self._harvest_all()
        return self._store.is_empty()

    def _schedule_autosave(self) -> None:
        if self._source is not None:
            self._timer.start()
            self._mark_dirty()

    def _save(self) -> None:
        if self._source is None:
            return
        self._harvest_all()
        if self._store.is_empty():
            # Never create an empty sidecar; drop a stale one if all items are gone.
            with contextlib.suppress(FileNotFoundError):
                os.remove(sidecar_path(self._source))
            return
        save_sidecar(self._source, self._store.document())
