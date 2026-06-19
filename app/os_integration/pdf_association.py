"""Register (and remove) the GUI viewer as a Windows PDF handler.

This is the Python port of ``pdft_gui_register.bat`` / ``pdft_gui_unregister.bat``
so the command palette can register the app without shelling out to a ``.bat``.

What registration does and does NOT do:

* It writes a per-user (HKCU, no admin) ProgID ``pdf-toolkit.Viewer`` and adds it
  to the ``.pdf`` *Open with* list, so the viewer becomes a *choosable* handler.
* It does **not** silently set the default. Windows 8+/10/11 guard the active
  association (``.pdf\\UserChoice``) with a per-user signed hash that no third
  party can forge, so the user must finish in the Default Apps UI.

The ``shell\\open\\command`` value differs by build: a dev/source run points at
``wscript.exe pdft_gui.vbs`` (which sets up the venv + PYTHONPATH); a frozen
PyInstaller build points at the running ``.exe`` directly (the vbs/bat are not
bundled and ``_MEIPASS`` is a volatile temp dir).
"""

from __future__ import annotations

import contextlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # Real on Windows; absent elsewhere — guarded by is_supported().
    import winreg
except ImportError:  # pragma: no cover - non-Windows import path
    winreg = None  # type: ignore[assignment]

log = logging.getLogger("pdf_toolkit")

PROGID = "pdf-toolkit.Viewer"
PROGID_LABEL = "PDF (pdf-toolkit viewer)"
PROGID_ICON = r"%SystemRoot%\System32\shell32.dll,1"
EXT = ".pdf"
LAUNCHER_VBS = "pdft_gui.vbs"

_CLASSES = r"Software\Classes"
PROGID_KEY = rf"{_CLASSES}\{PROGID}"
ICON_KEY = rf"{PROGID_KEY}\DefaultIcon"
_SHELL_KEY = rf"{PROGID_KEY}\shell"
_OPEN_KEY = rf"{_SHELL_KEY}\open"
COMMAND_KEY = rf"{_OPEN_KEY}\command"
OPENWITH_KEY = rf"{_CLASSES}\{EXT}\OpenWithProgids"

_NOT_WINDOWS_ERROR = "Setting the default PDF viewer is only supported on Windows."
_NO_LAUNCHER_ERROR = f"Launcher not found ({LAUNCHER_VBS}); cannot register."


@dataclass(frozen=True)
class RegistrationResult:
    """Outcome of a register / unregister attempt. Never raised — always returned."""

    ok: bool
    progid: str
    launch_command: str
    is_windows: bool
    error: str | None = None


def is_supported() -> bool:
    """True only on Windows (the registry approach is HKCU-specific)."""
    return sys.platform == "win32"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _repo_root() -> Path:
    """Project root in a source checkout (…/app/os_integration/this.py → root)."""
    return Path(__file__).resolve().parents[2]


def launch_command(root: Path | None = None) -> str:
    """Return the ``shell\\open\\command`` string for the current install.

    Frozen builds launch the exe directly; source runs go through the windowless
    ``pdft_gui.vbs`` launcher at the project root.
    """
    if _is_frozen():
        return f'"{sys.executable}" "%1"'
    base = root if root is not None else _repo_root()
    return f'wscript.exe "{base / LAUNCHER_VBS}" "%1"'


def register_pdf_viewer(root: Path | None = None) -> RegistrationResult:
    """Write the HKCU ProgID + OpenWithProgids keys. Idempotent; never raises."""
    command = launch_command(root)
    if not is_supported():
        return RegistrationResult(False, PROGID, command, False, _NOT_WINDOWS_ERROR)
    if not _is_frozen():
        base = root if root is not None else _repo_root()
        if not (base / LAUNCHER_VBS).exists():
            return RegistrationResult(False, PROGID, command, True, _NO_LAUNCHER_ERROR)
    try:
        _set_default(PROGID_KEY, PROGID_LABEL)
        _set_default(ICON_KEY, PROGID_ICON)
        _set_default(COMMAND_KEY, command)
        _add_open_with()
    except OSError as err:
        log.warning("failed to register PDF viewer: %s", err)
        return RegistrationResult(False, PROGID, command, True, str(err))
    log.info("registered PDF viewer progid=%s command=%s", PROGID, command)
    return RegistrationResult(True, PROGID, command, True)


def unregister_pdf_viewer() -> RegistrationResult:
    """Delete the keys created by :func:`register_pdf_viewer`. Never raises."""
    command = launch_command()
    if not is_supported():
        return RegistrationResult(False, PROGID, command, False, _NOT_WINDOWS_ERROR)
    try:
        _delete_value(OPENWITH_KEY, PROGID)
        # winreg.DeleteKey only removes empty keys, so delete deepest-first.
        for key in (COMMAND_KEY, _OPEN_KEY, _SHELL_KEY, ICON_KEY, PROGID_KEY):
            _delete_key(key)
    except OSError as err:
        log.warning("failed to unregister PDF viewer: %s", err)
        return RegistrationResult(False, PROGID, command, True, str(err))
    log.info("unregistered PDF viewer progid=%s", PROGID)
    return RegistrationResult(True, PROGID, command, True)


def _set_default(subkey: str, value: str) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)


def _add_open_with() -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, OPENWITH_KEY, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, PROGID, 0, winreg.REG_NONE, b"")


def _delete_key(subkey: str) -> None:
    """Delete a key, treating an already-absent key as success (idempotent)."""
    with contextlib.suppress(FileNotFoundError):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, subkey)


def _delete_value(subkey: str, name: str) -> None:
    """Delete a value, treating an absent key/value as success (idempotent)."""
    with (
        contextlib.suppress(FileNotFoundError),
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_WRITE) as key,
    ):
        winreg.DeleteValue(key, name)
