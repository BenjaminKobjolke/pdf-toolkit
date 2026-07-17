"""Persisted, cross-session filter for the open-file dialog.

Which files the open dialog lists: everything, or only a user-editable set of
extensions (defaults derived from the viewer's :class:`FileFormat` enum). Uses
the same versioned-dict pattern as :mod:`app.config.text_view_settings`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.pdf.file_format import FileFormat
from app.storage.backend import StorageBackend

# v2: image formats joined FileFormat — reset stored filters to the new defaults
# so images aren't silently hidden from the open dialog and sibling navigation.
OPEN_FILTER_VERSION = 2
OPEN_FILTER_KEY = "open_filter"

# The viewer's own formats are the natural default — derived, not restated.
DEFAULT_EXTENSIONS: tuple[str, ...] = tuple(f.value for f in FileFormat)


def parse_extensions(text: str) -> tuple[str, ...]:
    """Normalize user input like ``"PDF, txt ini"`` to ``(".pdf", ".txt", ".ini")``.

    Lowercase dotted forms are required: :meth:`FileFilter.accepts` compares
    against ``path.suffix.casefold()``. Blanks are dropped, order-preserving dedupe.
    """
    parts = (p.strip().lower() for p in text.replace(",", " ").split())
    dotted = (p if p.startswith(".") else f".{p}" for p in parts if p.strip("."))
    return tuple(dict.fromkeys(dotted))


@dataclass(frozen=True)
class OpenFilterSettings:
    """Remembered open-dialog filter preferences (defaults = viewer formats)."""

    all_files: bool = False
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS


class OpenFilterSettingsStore(RecordStore):
    """Reads and writes :class:`OpenFilterSettings` via the storage backend."""

    LABEL = "Open dialog filter"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, OPEN_FILTER_KEY)

    def load(self) -> OpenFilterSettings:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, OPEN_FILTER_VERSION)
        if raw is None:
            return OpenFilterSettings()
        default = OpenFilterSettings()
        return OpenFilterSettings(
            all_files=bool(raw.get("all_files", default.all_files)),
            extensions=tuple(raw.get("extensions", default.extensions)),
        )

    def save(self, settings: OpenFilterSettings) -> None:
        self._backend.set_versioned(
            self._key,
            OPEN_FILTER_VERSION,
            {"all_files": settings.all_files, "extensions": list(settings.extensions)},
        )
