"""Per-document remembered zoom.

Reopens each PDF at the zoom last used for it. Reuses :class:`ZoomSettings` and
its shared (de)serialization so the on-disk shape matches the global default-zoom
store exactly.
"""

from __future__ import annotations

from typing import Any

from app.config.per_document_store import PerDocumentStore
from app.config.zoom_settings import ZoomSettings, zoom_from_dict, zoom_to_dict
from app.storage.backend import StorageBackend

DOCUMENT_ZOOM_NAMESPACE = "zoom"


class DocumentZoomStore(PerDocumentStore[ZoomSettings]):
    """Remembers a :class:`ZoomSettings` per document path."""

    LABEL = "Remembered document zoom"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, DOCUMENT_ZOOM_NAMESPACE)

    def _encode(self, value: ZoomSettings) -> Any:
        return zoom_to_dict(value)

    def _decode(self, raw: Any) -> ZoomSettings:
        return zoom_from_dict(raw)
