"""A keyboard-first color picker.

Type a hex (``#ff8800``) or a color name (``white``), or pick from the
recently-used list and a curated set of common names. A live swatch previews the
current value. Returns a normalised ``#rrggbb`` string. No mouse required.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QWidget

from app.gui import strings
from app.gui.filterable_dialog import FilterableListDialog

# Curated common colors offered in the list (any valid Qt name still works when
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

#: Sentinel returned when the user picks "transparent" (only offered with
#: ``allow_transparent``). Distinct from ``None``, which means cancelled.
TRANSPARENT = "transparent"


def _normalize(text: str) -> str | None:
    """Return ``#rrggbb`` for a valid hex/name, else ``None``."""
    value = text.strip()
    if not value:
        return None
    color = QColor(value)
    if not color.isValid():
        return None
    return color.name(QColor.NameFormat.HexRgb)


class ColorPickerDialog(FilterableListDialog):
    """Filterable color list with a typed hex/name override and live preview."""

    #: Class-level alias of the module :data:`TRANSPARENT` sentinel.
    TRANSPARENT = TRANSPARENT

    def __init__(
        self,
        *,
        recent: list[str] | None = None,
        allow_transparent: bool = False,
        title: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            placeholder=strings.COLOR_PLACEHOLDER,
            title=title or strings.COLOR_DIALOG_TITLE,
            parent=parent,
        )
        self._allow_transparent = allow_transparent
        self._rows: list[tuple[str, str]] = self._build_rows(recent or [], allow_transparent)
        self._visible: list[tuple[str, str]] = []
        self._chosen: str | None = None

        self._preview = QLabel()
        self._preview.setMinimumHeight(28)
        self._finish_layout(self._preview, size=(360, 420))

    # --- queries (callers and tests) ----------------------------------------

    def chosen(self) -> str | None:
        """Return the accepted ``#rrggbb`` value, or ``None`` if cancelled."""
        return self._chosen

    def visible_count(self) -> int:
        return len(self._visible)

    def visible_hex(self, row: int) -> str:
        return self._visible[row][1]

    def preview_hex(self) -> str | None:
        """The color the swatch currently shows (typed value, else row)."""
        typed = _normalize(self._filter.text())
        if typed is not None:
            return typed
        row = self._list.currentRow()
        if 0 <= row < len(self._visible):
            return self._visible[row][1]
        return None

    # --- interaction --------------------------------------------------------

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
        """Interpret the filter text as transparent (if allowed) or a color."""
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

    def _on_row_changed(self) -> None:
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


_MAX_RECENT_COLORS = 8


def pick_color(
    parent: QWidget | None,
    recent: list[str],
    *,
    title: str = "",
    allow_transparent: bool = False,
) -> str | None:
    """Run the picker and maintain ``recent`` (a most-recently-used list) in place.

    Returns the chosen ``#rrggbb``, :data:`ColorPickerDialog.TRANSPARENT`, or
    ``None`` when cancelled. Only real colors enter the recent list, capped and
    front-inserted so the last picks are one keystroke away.
    """
    dialog = ColorPickerDialog(
        recent=recent, allow_transparent=allow_transparent, title=title, parent=parent
    )
    if not dialog.exec() or (chosen := dialog.chosen()) is None:
        return None
    if chosen != TRANSPARENT:
        if chosen in recent:
            recent.remove(chosen)
        recent.insert(0, chosen)
        del recent[_MAX_RECENT_COLORS:]
    return chosen
