"""GUI operation boundary: backup + run a core op, returning a message object.

Mirrors ``app.cli._common`` but returns a user-facing :class:`OpResult` instead
of an exit code, because the GUI surfaces error messages in a dialog. The
reusable unit — :func:`app.pdf.backup.create_backup` — is shared, not duplicated.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.config.settings import Settings
from app.gui import strings
from app.pdf.backup import create_backup
from app.pdf.merger import MERGED_FILENAME

log = logging.getLogger("pdf_toolkit")


@dataclass(frozen=True)
class OpResult:
    """Outcome of a GUI operation, carrying a message for the user."""

    ok: bool
    message: str


class GuiOperationRunner:
    """Run core PDF ops with a backup and turn failures into :class:`OpResult`."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def run_on_file(self, source: Path, op: Callable[[Path], None]) -> OpResult:
        """Validate ``source``, back it up, then run ``op`` on it."""
        if not source.is_file():
            return OpResult(False, strings.MSG_NOT_FOUND_FMT.format(path=source))

        backup = self._back_up(source)
        if backup is not None and not backup.ok:
            return backup

        return self._run(op, source, strings.MSG_DONE_FMT.format(name=source.name))

    def run_folder_merge(self, folder: Path, op: Callable[[Path], None]) -> OpResult:
        """Validate ``folder``, back up an existing merged.pdf, then run ``op``."""
        if not folder.is_dir():
            return OpResult(False, strings.MSG_NOT_FOUND_FMT.format(path=folder))

        existing = self._find_existing_merged(folder)
        if existing is not None:
            backup = self._back_up(existing)
            if backup is not None and not backup.ok:
                return backup

        merged = folder / MERGED_FILENAME
        return self._run(op, folder, strings.MSG_MERGED_FMT.format(path=merged))

    def _back_up(self, source: Path) -> OpResult | None:
        try:
            backup_path = create_backup(source, self._settings.backup_dir)
        except OSError as err:
            log.error("failed to create backup: %s", err)
            return OpResult(False, strings.MSG_BACKUP_FAILED_FMT.format(error=err))
        log.info("backup written: %s", backup_path)
        return None

    def _run(self, op: Callable[[Path], None], target: Path, success: str) -> OpResult:
        try:
            op(target)
        except (ValueError, OSError) as err:
            log.error("%s", err)
            return OpResult(False, str(err))
        log.info("%s", success)
        return OpResult(True, success)

    @staticmethod
    def _find_existing_merged(folder: Path) -> Path | None:
        for entry in folder.iterdir():
            if entry.is_file() and entry.name.lower() == MERGED_FILENAME.lower():
                return entry
        return None
