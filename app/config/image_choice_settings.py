"""Persistence for the last-used image-add choice: copy into assets vs reference.

Lets the add-image prompt pre-select the user's previous choice across restarts.
Kept Qt-free; the GUI maps the stored id to a dialog default.
"""

from __future__ import annotations

from app.config.file_backed_store import FileBackedStore
from app.io.json_store import read_versioned_dict, write_versioned

IMAGE_CHOICE_VERSION = 1

CHOICE_COPY = "copy"
CHOICE_REFERENCE = "reference"


class ImageChoiceStore(FileBackedStore):
    """Reads and writes the last image-add choice at a fixed JSON path."""

    LABEL = "Image add: copy-vs-reference choice"

    def load(self) -> str | None:
        """Return the stored choice id, or ``None`` if absent/corrupt."""
        raw = read_versioned_dict(self._path, IMAGE_CHOICE_VERSION)
        if raw is None:
            return None
        value = raw.get("choice")
        return value if value in (CHOICE_COPY, CHOICE_REFERENCE) else None

    def save(self, choice: str) -> None:
        write_versioned(self._path, IMAGE_CHOICE_VERSION, {"choice": choice})
