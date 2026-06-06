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
from app.pdf.merger import MERGED_FILENAME, find_existing_merged

log = logging.getLogger("pdf_toolkit")


@dataclass(frozen=True)
class OpResult:
    """Outcome of a GUI operation, carrying a message for the user."""

    ok: bool
    message: str


def back_up(source: Path, backup_dir: Path) -> OpResult | None:
    """Back up ``source`` into ``backup_dir``.

    Returns ``None`` on success or an error :class:`OpResult` if the copy fails,
    so callers in both the runner and :class:`~app.gui.working_document.WorkingDocument`
    share one backup error path.
    """
    try:
        backup_path = create_backup(source, backup_dir)
    except OSError as err:
        log.error("failed to create backup: %s", err)
        return OpResult(False, strings.MSG_BACKUP_FAILED_FMT.format(error=err))
    log.info("backup written: %s", backup_path)
    return None


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

    def run_on_working(self, working: Path, op: Callable[[Path], None]) -> OpResult:
        """Run ``op`` on the temp working copy with no backup.

        Page ops mutate the working copy, not the original; the single backup
        happens later in :meth:`WorkingDocument.save`.
        """
        if not working.is_file():
            return OpResult(False, strings.MSG_NOT_FOUND_FMT.format(path=working))
        return self._run(op, working, strings.MSG_DONE_FMT.format(name=working.name))

    def run_to_new_file(self, source: Path, op: Callable[[Path], None]) -> OpResult:
        """Run ``op`` on ``source`` with no backup (``op`` writes a separate new file).

        Used by extract, which leaves ``source`` untouched, so the timestamped
        backup the in-place ops make is unnecessary.
        """
        if not source.is_file():
            return OpResult(False, strings.MSG_NOT_FOUND_FMT.format(path=source))
        return self._run(op, source, strings.MSG_DONE_FMT.format(name=source.name))

    def run_folder_merge(self, folder: Path, op: Callable[[Path], None]) -> OpResult:
        """Validate ``folder``, back up an existing merged.pdf, then run ``op``."""
        if not folder.is_dir():
            return OpResult(False, strings.MSG_NOT_FOUND_FMT.format(path=folder))

        existing = find_existing_merged(folder)
        if existing is not None:
            backup = self._back_up(existing)
            if backup is not None and not backup.ok:
                return backup

        merged = folder / MERGED_FILENAME
        return self._run(op, folder, strings.MSG_MERGED_FMT.format(path=merged))

    def _back_up(self, source: Path) -> OpResult | None:
        return back_up(source, self._settings.backup_dir)

    def _run(self, op: Callable[[Path], None], target: Path, success: str) -> OpResult:
        try:
            op(target)
        except (ValueError, OSError) as err:
            log.error("%s", err)
            return OpResult(False, str(err))
        log.info("%s", success)
        return OpResult(True, success)
