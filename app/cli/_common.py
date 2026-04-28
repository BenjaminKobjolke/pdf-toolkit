"""Shared CLI orchestration: backup + run an operation, with a single error boundary."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from app.config.settings import Settings
from app.pdf.backup import create_backup

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_FAILURE = 1

log = logging.getLogger("pdf_toolkit")


def run_with_backup(
    source: Path,
    op: Callable[[Path], None],
    settings: Settings,
) -> int:
    """Validate, back up, then run ``op`` on ``source``. Return a process exit code."""
    if not source.is_file():
        log.error("input file not found: %s", source)
        return EXIT_USAGE

    try:
        backup_path = create_backup(source, settings.backup_dir)
    except OSError as err:
        log.error("failed to create backup: %s", err)
        return EXIT_FAILURE
    log.info("backup written: %s", backup_path)

    try:
        op(source)
    except ValueError as err:
        log.error("%s", err)
        return EXIT_FAILURE
    except OSError as err:
        log.error("I/O error while processing %s: %s", source, err)
        return EXIT_FAILURE

    log.info("done: %s", source)
    return EXIT_OK
