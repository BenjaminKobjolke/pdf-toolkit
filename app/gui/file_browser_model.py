"""Pure, Qt-free filesystem logic for the custom file browser dialog.

The only file-browser logic that can fail on its own — directory listing,
sorting, extension filtering, type-ahead matching, and parent navigation — lives
here so it is unit-tested directly with ``tmp_path``. The Qt widget and the vim
key dispatch live in :mod:`app.gui.file_browser_dialog`; the trivial cursor
clamps (``j``/``k``/``gg``/``G``) stay there because clamping a list index can't
meaningfully break.
"""

from __future__ import annotations

import ctypes
import os
import string
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileFilter:
    """Which files a browser shows. An empty ``patterns`` accepts every file."""

    label: str
    patterns: tuple[str, ...] = ()

    def accepts(self, path: Path) -> bool:
        """True if ``path``'s extension matches (case-insensitive), or if no filter."""
        if not self.patterns:
            return True
        return path.suffix.casefold() in self.patterns


@dataclass(frozen=True)
class FsEntry:
    """One row in the browser: a file or directory under the current folder."""

    name: str
    path: Path
    is_dir: bool


def list_dir(directory: Path, filt: FileFilter) -> list[FsEntry]:
    """Directories first, then matching files; each group case-insensitive alpha.

    Hidden dotfiles are skipped. Returns ``[]`` for an empty or unreadable
    directory — callers treat absent and empty the same: nothing to pick.
    """
    try:
        children = list(directory.iterdir())
    except OSError:
        return []
    dirs: list[FsEntry] = []
    files: list[FsEntry] = []
    for child in children:
        if child.name.startswith("."):
            continue
        if child.is_dir():
            dirs.append(FsEntry(child.name, child, True))
        elif filt.accepts(child):
            files.append(FsEntry(child.name, child, False))
    dirs.sort(key=lambda entry: entry.name.casefold())
    files.sort(key=lambda entry: entry.name.casefold())
    return dirs + files


def parent_of(directory: Path) -> Path:
    """The parent directory, clamped at the filesystem root (``Path.parent`` self-clamps)."""
    return directory.parent


def is_root(directory: Path) -> bool:
    """True when ``directory`` is a filesystem root (its parent is itself)."""
    return parent_of(directory) == directory


def drives() -> list[FsEntry]:
    """The mounted drive roots, as directory entries (``C:\\``, ``D:\\``, …).

    Used as the "one level above a drive root" view. Reads the live drive bitmask
    from ``GetLogicalDrives`` — never stats individual letters, so an absent
    floppy/network ``A:`` can't stall the call. Returns ``[]`` off Windows.
    """
    if os.name != "nt":
        return []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    roots: list[FsEntry] = []
    for index, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << index):
            roots.append(FsEntry(f"{letter}:\\", Path(f"{letter}:\\"), True))
    return roots


def substring_filter(entries: list[FsEntry], query: str) -> list[FsEntry]:
    """Entries whose name contains ``query`` (case-insensitive); empty query keeps all."""
    if not query:
        return entries
    needle = query.casefold()
    return [entry for entry in entries if needle in entry.name.casefold()]
