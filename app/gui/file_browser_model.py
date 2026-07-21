"""Pure, Qt-free filesystem logic for the custom file browser dialog.

The only file-browser logic that can fail on its own — directory listing,
sorting, extension filtering, type-ahead matching, and parent navigation — lives
here so it is unit-tested directly with ``tmp_path``. The Qt widget and the vim
key dispatch live in :mod:`app.gui.file_browser_dialog`; the trivial cursor
clamps (``j``/``k``/``gg``/``G``) stay there because clamping a list index can't
meaningfully break.
"""

from __future__ import annotations

import bisect
import ctypes
import os
import string
from dataclasses import dataclass
from pathlib import Path

from app.pdf.file_format import FileFormat


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


def sibling_file(current: Path, filt: FileFilter, step: int) -> Path | None:
    """The next (``step=1``) / previous (``step=-1``) openable file beside ``current``.

    Candidates are the filter-matching files in ``current``'s directory, in the
    same case-insensitive alphabetical order the browser shows; the ends wrap
    around. Files the viewer can't render (``FileFormat.of`` → ``None``, e.g.
    binaries under an all-files filter) are skipped. Never returns ``current``
    itself; ``None`` when no other openable file exists.
    """
    files = [entry.path for entry in list_dir(current.parent, filt) if not entry.is_dir]
    names = [path.name.casefold() for path in files]
    key = current.name.casefold()
    if key in names:
        index = names.index(key)
    else:
        # The open document itself may not pass the filter (a sniff-opened file
        # such as .ini); anchor stepping at its alphabetical position anyway.
        index = bisect.bisect_left(names, key)
        files.insert(index, current)
    for offset in range(1, len(files)):
        candidate = files[(index + step * offset) % len(files)]
        if candidate != current and FileFormat.of(candidate) is not None:
            return candidate
    return None


def nearest_file(missing: Path, filt: FileFilter) -> Path | None:
    """The openable file closest to a (deleted) ``missing``: successor, else predecessor.

    Unlike :func:`sibling_file` this never wraps — after deleting the last file
    the selection lands on the new last file, not the first. Never returns
    ``missing`` itself, so it also works before the deletion hits the disk.
    ``None`` when no other openable file exists.
    """
    files = [path for path in openable_files(missing.parent, filt) if path != missing]
    if not files:
        return None
    names = [path.name.casefold() for path in files]
    index = bisect.bisect_left(names, missing.name.casefold())
    return files[min(index, len(files) - 1)]


def openable_files(directory: Path, filt: FileFilter) -> list[Path]:
    """All filter-matching, renderable files in ``directory``, in list order.

    Same openability rule as :func:`sibling_file` (``FileFormat.of`` must
    recognize the file); directories are excluded.
    """
    return [
        entry.path
        for entry in list_dir(directory, filt)
        if not entry.is_dir and FileFormat.of(entry.path) is not None
    ]


def first_openable_file(directory: Path, filt: FileFilter) -> Path | None:
    """The alphabetically first filter-matching, renderable file in ``directory``.

    ``None`` when the directory holds nothing the viewer can open.
    """
    return next(iter(openable_files(directory, filt)), None)


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
