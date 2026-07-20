"""The "Open with" command: launch the current document in a chosen external app.

Keeps a small user-managed list of application executables (persisted via
:class:`OpenWithStore`) and opens the current file with the picked one. The same
picker adds apps (an "[ Add application… ]" row browses for an ``.exe``) and
removes them (Del on a configured app), mirroring the Configure-shortcuts
workflow in :mod:`app.gui.keybinding_actions`.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.app_logger import log
from app.config.open_with import OpenWithStore
from app.gui import file_browser_strings, file_dialogs, file_strings
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.operations import OpResult
from app.gui.palette_controller import PaletteController
from app.os_integration import processes

# Sentinel payloads for the two add-rows (real app rows carry a Path payload).
_ADD_FROM_FILE = object()
_ADD_FROM_PROCESS = object()


class OpenWithActions:
    """Open the current document with a user-chosen external application."""

    def __init__(
        self,
        parent: QWidget,
        palette: PaletteController,
        store: OpenWithStore,
        source: Callable[[], Path | None],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._palette = palette
        self._store = store
        self._source = source
        self._report = report

    def show(self) -> None:
        """Pick a configured app (or add one) and open the current document with it."""
        if self._source() is None:
            return
        dialog = FilterListDialog(
            self._entries(),
            FilterListOptions(
                placeholder=file_strings.OPEN_WITH_PLACEHOLDER,
                title=file_strings.OPEN_WITH_TITLE,
                on_delete=self._remove,
            ),
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._dispatch(chosen)

    def _entries(self) -> list[ListEntry]:
        entries = [
            ListEntry(title=app.stem, subtitle=str(app), payload=app) for app in self._store.load()
        ]
        # Two sentinel add-rows (non-Path payloads) always last.
        entries.append(ListEntry(title=file_strings.CMD_OPEN_WITH_ADD_FILE, payload=_ADD_FROM_FILE))
        entries.append(
            ListEntry(title=file_strings.CMD_OPEN_WITH_ADD_PROCESS, payload=_ADD_FROM_PROCESS)
        )
        return entries

    def _dispatch(self, entry: ListEntry) -> None:
        if entry.payload is _ADD_FROM_FILE:
            if self._add_from_file():
                self.show()  # reopen so the newly-added app can be picked
            return
        if entry.payload is _ADD_FROM_PROCESS:
            if self._add_from_process():
                self.show()
            return
        self._launch(entry.payload)

    def _add_from_file(self) -> bool:
        """Browse for an executable and store it; ``True`` if one was added."""
        chosen = file_dialogs.prompt_open_file(
            self._parent,
            file_strings.OPEN_WITH_ADD_TITLE,
            file_browser_strings.FILTER_EXECUTABLE,
        )
        if chosen is None:
            return False
        self._save(chosen)
        return True

    def _add_from_process(self) -> bool:
        """Pick a running process and store its executable path; ``True`` if added."""
        entries = [
            ListEntry(title=app.name, subtitle=str(app.path), payload=app.path)
            for app in processes.running_apps()
        ]
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=file_strings.OPEN_WITH_PROCESS_PLACEHOLDER,
                title=file_strings.OPEN_WITH_PROCESS_TITLE,
            ),
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            self._save(chosen.payload)
            return True
        return False

    def _save(self, app: Path) -> None:
        self._store.add(app)
        self._report(OpResult(True, file_strings.MSG_OPEN_WITH_ADDED_FMT.format(app=app.stem)))

    def _remove(self, entry: ListEntry) -> None:
        if not isinstance(entry.payload, Path):  # never remove the add-rows
            return
        app: Path = entry.payload
        self._store.remove(app)
        self._report(OpResult(True, file_strings.MSG_OPEN_WITH_REMOVED_FMT.format(app=app.stem)))

    def _launch(self, app: Path) -> None:
        source = self._source()
        if source is None:
            return
        try:
            subprocess.Popen([str(app), str(source)])  # noqa: S603 - list args, no shell
        except OSError as err:
            log.warning("could not open with %s: %s", app, err)
            self._report(OpResult(False, file_strings.MSG_OPEN_WITH_FAILED_FMT.format(error=err)))
            return
        self._report(OpResult(True, file_strings.MSG_OPEN_WITH_LAUNCHED_FMT.format(app=app.stem)))
