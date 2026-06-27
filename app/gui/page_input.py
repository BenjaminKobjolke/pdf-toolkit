"""Keyboard and mouse-wheel handling for :class:`~app.gui.page_view.PageView`.

The view stays a pure renderer; this controller owns the input policy — page
flipping at scroll edges, arrow-key nudging of selected fields, and wheel
navigation. It talks to the view through its public API only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeyEvent, QWheelEvent

from app.gui import overlay_selection
from app.gui.crosshair_item import CrosshairItem
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
_CONFIRM_KEYS = (Qt.Key.Key_Return, Qt.Key.Key_Enter)
_SCALE_UP_KEYS = (Qt.Key.Key_Plus, Qt.Key.Key_Equal)
_SCALE_DOWN_KEYS = (Qt.Key.Key_Minus, Qt.Key.Key_Underscore)
_SCALE_STEP = 1.1  # multiply / divide the selected image's scale per keypress


@dataclass
class _PlacementSession:
    """An in-flight custom-placement: the live crosshair and its completion hook."""

    crosshair: CrosshairItem
    on_done: Callable[[QPointF | None], None]


class PageInputController:
    """Decides what each key/wheel event does for a :class:`PageView`."""

    def __init__(self, view: PageView) -> None:
        self._view = view
        self._placement: _PlacementSession | None = None

    # --- custom placement ---------------------------------------------------

    def begin_placement(self, on_done: Callable[[QPointF | None], None]) -> None:
        """Start picking a spot: show a crosshair at the view centre.

        ``on_done`` is called exactly once when the session finishes: with the
        chosen scene point (click or Enter), or with ``None`` if cancelled (Esc).
        A second call cancels any in-flight session first.
        """
        self._finish_placement(None)
        crosshair = CrosshairItem()
        crosshair.setPos(self._view.viewport_center_scene())
        self._view.graphics_scene().addItem(crosshair)
        self._placement = _PlacementSession(crosshair, on_done)

    def placement_active(self) -> bool:
        return self._placement is not None

    def mouse_press(self, scene_pt: QPointF) -> None:
        """Confirm placement at ``scene_pt`` immediately (single click creates)."""
        if self._placement is not None:
            self._finish_placement(scene_pt)

    def mouse_move(self, scene_pt: QPointF) -> None:
        """Move the crosshair under the cursor (hover feedback)."""
        if self._placement is not None:
            self._placement.crosshair.setPos(scene_pt)

    def _key_in_placement(self, event: QKeyEvent, key: Qt.Key) -> bool:
        session = self._placement
        if session is None:
            return False
        if key == Qt.Key.Key_Escape:
            self._finish_placement(None)
            return True
        if key in _CONFIRM_KEYS:
            self._finish_placement(session.crosshair.pos())
            return True
        if key in _ARROW_DELTAS:
            fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            step = _NUDGE_STEP_FINE if fine else _NUDGE_STEP
            dx, dy = _ARROW_DELTAS[key]
            session.crosshair.moveBy(dx * step, dy * step)
            return True
        return False

    def _finish_placement(self, point: QPointF | None) -> None:
        """Tear down the session (if any) and fire its completion hook once."""
        session = self._placement
        if session is None:
            return
        self._view.graphics_scene().removeItem(session.crosshair)
        self._placement = None
        session.on_done(point)

    # --- keyboard -----------------------------------------------------------

    def key_press(self, event: QKeyEvent) -> bool:
        """Handle a key event. Returns True when it was consumed."""
        key = Qt.Key(event.key())
        if self._placement is not None:
            return self._key_in_placement(event, key)
        if key == Qt.Key.Key_Escape and self._view.has_highlights():
            self._view.clear_highlights()
            return True
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self._can_edit_selection():
            self._view.delete_requested.emit()
            return True
        if key in _CONFIRM_KEYS and self._can_edit_selection():
            self._view.edit_text_requested.emit()
            return True
        if (key in _SCALE_UP_KEYS or key in _SCALE_DOWN_KEYS) and self._scale_selected_image(key):
            return True
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and not self._is_text_editing():
            return overlay_selection.select_adjacent_editable(
                self._view, forward=key == Qt.Key.Key_Tab
            )
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
        """Move selected items by an arrow step. Returns False if none selected."""
        selected = overlay_selection.selected_movable_items(self._view)
        if not selected:
            return False
        fine = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        step = _NUDGE_STEP_FINE if fine else _NUDGE_STEP
        dx, dy = _ARROW_DELTAS[key]
        for item in selected:
            item.moveBy(dx * step, dy * step)
        return True

    def _scale_selected_image(self, key: Qt.Key) -> bool:
        """Grow/shrink the selected image. Returns False if none / text-editing."""
        if self._is_text_editing():
            return False
        image = self._view.selected_image_item()
        if image is None:
            return False
        factor = _SCALE_STEP if key in _SCALE_UP_KEYS else 1.0 / _SCALE_STEP
        image.scale_about_center(image.scale_factor() * factor)
        return True

    def _can_edit_selection(self) -> bool:
        """True when an overlay item is selected and none is being text-edited."""
        if self._is_text_editing():
            return False  # let the keystroke act on the text being edited
        return bool(overlay_selection.selected_movable_items(self._view))

    def _is_text_editing(self) -> bool:
        """True when a field currently has inline text-editing focus."""
        focus = self._view.graphics_scene().focusItem()
        return isinstance(focus, TextFieldItem) and (
            focus.textInteractionFlags() != Qt.TextInteractionFlag.NoTextInteraction
        )
