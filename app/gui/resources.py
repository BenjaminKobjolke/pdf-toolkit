"""Resolve bundled GUI assets in both source and frozen (PyInstaller) runs.

PyInstaller's onefile exe unpacks bundled ``datas`` under ``sys._MEIPASS`` at
runtime; from source we resolve relative to the project root. ``pdft-gui.spec``
bundles ``assets/icon.ico`` so ``app_icon()`` works in both modes.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

ICON_FILE = "icon.ico"


def _base_dir() -> Path:
    """Root that contains the ``assets/`` folder (MEIPASS when frozen)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass)
    return Path(__file__).resolve().parents[2]


def asset_path(name: str) -> Path:
    """Absolute path to a bundled asset by file name."""
    return _base_dir() / "assets" / name


def app_icon() -> QIcon:
    """The application icon; empty ``QIcon`` if the file is missing."""
    return QIcon(str(asset_path(ICON_FILE)))
