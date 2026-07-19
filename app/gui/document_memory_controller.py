"""Drives one per-document remembered dimension (zoom or page).

A single generic controller, instantiated once per dimension, so the menu,
the boundary capture, and the on-open apply are written once. The differences
between dimensions are injected: how to read the current value from the page
view, how to apply a remembered value, an optional fallback when none is
remembered, and the user-facing strings.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from PySide6.QtWidgets import QWidget

from app.config.per_document_store import PerDocumentStore
from app.gui import settings_strings
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.operations import OpResult

T = TypeVar("T")

# Menu action payloads.
_REMEMBER = "remember"
_AUTO = "auto"
_FORGET = "forget"
_FORGET_ALL = "forget_all"


@dataclass(frozen=True)
class MemoryStrings:
    """User-facing strings for one per-document dimension."""

    menu_title: str
    placeholder: str
    remember: str
    auto_on: str
    auto_off: str
    forget: str
    forget_all: str
    msg_remembered: str
    msg_forgot: str
    msg_forgot_all: str
    msg_auto_on: str
    msg_auto_off: str
    msg_no_doc: str

    @classmethod
    def for_noun(cls, noun: str) -> MemoryStrings:
        """Build the strings for a dimension named ``noun`` (e.g. "zoom")."""
        return cls(
            menu_title=settings_strings.DOC_MEM_MENU_TITLE_FMT.format(noun=noun),
            placeholder=settings_strings.DOC_MEM_PLACEHOLDER,
            remember=settings_strings.DOC_MEM_REMEMBER_FMT.format(noun=noun),
            auto_on=settings_strings.DOC_MEM_AUTO_ON_FMT.format(noun=noun),
            auto_off=settings_strings.DOC_MEM_AUTO_OFF_FMT.format(noun=noun),
            forget=settings_strings.DOC_MEM_FORGET_FMT.format(noun=noun),
            forget_all=settings_strings.DOC_MEM_FORGET_ALL_FMT.format(noun=noun),
            msg_remembered=settings_strings.DOC_MEM_MSG_REMEMBERED_FMT.format(noun=noun),
            msg_forgot=settings_strings.DOC_MEM_MSG_FORGOT_FMT.format(noun=noun),
            msg_forgot_all=settings_strings.DOC_MEM_MSG_FORGOT_ALL_FMT.format(noun=noun),
            msg_auto_on=settings_strings.DOC_MEM_MSG_AUTO_ON_FMT.format(noun=noun),
            msg_auto_off=settings_strings.DOC_MEM_MSG_AUTO_OFF_FMT.format(noun=noun),
            msg_no_doc=settings_strings.DOC_MEM_MSG_NO_DOC,
        )


@dataclass(frozen=True)
class MemoryHooks(Generic[T]):
    """How one dimension reads, applies, reports, and falls back its value."""

    current_path: Callable[[], Path | None]
    capture_value: Callable[[], T | None]
    apply_value: Callable[[T], None]
    report: Callable[[OpResult], None]
    fallback: Callable[[], None] | None = None


class DocumentMemoryController(Generic[T]):
    """Menu + boundary capture + on-open apply for one remembered dimension."""

    def __init__(
        self,
        parent: QWidget | None,
        store: PerDocumentStore[T],
        hooks: MemoryHooks[T],
        labels: MemoryStrings,
    ) -> None:
        self._parent = parent
        self._store = store
        self._current_path = hooks.current_path
        self._capture_value = hooks.capture_value
        self._apply_value = hooks.apply_value
        self._report = hooks.report
        self._labels = labels
        self._fallback = hooks.fallback

    # --- palette command ----------------------------------------------------

    def open_menu(self) -> None:
        """Show the remember/auto/forget menu and run the chosen action."""
        s = self._labels
        auto_title = s.auto_on if self._store.auto_all() else s.auto_off
        entries = [
            ListEntry(title=s.remember, payload=_REMEMBER),
            ListEntry(title=auto_title, payload=_AUTO),
            ListEntry(title=s.forget, payload=_FORGET),
            ListEntry(title=s.forget_all, payload=_FORGET_ALL),
        ]
        dialog = FilterListDialog(
            entries,
            FilterListOptions(placeholder=s.placeholder, title=s.menu_title),
            parent=self._parent,
        )
        if not dialog.exec() or (chosen := dialog.chosen()) is None:
            return
        self._dispatch(chosen.payload)

    # --- document lifecycle hooks -------------------------------------------

    def capture(self, path: Path | None) -> None:
        """If auto-remember is on, store the current value for ``path``."""
        if path is None or not self._store.auto_all():
            return
        value = self._capture_value()
        if value is not None:
            self._store.remember(path, value)

    def apply_for(self, path: Path) -> None:
        """Apply the remembered value for ``path``, or the fallback if none."""
        value = self._store.value_for(path)
        if value is not None:
            self._apply_value(value)
        elif self._fallback is not None:
            self._fallback()

    # --- internals ----------------------------------------------------------

    def _dispatch(self, action: str) -> None:
        if action == _REMEMBER:
            self._remember_current()
        elif action == _AUTO:
            self._toggle_auto()
        elif action == _FORGET:
            self._forget_current()
        elif action == _FORGET_ALL:
            self._store.forget_all()
            self._report(OpResult(True, self._labels.msg_forgot_all))

    def _remember_current(self) -> None:
        path = self._current_path()
        if path is None:
            self._report(OpResult(False, self._labels.msg_no_doc))
            return
        value = self._capture_value()
        if value is None:
            return
        self._store.remember(path, value)
        self._report(OpResult(True, self._labels.msg_remembered))

    def _toggle_auto(self) -> None:
        enabled = not self._store.auto_all()
        self._store.set_auto_all(enabled)
        msg = self._labels.msg_auto_on if enabled else self._labels.msg_auto_off
        self._report(OpResult(True, msg))

    def _forget_current(self) -> None:
        path = self._current_path()
        if path is None:
            self._report(OpResult(False, self._labels.msg_no_doc))
            return
        self._store.forget(path)
        self._report(OpResult(True, self._labels.msg_forgot))


class DocumentMemoryGroup:
    """The per-document memory controllers, captured and applied as a set.

    Keeps the iterate-over-dimensions logic out of the window: capturing happens
    at document boundaries, applying happens on open. The controllers themselves
    stay independent (separate stores and auto toggles).
    """

    def __init__(self, controllers: Sequence[DocumentMemoryController[Any]]) -> None:
        self._controllers = list(controllers)

    def capture(self, path: Path | None) -> None:
        """Persist the current view state for every auto-remember dimension."""
        for controller in self._controllers:
            controller.capture(path)

    def apply_for(self, path: Path) -> None:
        """Restore every remembered dimension for the just-opened ``path``."""
        for controller in self._controllers:
            controller.apply_for(path)
