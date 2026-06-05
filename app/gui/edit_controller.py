"""Owns the text-field editing model: per-page specs, autosave, and export.

The view (:class:`PageView`) holds only the items currently on screen; this
controller is the source of truth across pages. On navigation it harvests live
items back into specs and rebuilds the destination page. Specs persist to the
JSON sidecar (debounced) and feed the fitz overlay export.
"""

from __future__ import annotations

import contextlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QTimer

from app.gui import strings, text_style
from app.gui.operations import OpResult
from app.gui.page_view import PageView
from app.gui.text_item import TextFieldItem
from app.gui.text_style import TextStyle
from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_overlay import apply_text_overlay, embedded_output_path
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec

log = logging.getLogger("pdf_toolkit")

_AUTOSAVE_MS = 400
_NEW_FIELD_POS = (40.0, 40.0)


@dataclass(frozen=True)
class FieldHit:
    """A text-field search match: its page, position in that page, and text."""

    page_index: int
    field_index: int
    text: str


class EditController:
    """Coordinates text-field editing between the page view and persistence."""

    def __init__(self, page_view: PageView) -> None:
        self._page_view = page_view
        self._source: Path | None = None
        self._fields_by_page: dict[int, list[TextFieldSpec]] = {}
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

    # --- public API ---------------------------------------------------------

    def on_document_loaded(self, pdf: Path) -> None:
        """Load the sidecar for ``pdf``. Fields are shown whether editing or not.

        Call before the page view renders; the resulting ``page_changed`` signal
        restores this page's fields. Raises ``ValueError`` on a malformed sidecar.
        """
        self._edit_mode = False
        self._fields_by_page = {}
        try:
            doc = load_sidecar(pdf)
        finally:
            self._source = pdf  # set even on failure so stale specs are dropped
        for field in doc.fields:
            self._fields_by_page.setdefault(field.page_index, []).append(field)

    def set_edit_mode(self, on: bool) -> None:
        """Toggle whether the (always-visible) fields can be moved/edited."""
        if not on:
            self._harvest_page(self._page_view.current_page_index())
        self._edit_mode = on
        for item in self._page_view.text_items():
            item.set_editable(on)

    def add_field(self) -> None:
        """Add a new default text field to the current page (edit mode only)."""
        if not self._edit_mode or self._source is None:
            return
        item = TextFieldItem()
        text_style.apply_style(item, self._style)
        item.setPos(*_NEW_FIELD_POS)
        self._page_view.add_text_item(item)
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
        # Harvest the current page so unsaved edits are searchable too.
        self._harvest_page(self._page_view.current_page_index())
        hits: list[FieldHit] = []
        for page_index in sorted(self._fields_by_page):
            for field_index, spec in enumerate(self._fields_by_page[page_index]):
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
        """Replace the selected field's text."""
        item = self._page_view.selected_text_item()
        if item is not None:
            item.setPlainText(text)
            self._schedule_autosave()

    def clear_saved_fields(self) -> None:
        """Delete this document's saved text fields and its sidecar file."""
        self._timer.stop()
        self._fields_by_page = {}
        self._page_view.clear_text_items()
        if self._source is not None:
            with contextlib.suppress(FileNotFoundError):
                os.remove(sidecar_path(self._source))

    def flush(self) -> None:
        """Persist any pending edits immediately (e.g. before closing a doc)."""
        self._timer.stop()
        self._save()

    def export(self, source: Path) -> OpResult:
        """Write a copy of ``source`` with the text fields embedded.

        Writes ``<stem>_text-embedded.pdf`` next to ``source`` (leaving the
        original untouched) and saves the sidecar. Returns an :class:`OpResult`.
        """
        specs = self._collect_specs()
        output = embedded_output_path(source)
        try:
            apply_text_overlay(source, specs, output)
        except (ValueError, OSError) as err:
            log.error("%s", err)
            return OpResult(False, str(err))
        self._save()
        return OpResult(True, strings.MSG_TEXT_EXPORTED_FMT.format(name=output.name))

    # --- internals ----------------------------------------------------------

    def _on_page_shown(self, _current: int, _total: int) -> None:
        self._restore_page(self._page_view.current_page_index())

    def _on_scene_changed(self, *_args: object) -> None:
        if self._edit_mode:
            self._schedule_autosave()

    def _harvest_page(self, index: int) -> None:
        self._fields_by_page[index] = [
            text_style.item_to_spec(item, index) for item in self._page_view.text_items()
        ]

    def _restore_page(self, index: int) -> None:
        self._page_view.clear_text_items()
        for spec in self._fields_by_page.get(index, []):
            item = text_style.spec_to_item(spec)
            item.set_editable(self._edit_mode)
            self._page_view.add_text_item(item)

    def _collect_specs(self) -> tuple[TextFieldSpec, ...]:
        self._harvest_page(self._page_view.current_page_index())
        ordered: list[TextFieldSpec] = []
        for index in sorted(self._fields_by_page):
            ordered.extend(self._fields_by_page[index])
        return tuple(ordered)

    def _schedule_autosave(self) -> None:
        if self._source is not None:
            self._timer.start()

    def _save(self) -> None:
        if self._source is None:
            return
        specs = self._collect_specs()
        if not specs:
            # No fields to persist: never create an empty sidecar, and drop a
            # stale one (e.g. the user deleted every previously-saved field).
            with contextlib.suppress(FileNotFoundError):
                os.remove(sidecar_path(self._source))
            return
        save_sidecar(self._source, TextDocumentSpec(fields=specs))
