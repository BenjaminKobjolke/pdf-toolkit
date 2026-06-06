"""Owns the temporary working copy of an open document.

A working copy is the pair *(working PDF, working JSON sidecar)* in a per-session
temp directory. Page operations and text-field autosaves mutate this copy; the
original PDF and its sidecar are untouched until :meth:`save`, which backs the
original up once and propagates both files. This is what makes every edit
deferred until the user explicitly saves.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import tempfile
from pathlib import Path

from app.config.settings import Settings
from app.gui import strings
from app.gui.operations import OpResult, back_up
from app.pdf.sidecar import sidecar_path

log = logging.getLogger("pdf_toolkit")

_TMP_SUFFIX = ".tmp"


class WorkingDocument:
    """The temp PDF + sidecar pair backing the open document, with a dirty flag."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._original: Path | None = None
        self._working: Path | None = None
        self._dirty = False

    def open(self, original: Path) -> Path:
        """Copy ``original`` (and its sidecar, if any) into a fresh temp dir.

        Returns the working PDF path. Resets the dirty flag.
        """
        self.close()
        tmp_dir = Path(tempfile.mkdtemp(prefix="pdftk-"))
        working = tmp_dir / original.name
        shutil.copy2(original, working)
        original_sidecar = sidecar_path(original)
        if original_sidecar.is_file():
            shutil.copy2(original_sidecar, sidecar_path(working))
        self._original = original
        self._working = working
        self._dirty = False
        return working

    def original(self) -> Path | None:
        return self._original

    def working(self) -> Path | None:
        return self._working

    def is_dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        self._dirty = True

    def discard(self) -> None:
        """Drop the dirty flag without saving; the temp edits are abandoned on close."""
        self._dirty = False

    def save(self) -> OpResult:
        """Back up the original once, then copy the working PDF + sidecar onto it."""
        if self._original is None or self._working is None:
            return OpResult(False, strings.MSG_NO_DOCUMENT)

        failure = back_up(self._original, self._settings.backup_dir)
        if failure is not None:
            return failure

        try:
            self._replace_atomic(self._working, self._original)
            self._propagate_sidecar()
        except OSError as err:
            log.error("failed to save changes: %s", err)
            return OpResult(False, str(err))

        self._dirty = False
        return OpResult(True, strings.MSG_SAVED_FMT.format(name=self._original.name))

    def close(self) -> None:
        """Delete the working PDF + sidecar (and the temp dir) and reset state."""
        if self._working is not None:
            self._remove_quietly(self._working)
            self._remove_quietly(sidecar_path(self._working))
            with contextlib.suppress(OSError):
                self._working.parent.rmdir()
        self._original = None
        self._working = None
        self._dirty = False

    # --- internals ----------------------------------------------------------

    def _propagate_sidecar(self) -> None:
        assert self._original is not None and self._working is not None
        working_sidecar = sidecar_path(self._working)
        original_sidecar = sidecar_path(self._original)
        if working_sidecar.is_file():
            self._replace_atomic(working_sidecar, original_sidecar)
        else:
            # No fields left in the working copy: never leave a stale sidecar.
            self._remove_quietly(original_sidecar)

    @staticmethod
    def _replace_atomic(src: Path, dst: Path) -> None:
        """Copy ``src`` onto ``dst`` atomically (tmp sibling + ``os.replace``)."""
        tmp = dst.with_suffix(dst.suffix + _TMP_SUFFIX)
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)

    @staticmethod
    def _remove_quietly(path: Path) -> None:
        with contextlib.suppress(FileNotFoundError):
            os.remove(path)
