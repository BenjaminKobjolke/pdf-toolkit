"""Keyboard and mouse-wheel handling for :class:`~app.gui.page_view.PageView`.

The view stays a pure renderer; this controller owns the input policy — page
flipping at scroll edges, arrow-key nudging of selected fields, and wheel
navigation. It talks to the view through its public API only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QWheelEvent

from app.gui.text_item import TextFieldItem

if TYPE_CHECKING:
    from app.gui.page_view import PageView

_NUDGE_STEP = 10.0  # scene px per arrow press
_NUDGE_STEP_FINE = 1.0  # scene px per arrow press while Shift is held
_ARROW_DELTAS: dict[Qt.Key, tuple[float, float]] = {
    Qt.Key.Key_Left: (-1.0, 0.0),
    Qt.Key.Key_Right: (1.0, 0.0),
    Qt.Key.Key_Up: (0.0, -1.0),
    Qt.Key.Key_Down: (0.0, 1.0),
}


class PageInputController:
    """Decides what each key/wheel event does for a :class:`PageView`."""

    def __init__(self, view: PageView) -> None:
        self._view = view

    # --- keyboard -----------------------------------------------------------

    def key_press(self, event: QKeyEvent) -> bool:
        """Handle a key event. Returns True when it was consumed."""
        key = Qt.Key(event.key())
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self._can_edit_selection():
            self._view.delete_requested.emit()
            return True
        if key in _ARROW_DELTAS and self._can_edit_selection() and self._nudge(event, key):
            return True
        return (
            key in (Qt.Key.Key_Down, Qt.Key.Key_Up)
            and not self._is_text_editing()
            and self._flip_at_scroll_edge(going_down=key == Qt.Key.Key_Down)
        )

    # --- mouse wheel --------------------------------------------------------

    def wheel(self, event: QWheelEvent) -> bool:
        """Handle a wheel event. Returns True when it was consumed."""
        if self._view.source() is None:
            return False
        mods = event.modifiers()
        dy = event.angleDelta().y()

        # Ctrl + wheel: jump pages directly, ignore scroll position.
        if mods & Qt.KeyboardModifier.ControlModifier:
            if dy < 0:
                self._view.show_next()
            elif dy > 0:
                self._view.show_prev()
            return True

        # Shift + wheel: horizontal scroll. Some platforms report it on x().
        if mods & Qt.KeyboardModifier.ShiftModifier:
            delta = dy or event.angleDelta().x()
            bar = self._view.horizontalScrollBar()
            bar.setValue(bar.value() - delta)
            return True

        # Plain wheel: flip at the scroll edge, else let the view scroll.
        return self._flip_at_scroll_edge(going_down=dy < 0)

    # --- helpers ------------------------------------------------------------

    def _flip_at_scroll_edge(self, going_down: bool) -> bool:
        """Flip pages when the vertical scrollbar is already at the far edge.

        Returns False when there is still room to scroll (let the view scroll) or
        when already on the first/last page.
        """
        view = self._view
        bar = view.verticalScrollBar()
        index = view.current_page_index()
        last = view.total_pages() - 1
        if going_down and bar.value() >= bar.maximum() and index < last:
            view.show_next()
            view.verticalScrollBar().setValue(view.verticalScrollBar().minimum())
            return True
        if not going_down and bar.value() <= bar.minimum() and index > 0:
            view.show_prev()
            view.verticalScrollBar().setValue(view.verticalScrollBar().maximum())
            return True
        return False

    def _nudge(self, event: QKeyEvent, key: Qt.Key) -> bool:
        """Move selected fields by an arrow step. Returns False if none selected."""
        selected = [item for item in self._view.text_items() if item.isSelected()]
        if not selected:
            return False
        fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        step = _NUDGE_STEP_FINE if fine else _NUDGE_STEP
        dx, dy = _ARROW_DELTAS[key]
        for item in selected:
            item.moveBy(dx * step, dy * step)
        return True

    def _can_edit_selection(self) -> bool:
        """True when a field is selected and none is being text-edited."""
        if self._is_text_editing():
            return False  # let the keystroke act on the text being edited
        return any(item.isSelected() for item in self._view.text_items())

    def _is_text_editing(self) -> bool:
        """True when a field currently has inline text-editing focus."""
        focus = self._view.graphics_scene().focusItem()
        return isinstance(focus, TextFieldItem) and (
            focus.textInteractionFlags() != Qt.TextInteractionFlag.NoTextInteraction
        )
