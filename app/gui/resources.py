"""Resolve bundled GUI assets in both source and frozen (PyInstaller) runs.

PyInstaller's onefile exe unpacks bundled ``datas`` under ``sys._MEIPASS`` at
runtime; from source we resolve relative to the project root. ``pdft-gui.spec``
bundles ``assets/icon.ico`` so ``app_icon()`` works in both modes.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

from app.logging_setup import log
from app.release.schema import RELEASE_NOTES_DIRNAME

ICON_FILE = "icon.ico"
APP_USER_MODEL_ID = "BenjaminKobjolke.PdfToolkit.Gui"


def _base_dir() -> Path:
    """Root that contains the ``assets/`` folder (MEIPASS when frozen)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass)
    return Path(__file__).resolve().parents[2]


def bundled_root() -> Path:
    """Frozen-aware project/bundle root (MEIPASS when frozen, repo root in dev)."""
    return _base_dir()


def release_notes_dir() -> Path:
    """Absolute path to the bundled ``release_notes/`` folder."""
    return _base_dir() / RELEASE_NOTES_DIRNAME


def asset_path(name: str) -> Path:
    """Absolute path to a bundled asset by file name."""
    return _base_dir() / "assets" / name


def app_icon() -> QIcon:
    """The application icon; empty ``QIcon`` if the file is missing."""
    return QIcon(str(asset_path(ICON_FILE)))


def set_app_user_model_id(app_id: str = APP_USER_MODEL_ID) -> bool:
    """Set the explicit Windows AppUserModelID so the taskbar uses our icon.

    Without this the taskbar groups the window under the host process
    (``python.exe`` / ``pythonw.exe``) and shows *its* icon, ignoring
    ``QApplication.setWindowIcon``. Must run before any window is shown.
    Returns ``True`` if applied; a no-op returning ``False`` off Windows.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except (OSError, AttributeError) as exc:
        log.warning("Could not set AppUserModelID: %s", exc)
        return False
    return True
