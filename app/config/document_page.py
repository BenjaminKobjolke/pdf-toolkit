"""Per-document remembered page.

Reopens each PDF on the page (0-based index) the user was last viewing. The index
is stored as-is; out-of-range values are clamped when applied by
:meth:`PageView.go_to_page`, so the store stays trivial.
"""

from __future__ import annotations

from typing import Any

from app.config.per_document_store import PerDocumentStore
from app.storage.backend import StorageBackend

DOCUMENT_PAGE_NAMESPACE = "page"


class DocumentPageStore(PerDocumentStore[int]):
    """Remembers a 0-based page index per document path."""

    LABEL = "Remembered document page"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, DOCUMENT_PAGE_NAMESPACE)

    def _encode(self, value: int) -> Any:
        return int(value)

    def _decode(self, raw: Any) -> int:
        return int(raw)
