"""Loader for the fman-style favorites file (``Name|Path`` per line).

The file is shared with other tools (fman's GoTo favorites), so this module
only reads it — it never writes. Missing or unreadable files degrade to an
empty list, matching the project's other optional global stores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FavoriteDir:
    """One favorites entry: a display name and the directory it points to."""

    name: str
    path: Path


def load_favorites(file: Path) -> list[FavoriteDir]:
    """Parse ``Name|Path`` lines from ``file``; ``[]`` when missing/unreadable.

    Skips blank/malformed lines and fman-internal ``{{…}}`` placeholder paths
    (unresolvable outside fman). ``~`` prefixes are expanded to the home dir.
    """
    try:
        text = file.read_text(encoding="utf-8")
    except OSError:
        return []
    favorites: list[FavoriteDir] = []
    for line in text.splitlines():
        name, sep, raw_path = line.strip().partition("|")
        if not sep or not name or not raw_path or "{{" in raw_path:
            continue
        favorites.append(FavoriteDir(name=name, path=Path(raw_path).expanduser()))
    return favorites
