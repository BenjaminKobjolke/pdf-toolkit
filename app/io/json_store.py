"""Atomic JSON file writes (and versioned reads) shared across the codebase.

Several small stores (sidecar, recent files, UI state) persist JSON the same
way: serialize, write to a sibling ``.tmp`` file, then ``os.replace`` it so a
reader never sees a half-written file. The versioned helpers add the matching
read/write guard the config stores share.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.io.fs import replace_atomic
from app.logging_setup import log

_TMP_SUFFIX = ".tmp"


def write_json_atomic(path: Path, payload: Any) -> None:
    """Serialize ``payload`` and write it to ``path`` atomically.

    Writes ``json.dumps(payload, indent=2)`` to ``<path>.tmp`` then replaces
    ``path`` with it. Leaves no temp file behind on success.
    """
    tmp = path.with_name(path.name + _TMP_SUFFIX)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    replace_atomic(tmp, path)


def read_versioned_dict(path: Path, version: int) -> dict[str, Any] | None:
    """Read a versioned JSON object, or ``None`` if absent/corrupt/mismatched.

    Returns the raw dict only when the file exists, parses, is a JSON object,
    and carries the expected ``"version"``. A bad read is logged, not raised, so
    a corrupt store degrades to defaults instead of blocking the app.
    """
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        log.warning("ignoring unreadable store %s: %s", path, err)
        return None
    if not isinstance(raw, dict) or raw.get("version") != version:
        log.warning("ignoring store %s with bad shape/version", path)
        return None
    return raw


def write_versioned(path: Path, version: int, payload: dict[str, Any]) -> None:
    """Write ``payload`` (with ``version`` injected) atomically, creating dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, {"version": version, **payload})
