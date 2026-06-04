"""Rename a PDF together with its JSON sidecar.

Keeps the field sidecar (``document.json``) next to its PDF when the PDF is
renamed, so saved text fields survive the rename.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.pdf.sidecar import sidecar_path


def rename_document(source: Path, target: Path) -> None:
    """Rename ``source`` to ``target`` (and its sidecar, if any).

    Raises ``ValueError`` if ``target`` already exists, leaving ``source`` in
    place.
    """
    if target.exists():
        raise ValueError(f"a file named {target.name} already exists")
    os.rename(source, target)
    old_sidecar = sidecar_path(source)
    if old_sidecar.is_file():
        os.rename(old_sidecar, sidecar_path(target))
