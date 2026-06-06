"""Placement policy for new text fields: where on the page a field lands.

Pure value logic with no Qt-widget dependency, so the ordering rule (the
last-used option floats to the top of the chooser) is unit-testable on its own.
The window maps each mode to a scene point and hands it to the edit controller.
"""

from __future__ import annotations

from enum import StrEnum
from typing import cast

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget

from app.gui import strings
from app.gui.edit_controller import EditController
from app.gui.filter_list_dialog import FilterListDialog, ListEntry
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.page_view import PageView


class PlacementMode(StrEnum):
    """How a newly-added text field is positioned on the current page."""

    TOP_LEFT = "top_left"
    PAGE_CENTER = "page_center"
    VIEW_CENTER = "view_center"
    CUSTOM = "custom"


PLACEMENT_TITLES: dict[PlacementMode, str] = {
    PlacementMode.TOP_LEFT: strings.PLACEMENT_TOP_LEFT,
    PlacementMode.PAGE_CENTER: strings.PLACEMENT_PAGE_CENTER,
    PlacementMode.VIEW_CENTER: strings.PLACEMENT_VIEW_CENTER,
    PlacementMode.CUSTOM: strings.PLACEMENT_CUSTOM,
}


def ordered_modes(last: PlacementMode) -> list[PlacementMode]:
    """Return all modes with ``last`` first (the "last choice on top" rule)."""
    rest = [mode for mode in PlacementMode if mode is not last]
    return [last, *rest]


class PlacementController:
    """Choose and apply placement for newly created text fields."""

    def __init__(
        self,
        parent: QWidget,
        page_view: PageView,
        edit_controller: EditController,
        mode_bar: ModeStatusBar,
    ) -> None:
        self._parent = parent
        self._page_view = page_view
        self._edit_controller = edit_controller
        self._mode_bar = mode_bar
        self._last = PlacementMode.TOP_LEFT

    def choose_and_place(self) -> None:
        """Ask where the new field should land and apply the selected mode."""
        mode = self._choose()
        if mode is None:
            return
        self._last = mode
        self._place(mode)

    def _choose(self) -> PlacementMode | None:
        entries = [
            ListEntry(title=PLACEMENT_TITLES[mode], payload=mode)
            for mode in ordered_modes(self._last)
        ]
        dialog = FilterListDialog(
            entries,
            placeholder=strings.PLACEMENT_PLACEHOLDER,
            title=strings.PLACEMENT_TITLE,
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            return cast(PlacementMode, chosen.payload)
        return None

    def _place(self, mode: PlacementMode) -> None:
        if mode is PlacementMode.PAGE_CENTER:
            self._edit_controller.add_field(self._page_view.page_center(), centered=True)
        elif mode is PlacementMode.VIEW_CENTER:
            self._edit_controller.add_field(self._page_view.viewport_center_scene(), centered=True)
        elif mode is PlacementMode.CUSTOM:
            self._mode_bar.set_hint(strings.PLACEMENT_HINT)
            self._page_view.begin_custom_placement(self._custom_placement_done)
        else:
            self._edit_controller.add_field()

    def _custom_placement_done(self, point: QPointF | None) -> None:
        self._mode_bar.clear_hint()
        if point is not None:
            self._edit_controller.add_field(point, centered=True)
