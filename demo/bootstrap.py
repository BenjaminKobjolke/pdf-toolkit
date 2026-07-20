"""Deterministic demo state: a wiped temp SQLite DB, optionally pre-seeded.

The app persists preferences in SQLite (not QSettings), so the connector's
``prepare_demo_settings`` does not apply. This is its SQLite equivalent.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.storage.factory import make_backend

_DEMO_DIR_NAME = "fastfileviewer-demo-settings"


def prepare_demo_database(settings: Iterable[tuple[str, str]]) -> str:
    """Create a wiped temp demo DB, seed it, and return its database URL.

    ``settings`` are ``--automation-demo-settings`` pairs in the dialect
    ``"<store_key>/<field>": value`` (e.g. ``"text_view/font_pt": "16"``);
    fields are grouped per store key and written as one versioned row.
    String values are fine — SettingsRecordStore.load coerces on read.
    """
    demo_dir = Path(tempfile.gettempdir()) / _DEMO_DIR_NAME
    shutil.rmtree(demo_dir, ignore_errors=True)
    demo_dir.mkdir(parents=True)
    url = f"sqlite:///{demo_dir / 'demo.db'}"

    grouped: dict[str, dict[str, Any]] = {}
    for key, value in settings:
        store_key, _, field = key.partition("/")
        if not field:
            raise ValueError(f"demo setting key must be '<store>/<field>': {key!r}")
        grouped.setdefault(store_key, {})[field] = value

    if grouped:
        backend = make_backend(url)
        for store_key, payload in grouped.items():
            # ponytail: every store is VERSION 1 today; add a version map here
            # if a store ever bumps.
            backend.set_versioned(store_key, 1, payload)
    return url
