"""Load release notes from the ``release_notes/<version>_<build>/`` tree.

Each release folder holds one JSON file per locale (``en.json`` plus any
translations). This reads the requested locale (falling back to ``en``), parses
each folder, and returns typed :class:`ReleaseNote` objects sorted newest-first
so the dialog can show the latest release before older ones.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.logging_setup import log
from app.release import schema


@dataclass(frozen=True)
class ReleaseNote:
    """One release's notes, resolved for a single locale."""

    version: str
    build: int
    date: str
    title: str
    notes: tuple[str, ...]

    @property
    def label(self) -> str:
        """The ``<version>_<build>`` label string."""
        return f"{self.version}_{self.build}"


def _parse_folder_name(name: str) -> tuple[str, int] | None:
    """Split ``<version>_<build>`` into ``(version, build)``; ``None`` if malformed."""
    version, sep, build_text = name.rpartition("_")
    if not sep or not version:
        return None
    try:
        return version, int(build_text)
    except ValueError:
        return None


def _version_key(version: str) -> tuple[int, ...]:
    """Sortable numeric key for a dotted version; non-numeric parts sort as 0."""
    parts: list[int] = []
    for piece in version.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _read_locale(folder: Path, locale: str) -> dict[str, object] | None:
    """Read ``<locale>.json``, falling back to ``en.json``; ``None`` if neither."""
    for name in (locale, schema.DEFAULT_LOCALE):
        candidate = folder / schema.LOCALE_FILE_FMT.format(locale=name)
        if candidate.exists():
            try:
                loaded = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                log.warning("Malformed release notes JSON: %s", candidate)
                return None
            return loaded if isinstance(loaded, dict) else None
    return None


def _to_note(data: dict[str, object], version: str, build: int) -> ReleaseNote:
    """Build a :class:`ReleaseNote`, preferring JSON fields over folder-derived ones."""
    raw_notes = data.get(schema.KEY_NOTES, [])
    notes = tuple(str(item) for item in raw_notes) if isinstance(raw_notes, list) else ()
    raw_build = data.get(schema.KEY_BUILD, build)
    return ReleaseNote(
        version=str(data.get(schema.KEY_VERSION, version)),
        build=int(raw_build) if isinstance(raw_build, int | str) else build,
        date=str(data.get(schema.KEY_DATE, "")),
        title=str(data.get(schema.KEY_TITLE, "")),
        notes=notes,
    )


def load_release_notes(
    locale: str = schema.DEFAULT_LOCALE, root: Path | None = None
) -> list[ReleaseNote]:
    """Return all release notes for ``locale``, newest first (``[]`` when none)."""
    if root is None:
        from app.gui.resources import release_notes_dir

        root = release_notes_dir()
    if not root.is_dir():
        return []
    notes: list[ReleaseNote] = []
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        parsed = _parse_folder_name(folder.name)
        if parsed is None:
            continue
        data = _read_locale(folder, locale)
        if data is None:
            continue
        notes.append(_to_note(data, parsed[0], parsed[1]))
    notes.sort(key=lambda note: (_version_key(note.version), note.build), reverse=True)
    return notes
