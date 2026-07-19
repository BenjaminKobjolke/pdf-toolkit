"""A reusable type-to-filter list dialog.

Both the command palette and the recent-documents picker are the same widget: a
filter box over a list, driven by Up/Down/Enter/Esc. They differ only in the
rows they show and what each row carries (a command, or a path), so each row is
a typed :class:`ListEntry` with an opaque ``payload`` the caller interprets.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QListWidgetItem,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

from app.gui.filterable_dialog import FilterableListDialog

_CHORD_ROLE = Qt.ItemDataRole.UserRole
_CHORD_MARGIN = 8


def _matches(haystack: str, tokens: list[str]) -> bool:
    """True if every whitespace-separated token is a substring of ``haystack``.

    Relaxed matching so a query like ``field del`` finds ``Field: delete``
    without needing the punctuation or exact word order.
    """
    return all(token in haystack for token in tokens)


@dataclass(frozen=True)
class ListEntry:
    """One selectable row. ``payload`` is returned verbatim to the caller."""

    title: str
    subtitle: str = ""
    enabled: bool = True
    payload: Any = None
    bold: bool = False
    shortcut: str = ""


@dataclass(frozen=True)
class FilterListOptions:
    """Behaviour switches for a :class:`FilterListDialog` beyond its entry list."""

    placeholder: str = ""
    title: str = ""
    provider: Callable[[str], list[ListEntry]] | None = None
    min_chars: int = 0
    show_shortcuts: bool = False
    on_delete: Callable[[ListEntry], None] | None = None


class ShortcutItemDelegate(QStyledItemDelegate):
    """Paints the row title (default) then its chord right-aligned and dimmed."""

    def paint(
        self,
        painter: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        super().paint(painter, option, index)
        chord = index.data(_CHORD_ROLE)
        if not chord:
            return
        painter.save()
        painter.setPen(option.palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text))
        rect = option.rect.adjusted(0, 0, -_CHORD_MARGIN, 0)
        painter.drawText(rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, chord)
        painter.restore()


class FilterListDialog(FilterableListDialog):
    """Filterable single-select list. Disabled entries are never shown.

    Two modes: a **static** list filtered by substring (palette, history), or a
    **live** mode where a ``provider`` callback recomputes the rows on every
    keystroke once at least ``min_chars`` are typed (PDF / field search).
    """

    def __init__(
        self,
        entries: list[ListEntry],
        options: FilterListOptions | None = None,
        parent: QWidget | None = None,
    ) -> None:
        opts = options or FilterListOptions()
        super().__init__(placeholder=opts.placeholder, title=opts.title, parent=parent)
        self._entries = [entry for entry in entries if entry.enabled]
        self._provider = opts.provider
        self._min_chars = opts.min_chars
        self._on_delete = opts.on_delete
        if opts.show_shortcuts:
            self._list.setItemDelegate(ShortcutItemDelegate(self._list))
        self._visible: list[ListEntry] = []
        self._chosen: ListEntry | None = None
        self._finish_layout()

    # --- queries (used by callers and tests) --------------------------------

    def chosen(self) -> ListEntry | None:
        """Return the accepted entry, or ``None`` if cancelled/empty."""
        return self._chosen

    def visible_count(self) -> int:
        return len(self._visible)

    def visible_entry(self, row: int) -> ListEntry:
        return self._visible[row]

    def current_entry(self) -> ListEntry | None:
        row = self._list.currentRow()
        if 0 <= row < len(self._visible):
            return self._visible[row]
        return None

    def set_filter(self, text: str) -> None:
        self.set_query(text)

    def accept_current(self) -> None:
        """Accept the highlighted entry (if any) and close."""
        self._chosen = self.current_entry()
        if self._chosen is not None:
            self.accept()

    def _on_delete_key(self) -> bool:
        """Route Del to the ``on_delete`` callback for the highlighted entry."""
        if self._on_delete is None:
            return False
        entry = self.current_entry()
        if entry is None:
            return False
        self._on_delete(entry)
        return True

    # --- internals ----------------------------------------------------------

    def _apply_filter(self, text: str) -> None:
        self._visible = self._compute_visible(text)
        self._list.clear()
        for entry in self._visible:
            label = f"{entry.title}   —   {entry.subtitle}" if entry.subtitle else entry.title
            item = QListWidgetItem(label)
            if entry.bold:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            if entry.shortcut:
                item.setData(_CHORD_ROLE, entry.shortcut)
            self._list.addItem(item)
        if self._visible:
            self._list.setCurrentRow(0)

    def _compute_visible(self, text: str) -> list[ListEntry]:
        if self._provider is not None:
            if len(text.strip()) < self._min_chars:
                return []
            return self._provider(text)
        tokens = text.casefold().split()
        return [e for e in self._entries if _matches(e.title.casefold(), tokens)]
