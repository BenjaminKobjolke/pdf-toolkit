"""The current release identity: version (pyproject) + build (build file).

``version`` is read from installed package metadata, falling back to parsing
``pyproject.toml`` from a source checkout. ``build`` is read through the frozen-
aware bundled root so it works both from source and inside the PyInstaller exe.
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from app.release.build_number import read_build
from app.release.schema import BUILD_FILE_NAME

_PACKAGE_NAME = "pdf-toolkit"
_FALLBACK_VERSION = "0.0.0"


@dataclass(frozen=True)
class ReleaseId:
    """Version + build identity for the running application."""

    version: str
    build: int

    @property
    def label(self) -> str:
        """The ``<version>_<build>`` folder/label string, e.g. ``0.1.0_22``."""
        return f"{self.version}_{self.build}"


def _version_from_pyproject() -> str:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.exists():
        return _FALLBACK_VERSION
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    return str(project.get("version", _FALLBACK_VERSION))


def current_version() -> str:
    """The installed package version, or the pyproject value in a source checkout."""
    try:
        return metadata.version(_PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return _version_from_pyproject()


def current_build() -> int:
    """The build number, resolved through the frozen-aware bundled root."""
    from app.gui.resources import bundled_root

    return read_build(bundled_root() / BUILD_FILE_NAME)


def current_release() -> ReleaseId:
    """Bundle the live version and build into a :class:`ReleaseId`."""
    return ReleaseId(current_version(), current_build())


def main(argv: list[str] | None = None) -> int:
    """CLI entry: print the current ``<version>_<build>`` label."""
    print(current_release().label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
