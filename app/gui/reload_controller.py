"""Reload the open document from disk — manually or when it changes on disk.

Owns the ``QFileSystemWatcher`` behind the three palette commands *Reload*,
*Reload on changes (this time)* and *Reload on changes (make default)*. The
session watch state re-initializes from the persisted default on every document
open, so "this time" naturally expires with the document.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer

from app.config.reload_settings import ReloadSettingsStore
from app.gui import settings_strings
from app.gui.operations import OpResult
from app.gui.page_view import PageView

# Editors fire several fileChanged events per save; collapse them into one reload.
_DEBOUNCE_MS = 300
# Atomic saves briefly remove the file; how often to re-check before giving up.
_MISSING_RETRIES = 3
# Our own Ctrl+S also touches the file; ignore watcher events this long after it.
_SELF_SAVE_IGNORE_S = 2.0


class ReloadController:
    """Manual reload plus debounced auto-reload of the current document."""

    def __init__(
        self,
        parent: QObject,
        store: ReloadSettingsStore,
        source: Callable[[], Path | None],
        open_pdf: Callable[[Path], None],
        page_view: PageView,
        report: Callable[[OpResult], None],
    ) -> None:
        self._store = store
        self._source = source
        self._open_pdf = open_pdf
        self._page_view = page_view
        self._report = report
        self._watching = False
        self._ignore_until = 0.0
        self._retries = 0
        self._watcher = QFileSystemWatcher(parent)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._timer = QTimer(parent)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_DEBOUNCE_MS)
        self._timer.timeout.connect(self._on_timeout)

    def reload(self) -> None:
        """Reopen the current document from disk, keeping page and zoom."""
        path = self._source()
        if path is None:
            return
        page = self._page_view.current_page_index()
        zoom = self._page_view.current_zoom()
        self._open_pdf(path)
        # If the unsaved-changes prompt was cancelled the document is unchanged
        # and re-applying the captured view is a no-op.
        self._page_view.set_default_zoom(zoom.fit, zoom.percent)
        self._page_view.go_to_page(page)

    def toggle_session_watch(self) -> None:
        """Flip auto-reload for the current document only."""
        self._set_watching(not self._watching)
        msg = (
            settings_strings.MSG_RELOAD_WATCH_ON
            if self._watching
            else settings_strings.MSG_RELOAD_WATCH_OFF
        )
        self._report(OpResult(True, msg))

    def toggle_watch_default(self) -> None:
        """Flip the persisted auto-reload default and adopt it immediately."""
        settings = self._store.load()
        flipped = not settings.watch_by_default
        self._store.save(replace(settings, watch_by_default=flipped))
        self._set_watching(flipped)
        msg = (
            settings_strings.MSG_RELOAD_DEFAULT_ON
            if flipped
            else settings_strings.MSG_RELOAD_DEFAULT_OFF
        )
        self._report(OpResult(True, msg))

    def on_document_opened(self, path: Path) -> None:
        """Re-initialize the watch state from the persisted default."""
        self._disarm()
        self._watching = self._store.load().watch_by_default
        if self._watching:
            self._arm(path)

    def on_document_closed(self) -> None:
        self._set_watching(False)

    def mark_self_save(self) -> None:
        """Suppress the watcher briefly so our own save does not trigger a reload."""
        self._ignore_until = time.monotonic() + _SELF_SAVE_IGNORE_S

    def _set_watching(self, watching: bool) -> None:
        self._watching = watching
        path = self._source()
        if watching and path is not None:
            self._arm(path)
        else:
            self._disarm()

    def _arm(self, path: Path) -> None:
        if str(path) not in self._watcher.files():
            self._watcher.addPath(str(path))

    def _disarm(self) -> None:
        files = self._watcher.files()
        if files:
            self._watcher.removePaths(files)
        self._timer.stop()

    def _on_file_changed(self, _path: str) -> None:
        self._retries = 0
        self._timer.start()

    def _on_timeout(self) -> None:
        if time.monotonic() < self._ignore_until:
            return
        path = self._source()
        if path is None or not self._watching:
            return
        if not path.exists():
            # ponytail: bounded retry, give up silently — a deleted file is not
            # a reload; the next fileChanged resets the counter.
            if self._retries < _MISSING_RETRIES:
                self._retries += 1
                self._timer.start()
            return
        self._arm(path)  # atomic saves drop the watched path; re-add it
        self.reload()
