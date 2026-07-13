"""Shared CLI orchestration: backup + run an operation, with a single error boundary."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from app.config.settings import Settings
from app.logging_setup import configure_logging, log
from app.pdf.backup import create_backup
from app.pdf.merger import find_existing_merged, merged_output_path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_FAILURE = 1


# Type of a runner like ``run_with_backup`` / ``run_folder_merge``.
CliRunner = Callable[[Path, Callable[[Path], None], Settings], int]


def run_cli(
    parse: Callable[[list[str]], argparse.Namespace],
    target: Callable[[argparse.Namespace], Path],
    op: Callable[[argparse.Namespace], Callable[[Path], None]],
    runner: CliRunner | None = None,
) -> int:
    """Shared ``main()`` body for the CLI entry points.

    Loads settings, configures logging, parses ``sys.argv`` (turning argparse's
    ``SystemExit`` into an exit code), then runs ``op(args)`` on ``target(args)``
    via ``runner`` (default :func:`run_with_backup`). Keeps every ``app.cli.*``
    ``main()`` from repeating the same five lines.
    """
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = parse(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE
    return (runner or run_with_backup)(target(args), op(args), settings)


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


def run_to_new_file(
    source: Path,
    op: Callable[[Path], None],
    settings: Settings,
) -> int:
    """Validate ``source`` then run ``op`` with no backup (``op`` writes a new file).

    Used by operations like extract that leave ``source`` untouched, so the
    timestamped backup the in-place ops make is unnecessary. ``settings`` is
    accepted to match the :data:`CliRunner` signature.
    """
    if not source.is_file():
        log.error("input file not found: %s", source)
        return EXIT_USAGE

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

    existing = find_existing_merged(folder)
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

    log.info("done: %s", merged_output_path(folder))
    return EXIT_OK
