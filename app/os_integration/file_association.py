"""Associate the GUI viewer with its supported file types on Windows.

Declarative HKCU (no admin) registration: :func:`set_associations` takes the
full set of extensions that should be associated and makes the registry match —
registering the checked ones, unregistering the rest, and tearing everything
down when the set is empty.

What registration does and does NOT do:

* It writes a per-user ProgID ``pdf-toolkit.Viewer``, adds it to each
  extension's *Open with* list, and registers the app (with its file-type
  capabilities) under ``RegisteredApplications`` so it appears as
  "FastFileViewer" in the Windows Default Apps page.
* It does **not** silently set the default. Windows 8+/10/11 guard the active
  association (``<ext>\\UserChoice``) with a per-user signed hash that no third
  party can forge, so the user must finish in the Default Apps UI.

The ``shell\\open\\command`` value differs by build: a dev/source run points at
``wscript.exe FastFileViewer.vbs`` (which sets up the venv + PYTHONPATH); a frozen
PyInstaller build points at the running ``.exe`` directly (the vbs/bat are not
bundled and ``_MEIPASS`` is a volatile temp dir).

Also usable as a CLI (consumed by the repo-root register/unregister bats):
``python -m app.os_integration.file_association register|unregister``.
"""

from __future__ import annotations

import contextlib
import sys
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from app.app_logger import log
from app.pdf.file_format import FileFormat

try:  # Real on Windows; absent elsewhere — guarded by is_supported().
    import winreg
except ImportError:  # pragma: no cover - non-Windows import path
    winreg = None  # type: ignore[assignment]


PROGID = "pdf-toolkit.Viewer"  # unchanged from the PDF-only era: zero migration
APP_NAME = "FastFileViewer"
PROGID_LABEL = APP_NAME
PROGID_ICON = r"%SystemRoot%\System32\shell32.dll,1"
LAUNCHER_VBS = "FastFileViewer.vbs"
ALL_EXTENSIONS: tuple[str, ...] = tuple(f.value for f in FileFormat)

_CLASSES = r"Software\Classes"
PROGID_KEY = rf"{_CLASSES}\{PROGID}"
ICON_KEY = rf"{PROGID_KEY}\DefaultIcon"
_SHELL_KEY = rf"{PROGID_KEY}\shell"
_OPEN_KEY = rf"{_SHELL_KEY}\open"
COMMAND_KEY = rf"{_OPEN_KEY}\command"
_APP_KEY = rf"Software\{APP_NAME}"
CAPABILITIES_KEY = rf"{_APP_KEY}\Capabilities"
FILE_ASSOC_KEY = rf"{CAPABILITIES_KEY}\FileAssociations"
REGISTERED_APPS_KEY = r"Software\RegisteredApplications"
_APP_DESCRIPTION = "Fast viewer for PDF, text, markdown and image files."

_NOT_WINDOWS_ERROR = "File type associations are only supported on Windows."
_NO_LAUNCHER_ERROR = f"Launcher not found ({LAUNCHER_VBS}); cannot register."


@dataclass(frozen=True)
class RegistrationResult:
    """Outcome of an association attempt. Never raised — always returned."""

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
    ``FastFileViewer.vbs`` launcher at the project root.
    """
    if _is_frozen():
        return f'"{sys.executable}" "%1"'
    base = root if root is not None else _repo_root()
    return f'wscript.exe "{base / LAUNCHER_VBS}" "%1"'


def _openwith_key(ext: str) -> str:
    return rf"{_CLASSES}\{ext}\OpenWithProgids"


def registered_extensions() -> frozenset[str]:
    """Extensions currently carrying our *Open with* entry. Never raises."""
    if not is_supported():
        return frozenset()
    found: set[str] = set()
    for ext in ALL_EXTENSIONS:
        # Value *presence* is the signal — REG_NONE data reads back as (b"", 0).
        with (
            contextlib.suppress(OSError),
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, _openwith_key(ext)) as key,
        ):
            winreg.QueryValueEx(key, PROGID)
            found.add(ext)
    return frozenset(found)


def set_associations(checked: Collection[str], root: Path | None = None) -> RegistrationResult:
    """Make the registry match ``checked`` exactly. Idempotent; never raises.

    Registers every extension in ``checked``, unregisters the rest of
    :data:`ALL_EXTENSIONS`, and tears the whole registration down (ProgID,
    Capabilities, RegisteredApplications) when ``checked`` is empty.
    """
    command = launch_command(root)
    checked_set = frozenset(checked)
    if not is_supported():
        return RegistrationResult(False, PROGID, command, False, _NOT_WINDOWS_ERROR)
    if checked_set and not _is_frozen():
        base = root if root is not None else _repo_root()
        if not (base / LAUNCHER_VBS).exists():
            return RegistrationResult(False, PROGID, command, True, _NO_LAUNCHER_ERROR)
    try:
        if checked_set:
            _write_registration(checked_set, command)
        else:
            _remove_registration()
    except OSError as err:
        log.warning("failed to set file associations: %s", err)
        return RegistrationResult(False, PROGID, command, True, str(err))
    log.info("file associations set: %s", sorted(checked_set) or "none")
    return RegistrationResult(True, PROGID, command, True)


def _write_registration(checked: frozenset[str], command: str) -> None:
    """Write ProgID + Capabilities, then reconcile every extension."""
    _set_default(PROGID_KEY, PROGID_LABEL)
    _set_default(ICON_KEY, PROGID_ICON)
    _set_default(COMMAND_KEY, command)
    _set_value(CAPABILITIES_KEY, "ApplicationName", APP_NAME)
    _set_value(CAPABILITIES_KEY, "ApplicationDescription", _APP_DESCRIPTION)
    _set_value(REGISTERED_APPS_KEY, APP_NAME, CAPABILITIES_KEY)
    for ext in ALL_EXTENSIONS:
        if ext in checked:
            _add_open_with(ext)
            _set_value(FILE_ASSOC_KEY, ext, PROGID)
        else:
            _delete_value(_openwith_key(ext), PROGID)
            _delete_value(FILE_ASSOC_KEY, ext)


def _remove_registration() -> None:
    """Delete everything :func:`_write_registration` may have created."""
    for ext in ALL_EXTENSIONS:
        _delete_value(_openwith_key(ext), PROGID)
    _delete_value(REGISTERED_APPS_KEY, APP_NAME)
    # winreg.DeleteKey only removes empty keys, so delete deepest-first.
    for key in (FILE_ASSOC_KEY, CAPABILITIES_KEY, _APP_KEY):
        _delete_key(key)
    for key in (COMMAND_KEY, _OPEN_KEY, _SHELL_KEY, ICON_KEY, PROGID_KEY):
        _delete_key(key)


def _set_default(subkey: str, value: str) -> None:
    _set_value(subkey, "", value)


def _set_value(subkey: str, name: str, value: str) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _add_open_with(ext: str) -> None:
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, _openwith_key(ext), 0, winreg.KEY_WRITE
    ) as key:
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


def _main(argv: list[str], root: Path | None = None) -> int:
    """CLI for the repo-root bats: ``register`` = all types, ``unregister`` = none."""
    verb = argv[0] if argv else ""
    if verb == "register":
        result = set_associations(ALL_EXTENSIONS, root)
    elif verb == "unregister":
        result = set_associations(frozenset(), root)
    else:
        sys.stderr.write(
            "usage: python -m app.os_integration.file_association register|unregister\n"
        )
        return 2
    if not result.ok:
        sys.stderr.write(f"{result.error}\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via _main tests
    raise SystemExit(_main(sys.argv[1:]))
