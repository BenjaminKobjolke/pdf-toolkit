"""Atomic JSON file writes shared across the codebase.

Both the per-PDF sidecar and the recent-files store persist JSON the same way:
serialize, write to a sibling ``.tmp`` file, then ``os.replace`` it into place so
a reader never sees a half-written file. This module owns that single pattern.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_TMP_SUFFIX = ".tmp"


def write_json_atomic(path: Path, payload: Any) -> None:
    """Serialize ``payload`` and write it to ``path`` atomically.

    Writes ``json.dumps(payload, indent=2)`` to ``<path>.tmp`` then replaces
    ``path`` with it. Leaves no temp file behind on success.
    """
    tmp = path.with_name(path.name + _TMP_SUFFIX)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)
