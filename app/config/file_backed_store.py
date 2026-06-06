"""Base class for the small JSON-backed config stores.

Every remembered-preference store persists to one file. This base gives them a
uniform :meth:`reset` (delete the file, restoring defaults on next load) and a
human-readable :attr:`label`, so the "Remembered settings" command can list and
reset them without a hardcoded table.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


class FileBackedStore:
    """A config store backed by a single JSON file at a fixed path."""

    LABEL = "setting"

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    @property
    def label(self) -> str:
        """Human-readable name shown in the Remembered-settings command."""
        return self.LABEL

    def reset(self) -> None:
        """Forget the remembered value by deleting the backing file (no-op if absent)."""
        with contextlib.suppress(FileNotFoundError):
            os.remove(self._path)
