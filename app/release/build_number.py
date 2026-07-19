"""Read/write the integer build number stored in ``build_version.txt`` (root).

The build number pairs with pyproject's ``version`` to form the release label
``<version>_<build>``. The ``tools/build_*.bat`` wrappers call this module's
``__main__`` (``get`` / ``increment`` / ``decrement``); the GUI reads it at
runtime via :mod:`app.release.release_info`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.app_logger import log
from app.release.schema import BUILD_FILE_NAME

# Counter = last shipped build; 0 = nothing shipped yet (bump-first, ship-next).
_DEFAULT_BUILD = 0
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_file() -> Path:
    """Path to ``build_version.txt`` at the project root (dev checkout)."""
    return _PROJECT_ROOT / BUILD_FILE_NAME


def read_build(path: Path | None = None) -> int:
    """Return the stored build number, or the default when absent/unreadable."""
    target = path or build_file()
    if not target.exists():
        return _DEFAULT_BUILD
    raw = target.read_text(encoding="utf-8").strip()
    try:
        return int(raw)
    except ValueError:
        log.warning("Invalid build number %r in %s; using %d", raw, target, _DEFAULT_BUILD)
        return _DEFAULT_BUILD


def write_build(value: int, path: Path | None = None) -> None:
    """Persist ``value`` (must be >= 0) to the build file."""
    if value < 0:
        raise ValueError(f"build number must be >= 0, got {value}")
    (path or build_file()).write_text(f"{value}\n", encoding="utf-8")


def increment(path: Path | None = None) -> int:
    """Raise the build number by one and return the new value."""
    value = read_build(path) + 1
    write_build(value, path)
    return value


def decrement(path: Path | None = None) -> int:
    """Lower the build number by one (floored at 0) and return the new value."""
    value = max(0, read_build(path) - 1)
    write_build(value, path)
    return value


_COMMANDS = {"get": read_build, "increment": increment, "decrement": decrement}


def main(argv: list[str] | None = None) -> int:
    """CLI entry: print the build number for ``get`` / ``increment`` / ``decrement``."""
    args = sys.argv[1:] if argv is None else argv
    action = args[0] if args else "get"
    handler = _COMMANDS.get(action)
    if handler is None:
        print(f"usage: python -m app.release.build_number [{'|'.join(_COMMANDS)}]")
        return 2
    print(handler())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
