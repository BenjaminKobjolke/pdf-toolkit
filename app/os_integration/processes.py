"""Enumerate running processes with resolvable executable paths.

Used by the "Open with" command to let the user add an application by picking a
process that is already running instead of hunting for its ``.exe``. Returns a
typed value object (never a bag-of-keys dict), deduplicated by executable path
since many processes share one binary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class RunningApp:
    """A running application: its display name and its executable path."""

    name: str
    path: Path


def running_apps() -> list[RunningApp]:
    """Distinct running processes that expose a readable exe path, sorted by name."""
    seen: dict[Path, RunningApp] = {}
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            exe = proc.info["exe"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):  # gone / no rights to read it
            continue
        if not exe:  # kernel/system processes report no executable
            continue
        path = Path(exe)
        seen.setdefault(path, RunningApp(proc.info["name"] or path.stem, path))
    return sorted(seen.values(), key=lambda app: app.name.casefold())
