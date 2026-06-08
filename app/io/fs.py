"""Filesystem helpers shared across the atomic writers.

PDFs that arrive from email attachments, downloads, or zip extraction commonly
carry the Windows read-only attribute. ``shutil.copy2`` propagates it onto the
working copy, and ``os.replace`` over a read-only destination then fails with
``[WinError 5] Access is denied``. These helpers strip that attribute before the
replace so an in-place atomic write always succeeds.
"""

from __future__ import annotations

import contextlib
import os
import stat
from pathlib import Path


def clear_readonly(path: Path) -> None:
    """Clear the read-only attribute so ``path`` can be overwritten/replaced.

    No-op-safe when the path is absent and on POSIX (where the read-only flag
    does not block ``os.replace`` anyway).
    """
    with contextlib.suppress(OSError):
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)


def replace_atomic(tmp: Path, dst: Path) -> None:
    """``os.replace(tmp, dst)`` after clearing any read-only attribute on ``dst``."""
    if dst.exists():
        clear_readonly(dst)
    os.replace(tmp, dst)
