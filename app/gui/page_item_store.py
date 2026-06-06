"""Per-page storage of placed text fields and images (the cross-page model).

Qt-free: it holds only the pure specs, keyed by page index. The view shows one
page at a time; the controllers harvest live items into this store on navigation
and restore them on the way back. One store instance is shared by the text and
image controllers so a single save writes both kinds.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.pdf.image_spec import ImageFieldSpec, SidecarDocument
from app.pdf.text_spec import TextFieldSpec


class PageItemStore:
    """The source-of-truth dictionaries for placed fields and images, per page."""

    def __init__(self) -> None:
        self._fields_by_page: dict[int, list[TextFieldSpec]] = {}
        self._images_by_page: dict[int, list[ImageFieldSpec]] = {}

    def load(self, doc: SidecarDocument) -> None:
        """Replace all content with ``doc``, distributing it by page index."""
        self.clear()
        for field in doc.fields:
            self._fields_by_page.setdefault(field.page_index, []).append(field)
        for image in doc.images:
            self._images_by_page.setdefault(image.page_index, []).append(image)

    def clear(self) -> None:
        self._fields_by_page = {}
        self._images_by_page = {}

    def set_fields(self, page_index: int, specs: Sequence[TextFieldSpec]) -> None:
        self._fields_by_page[page_index] = list(specs)

    def set_images(self, page_index: int, specs: Sequence[ImageFieldSpec]) -> None:
        self._images_by_page[page_index] = list(specs)

    def fields_on(self, page_index: int) -> list[TextFieldSpec]:
        return self._fields_by_page.get(page_index, [])

    def images_on(self, page_index: int) -> list[ImageFieldSpec]:
        return self._images_by_page.get(page_index, [])

    def all_fields(self) -> tuple[TextFieldSpec, ...]:
        ordered: list[TextFieldSpec] = []
        for index in sorted(self._fields_by_page):
            ordered.extend(self._fields_by_page[index])
        return tuple(ordered)

    def all_images(self) -> tuple[ImageFieldSpec, ...]:
        ordered: list[ImageFieldSpec] = []
        for index in sorted(self._images_by_page):
            ordered.extend(self._images_by_page[index])
        return tuple(ordered)

    def document(self) -> SidecarDocument:
        return SidecarDocument(fields=self.all_fields(), images=self.all_images())

    def is_empty(self) -> bool:
        return not self.all_fields() and not self.all_images()
