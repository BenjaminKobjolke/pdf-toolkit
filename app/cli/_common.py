"""Shared CLI orchestration: backup + run an operation, with a single error boundary."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from app.app_logger import configure_logging, log
from app.config.settings import Settings
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


def _require_file(source: Path) -> int | None:
    """Exit code if ``source`` is not an existing file, else None."""
    if not source.is_file():
        log.error("input file not found: %s", source)
        return EXIT_USAGE
    return None


def _make_backup(path: Path, settings: Settings, fail_message: str) -> int | None:
    """Back up ``path``; return an exit code on failure, else None."""
    try:
        backup_path = create_backup(path, settings.backup_dir)
    except OSError as err:
        log.error("%s: %s", fail_message, err)
        return EXIT_FAILURE
    log.info("backup written: %s", backup_path)
    return None


def _execute(
    target: Path,
    op: Callable[[Path], None],
    *,
    verb: str = "processing",
    done: Path | None = None,
) -> int:
    """Run ``op`` inside the shared error boundary; log ``done`` (default: target)."""
    try:
        op(target)
    except ValueError as err:
        log.error("%s", err)
        return EXIT_FAILURE
    except OSError as err:
        log.error("I/O error while %s %s: %s", verb, target, err)
        return EXIT_FAILURE

    log.info("done: %s", done if done is not None else target)
    return EXIT_OK


def run_with_backup(
    source: Path,
    op: Callable[[Path], None],
    settings: Settings,
) -> int:
    """Validate, back up, then run ``op`` on ``source``. Return a process exit code."""
    code = _require_file(source)
    if code is not None:
        return code
    code = _make_backup(source, settings, "failed to create backup")
    if code is not None:
        return code
    return _execute(source, op)


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
    code = _require_file(source)
    if code is not None:
        return code
    return _execute(source, op)


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
        code = _make_backup(existing, settings, "failed to back up existing merged.pdf")
        if code is not None:
            return code

    return _execute(folder, op, verb="merging", done=merged_output_path(folder))
