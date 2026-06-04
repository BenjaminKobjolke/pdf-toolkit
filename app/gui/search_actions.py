"""Live search of PDF body text and placed text fields, with match highlights.

Both searches use the same :class:`FilterListDialog` provider mode — only the
result source differs. PDF matches jump + highlight (highlight persists until
cleared); field matches jump + select the field.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.gui import strings
from app.gui.edit_bar import EditBar
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.page_view import PageView
from app.pdf.search import search_pdf

_SEARCH_MIN_CHARS = 3


class SearchActions:
    """PDF / field search and highlight clearing."""

    def __init__(
        self,
        parent: QWidget,
        page_view: PageView,
        controller: EditController,
        edit_bar: EditBar,
        source: Callable[[], Path | None],
    ) -> None:
        self._parent = parent
        self._page_view = page_view
        self._controller = controller
        self._edit_bar = edit_bar
        self._source = source

    def search_pdf_text(self) -> None:
        source = self._source()
        if source is None:
            return

        def provider(query: str) -> list[ListEntry]:
            return [
                ListEntry(
                    title=strings.SEARCH_RESULT_FMT.format(
                        page=hit.page_index + 1,
                        snippet=hit.snippet or strings.SEARCH_RESULT_NO_SNIPPET,
                    ),
                    payload=hit,
                )
                for hit in search_pdf(source, query)
            ]

        dialog = self._dialog(strings.SEARCH_PDF_TITLE, provider)
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            hit = chosen.payload
            self._page_view.go_to_page(hit.page_index)
            self._page_view.set_highlights([(hit.x0, hit.y0, hit.x1, hit.y1)])

    def search_fields(self) -> None:
        if self._source() is None:
            return

        def provider(query: str) -> list[ListEntry]:
            return [
                ListEntry(
                    title=strings.SEARCH_RESULT_FMT.format(
                        page=hit.page_index + 1, snippet=hit.text
                    ),
                    payload=hit,
                )
                for hit in self._controller.field_hits(query)
            ]

        dialog = self._dialog(strings.SEARCH_FIELDS_TITLE, provider)
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            hit = chosen.payload
            if not self._edit_bar.is_edit_mode():
                self._edit_bar.toggle_edit_mode()  # syncs toolbar + controller
            self._controller.activate_field(hit.page_index, hit.field_index)

    def clear_highlights(self) -> None:
        self._page_view.clear_highlights()

    def _dialog(self, title: str, provider: Callable[[str], list[ListEntry]]) -> FilterListDialog:
        return FilterListDialog(
            [],
            placeholder=strings.SEARCH_PLACEHOLDER,
            title=title,
            provider=provider,
            min_chars=_SEARCH_MIN_CHARS,
            parent=self._parent,
        )
