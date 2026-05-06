"""Shared CLI orchestration: backup + run an operation, with a single error boundary."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from app.config.settings import Settings
from app.pdf.backup import create_backup
from app.pdf.merger import MERGED_FILENAME

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


def run_folder_merge(
    folder: Path,
    op: Callable[[Path], None],
    settings: Settings,
) -> int:
    """Validate folder, back up an existing merged.pdf if present, then run ``op``."""
    if not folder.is_dir():
        log.error("folder not found: %s", folder)
        return EXIT_USAGE

    existing = _find_existing_merged(folder)
    if existing is not None:
        try:
            backup_path = create_backup(existing, settings.backup_dir)
        except OSError as err:
            log.error("failed to back up existing merged.pdf: %s", err)
            return EXIT_FAILURE
        log.info("backup written: %s", backup_path)

    try:
        op(folder)
    except ValueError as err:
        log.error("%s", err)
        return EXIT_FAILURE
    except OSError as err:
        log.error("I/O error while merging %s: %s", folder, err)
        return EXIT_FAILURE

    log.info("done: %s", folder / MERGED_FILENAME)
    return EXIT_OK


def _find_existing_merged(folder: Path) -> Path | None:
    """Return the existing merged.pdf in ``folder`` (case-insensitive on Windows)."""
    for entry in folder.iterdir():
        if entry.is_file() and entry.name.lower() == MERGED_FILENAME.lower():
            return entry
    return None
