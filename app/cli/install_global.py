"""Install the toolkit's bat wrappers into a PATH-listed directory."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE
from app.config.settings import Settings
from app.logging_setup import configure_logging

DEFAULT_TARGET = Path(r"C:\cmdtools")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Single source of truth: which bats get installed and which module each invokes.
BAT_FILES: tuple[tuple[str, str], ...] = (
    ("pdf-swap-pages.bat", "app.cli.swap"),
    ("pdf-delete-page.bat", "app.cli.delete_page"),
)

log = logging.getLogger("pdf_toolkit")


class InstallError(Exception):
    """Raised when bat installation fails for a domain reason."""


def render_bat(project_root: Path, module: str) -> str:
    """Return the contents of a global wrapper bat that calls ``module`` in this project.

    The generated bat preserves the user's CWD so relative path arguments resolve
    against the directory the user invoked the bat from.
    """
    root_str = str(project_root).replace("/", "\\")
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        f'set "PROJECT_ROOT={root_str}"\r\n'
        'set "PYTHONPATH=%PROJECT_ROOT%"\r\n'
        f'"%PROJECT_ROOT%\\.venv\\Scripts\\python.exe" -m {module} %*\r\n'
        "exit /b %ERRORLEVEL%\r\n"
    )


def install_bats(project_root: Path, target_dir: Path, overwrite: bool) -> list[Path]:
    """Write the global wrapper bats into ``target_dir``. Return the list of paths written."""
    if not target_dir.exists():
        raise InstallError(f"target directory does not exist: {target_dir}")
    if not target_dir.is_dir():
        raise InstallError(f"target is not a directory: {target_dir}")

    if not overwrite:
        existing = [target_dir / name for name, _ in BAT_FILES if (target_dir / name).exists()]
        if existing:
            joined = ", ".join(p.name for p in existing)
            raise InstallError(f"these files already exist in {target_dir}: {joined}")

    written: list[Path] = []
    for name, module in BAT_FILES:
        path = target_dir / name
        path.write_text(render_bat(project_root, module), encoding="utf-8", newline="")
        written.append(path)
    return written


def _read_target_from_stdin() -> Path:
    raw = input(f"Install target directory [{DEFAULT_TARGET}]: ").strip()
    return Path(raw) if raw else DEFAULT_TARGET


def _confirm_overwrite(existing_names: list[str]) -> bool:
    print("These files already exist:")
    for name in existing_names:
        print(f"  - {name}")
    answer = input("Overwrite? [y/N]: ").strip().lower()
    return answer == "y"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-install-global",
        description="Install pdf-toolkit bat wrappers into a directory on your PATH.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        help="Target directory. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting.",
    )
    return parser.parse_args(argv)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    target: Path = args.target if args.target is not None else _read_target_from_stdin()

    try:
        written = install_bats(PROJECT_ROOT, target, overwrite=args.force)
    except InstallError as err:
        if "already exist" in str(err) and not args.force:
            existing = [name for name, _ in BAT_FILES if (target / name).exists()]
            if not _confirm_overwrite(existing):
                log.error("aborted; nothing installed")
                return EXIT_FAILURE
            try:
                written = install_bats(PROJECT_ROOT, target, overwrite=True)
            except InstallError as err2:
                log.error("%s", err2)
                return EXIT_FAILURE
        else:
            log.error("%s", err)
            return EXIT_FAILURE

    print(f"Installed {len(written)} bat wrapper(s) in {target}:")
    for path in written:
        print(f"  - {path.name}")
    print(f"Project root referenced by the wrappers: {PROJECT_ROOT}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
