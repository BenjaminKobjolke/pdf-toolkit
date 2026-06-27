"""Public file-pick entry points — the keyboard-first replacements for the native
``QFileDialog`` static methods. Thin wrappers over :class:`FileBrowserDialog` so
callers never touch the widget or its modes directly.

Each returns a ``Path`` (accepted) or ``None`` (cancelled), mirroring the
cancel-is-``None`` shape of :mod:`app.gui.number_input_dialog` and friends.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.gui import file_browser_strings as fbs
from app.gui.file_browser_dialog import FileBrowserDialog, _Mode
from app.gui.file_browser_model import FileFilter


def _start_dir(start: Path | None) -> Path:
    """Resolve a usable starting directory from a dir, a file's parent, or home."""
    if start is not None and start.is_dir():
        return start
    if start is not None and start.parent.is_dir():
        return start.parent
    return Path.home()


def prompt_open_file(
    parent: QWidget | None, title: str, filt: FileFilter, start: Path | None = None
) -> Path | None:
    """Pick an existing file; return its path, or ``None`` if cancelled."""
    dialog = FileBrowserDialog(
        mode=_Mode.OPEN, title=title, filt=filt, start=_start_dir(start), parent=parent
    )
    dialog.exec()
    return dialog.chosen()


def prompt_save_file(
    parent: QWidget | None, title: str, default: Path, filt: FileFilter
) -> Path | None:
    """Pick a destination file (dir + name prefilled from ``default``); ``None`` if cancelled."""
    dialog = FileBrowserDialog(
        mode=_Mode.SAVE,
        title=title,
        filt=filt,
        start=_start_dir(default),
        default_name=default.name,
        parent=parent,
    )
    dialog.exec()
    return dialog.chosen()


def prompt_directory(parent: QWidget | None, title: str, start: Path | None = None) -> Path | None:
    """Pick a directory; return its path, or ``None`` if cancelled."""
    dialog = FileBrowserDialog(
        mode=_Mode.DIR, title=title, filt=fbs.FILTER_ALL, start=_start_dir(start), parent=parent
    )
    dialog.exec()
    return dialog.chosen()
