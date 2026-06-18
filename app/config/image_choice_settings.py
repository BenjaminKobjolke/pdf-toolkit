"""Persistence for the last-used image-add choice: copy into assets vs reference.

Lets the add-image prompt pre-select the user's previous choice across restarts.
Kept Qt-free; the GUI maps the stored id to a dialog default.
"""

from __future__ import annotations

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

IMAGE_CHOICE_VERSION = 1
IMAGE_CHOICE_KEY = "image_choice"

CHOICE_COPY = "copy"
CHOICE_REFERENCE = "reference"


class ImageChoiceStore(RecordStore):
    """Reads and writes the last image-add choice via the storage backend."""

    LABEL = "Image add: copy-vs-reference choice"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, IMAGE_CHOICE_KEY)

    def load(self) -> str | None:
        """Return the stored choice id, or ``None`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, IMAGE_CHOICE_VERSION)
        if raw is None:
            return None
        value = raw.get("choice")
        return value if value in (CHOICE_COPY, CHOICE_REFERENCE) else None

    def save(self, choice: str) -> None:
        self._backend.set_versioned(self._key, IMAGE_CHOICE_VERSION, {"choice": choice})
