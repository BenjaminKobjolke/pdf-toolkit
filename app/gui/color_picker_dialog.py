"""A keyboard-first colour picker.

Type a hex (``#ff8800``) or a colour name (``white``), or pick from the
recently-used list and a curated set of common names. A live swatch previews the
current value. Returns a normalised ``#rrggbb`` string. No mouse required.
"""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from app.gui import strings

# Curated common colours offered in the list (any valid Qt name still works when
# typed). Ordered roughly by usefulness.
COMMON_COLORS: tuple[str, ...] = (
    "black",
    "white",
    "red",
    "green",
    "blue",
    "yellow",
    "orange",
    "purple",
    "magenta",
    "cyan",
    "gray",
    "lightgray",
    "darkgray",
    "brown",
    "pink",
)

_SWATCH_STYLE = "background-color: {hex}; border: 1px solid #888;"
_TRANSPARENT_SWATCH_STYLE = "border: 1px dashed #888;"
_TRANSPARENT_WORDS = {"transparent", "none"}


def _normalize(text: str) -> str | None:
    """Return ``#rrggbb`` for a valid hex/name, else ``None``."""
    value = text.strip()
    if not value:
        return None
    color = QColor(value)
    if not color.isValid():
        return None
    return color.name(QColor.NameFormat.HexRgb)


class ColorPickerDialog(QDialog):
    """Filterable colour list with a typed hex/name override and live preview."""

    #: Sentinel returned by :meth:`chosen` when the user picks "transparent"
    #: (only offered when ``allow_transparent`` is set). Distinct from ``None``,
    #: which means the dialog was cancelled.
    TRANSPARENT = "transparent"

    def __init__(
        self,
        *,
        recent: list[str] | None = None,
        allow_transparent: bool = False,
        title: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or strings.COLOR_DIALOG_TITLE)
        self._allow_transparent = allow_transparent
        self._rows: list[tuple[str, str]] = self._build_rows(recent or [], allow_transparent)
        self._visible: list[tuple[str, str]] = []
        self._chosen: str | None = None

        self._filter = QLineEdit()
        self._filter.setPlaceholderText(strings.COLOR_PLACEHOLDER)
        self._filter.textChanged.connect(self._on_text_changed)
        self._filter.returnPressed.connect(self.accept_current)
        self._filter.installEventFilter(self)

        self._preview = QLabel()
        self._preview.setMinimumHeight(28)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(lambda _row: self._update_preview())
        self._list.itemActivated.connect(lambda _item: self.accept_current())

        layout = QVBoxLayout(self)
        layout.addWidget(self._filter)
        layout.addWidget(self._preview)
        layout.addWidget(self._list)
        self.resize(360, 420)

        self._apply_filter("")
        self._filter.setFocus()

    # --- queries (callers and tests) ----------------------------------------

    def chosen(self) -> str | None:
        """Return the accepted ``#rrggbb`` value, or ``None`` if cancelled."""
        return self._chosen

    def visible_count(self) -> int:
        return len(self._visible)

    def visible_hex(self, row: int) -> str:
        return self._visible[row][1]

    def preview_hex(self) -> str | None:
        """The colour the swatch currently shows (typed value, else row)."""
        typed = _normalize(self._filter.text())
        if typed is not None:
            return typed
        row = self._list.currentRow()
        if 0 <= row < len(self._visible):
            return self._visible[row][1]
        return None

    # --- interaction --------------------------------------------------------

    def set_query(self, text: str) -> None:
        self._filter.setText(text)

    def move_selection(self, delta: int) -> None:
        count = len(self._visible)
        if count == 0:
            return
        row = (self._list.currentRow() + delta) % count
        self._list.setCurrentRow(row)

    def accept_current(self) -> None:
        """Accept the highlighted row, else a valid typed value."""
        row = self._list.currentRow()
        if 0 <= row < len(self._visible):
            self._chosen = self._visible[row][1]
        else:
            self._chosen = self._typed_value()
        if self._chosen is not None:
            self.accept()

    # --- internals ----------------------------------------------------------

    def _typed_value(self) -> str | None:
        """Interpret the filter text as transparent (if allowed) or a colour."""
        text = self._filter.text()
        if self._allow_transparent and text.strip().casefold() in _TRANSPARENT_WORDS:
            return self.TRANSPARENT
        return _normalize(text)

    def _build_rows(self, recent: list[str], allow_transparent: bool) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        if allow_transparent:
            rows.append((self.TRANSPARENT, self.TRANSPARENT))
        seen: set[str] = set()
        for value in recent:
            hex_value = _normalize(value)
            if hex_value is not None and hex_value not in seen:
                rows.append((hex_value, hex_value))
                seen.add(hex_value)
        for name in COMMON_COLORS:
            hex_value = _normalize(name)
            if hex_value is not None and hex_value not in seen:
                rows.append((name, hex_value))
                seen.add(hex_value)
        return rows

    def _on_text_changed(self, text: str) -> None:
        self._apply_filter(text)
        self._update_preview()

    def _apply_filter(self, text: str) -> None:
        needle = text.casefold()
        self._visible = [
            row for row in self._rows if needle in row[0].casefold() or needle in row[1].casefold()
        ]
        self._list.clear()
        for label, hex_value in self._visible:
            suffix = f"   {hex_value}" if label != hex_value else ""
            self._list.addItem(f"{label}{suffix}")
        if self._visible:
            self._list.setCurrentRow(0)
        self._update_preview()

    def _preview_value(self) -> str | None:
        """The value the swatch should show: a hex, ``TRANSPARENT``, or ``None``."""
        typed = self._typed_value()
        if typed is not None:
            return typed
        row = self._list.currentRow()
        if 0 <= row < len(self._visible):
            return self._visible[row][1]
        return None

    def _update_preview(self) -> None:
        value = self._preview_value()
        if value == self.TRANSPARENT:
            self._preview.setStyleSheet(_TRANSPARENT_SWATCH_STYLE)
            self._preview.setText(self.TRANSPARENT)
        elif value is None:
            self._preview.setStyleSheet("")
            self._preview.setText("")
        else:
            self._preview.setStyleSheet(_SWATCH_STYLE.format(hex=value))
            self._preview.setText("")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._filter and event.type() == QEvent.Type.KeyPress:
            key = cast(QKeyEvent, event).key()
            if key == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            if key == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
        return super().eventFilter(watched, event)
