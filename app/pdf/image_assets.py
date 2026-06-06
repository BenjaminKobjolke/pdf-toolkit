"""Asset-folder handling for placed images.

Images are either copied into an ``assets/`` subfolder next to the PDF (stored as
a relative ``assets/<name>`` path) or referenced at their absolute location. Both
the on-screen pixmap and the fitz flatten resolve paths against the *original*
PDF's directory, never the temp working copy. Pure pathlib/shutil — no Qt, no
fitz — so it is unit-testable in isolation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ASSETS_DIRNAME = "assets"


def assets_dir(base_dir: Path) -> Path:
    """Return the ``assets/`` directory for a PDF living in ``base_dir``."""
    return base_dir / ASSETS_DIRNAME


def copy_into_assets(src: Path, base_dir: Path) -> str:
    """Copy ``src`` into ``base_dir/assets/`` and return its relative path.

    Creates the assets directory if needed. If a different file already occupies
    the target name, a numeric suffix (``name_1.png``, ``name_2.png`` …) is used
    so an existing asset is never overwritten. The returned string is always
    ``assets/<name>`` (POSIX separators) for portable storage in the sidecar.
    """
    target_dir = assets_dir(base_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    name = _unique_name(src, target_dir)
    shutil.copy2(src, target_dir / name)
    return f"{ASSETS_DIRNAME}/{name}"


def resolve_image_path(path: str, absolute: bool, base_dir: Path) -> Path:
    """Resolve a stored image path to an absolute filesystem path.

    Absolute references are returned as-is; relative (assets) paths are resolved
    against ``base_dir`` (the original PDF's directory).
    """
    if absolute:
        return Path(path)
    return base_dir / path


def _unique_name(src: Path, target_dir: Path) -> str:
    """Return a filename for ``src`` in ``target_dir`` that collides with nothing."""
    candidate = target_dir / src.name
    if not candidate.exists():
        return src.name
    stem, suffix = src.stem, src.suffix
    index = 1
    while (target_dir / f"{stem}_{index}{suffix}").exists():
        index += 1
    return f"{stem}_{index}{suffix}"
