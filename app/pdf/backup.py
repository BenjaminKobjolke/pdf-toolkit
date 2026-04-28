"""Timestamped backup writer."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

TIMESTAMP_FORMAT = "%Y%m%d-%H%M"


def create_backup(source: Path, backup_dir: Path) -> Path:
    """Copy ``source`` into ``backup_dir`` named ``YYYYMMDD-HHMM-<source.name>``.

    Creates ``backup_dir`` if missing. Returns the new backup path.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    target = backup_dir / f"{stamp}-{source.name}"
    shutil.copy2(source, target)
    return target
