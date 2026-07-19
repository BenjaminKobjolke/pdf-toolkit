"""Placement policy for new text fields: where on the page a field lands.

Pure value logic with no Qt-widget dependency, so the ordering rule (the
last-used option floats to the top of the chooser) is unit-testable on its own.
The window maps each mode to a scene point and hands it to the edit controller.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import cast

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget

from app.config.placement_settings import PlacementStore
from app.gui import strings
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.page_view import PageView

# A creator gets the chosen scene anchor (or None for the legacy top-left
# default) and whether the new item should be centred on that anchor.
PlaceFn = Callable[[QPointF | None, bool], None]


class PlacementMode(StrEnum):
    """How a newly-added overlay item is positioned on the current page."""

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


def _mode_from_stored(value: str | None) -> PlacementMode:
    """Map a stored mode id back to a :class:`PlacementMode`, defaulting to top-left."""
    if value is None:
        return PlacementMode.TOP_LEFT
    try:
        return PlacementMode(value)
    except ValueError:
        return PlacementMode.TOP_LEFT


class PlacementController:
    """Choose placement for a newly created overlay item and invoke its creator.

    The creator callback decouples placement from what is being placed, so the
    same chooser serves both text fields and images.
    """

    def __init__(
        self,
        parent: QWidget | None,
        page_view: PageView,
        mode_bar: ModeStatusBar,
        store: PlacementStore,
    ) -> None:
        self._parent = parent
        self._page_view = page_view
        self._mode_bar = mode_bar
        self._store = store
        self._last = _mode_from_stored(store.load())
        self._pending_create: PlaceFn | None = None

    def choose_and_place(self, create: PlaceFn) -> None:
        """Ask where the new item should land and hand the anchor to ``create``."""
        mode = self._choose()
        if mode is None:
            return
        self._last = mode
        self._store.save(mode.value)
        self._place(mode, create)

    def _choose(self) -> PlacementMode | None:
        entries = [
            ListEntry(title=PLACEMENT_TITLES[mode], payload=mode)
            for mode in ordered_modes(self._last)
        ]
        dialog = FilterListDialog(
            entries,
            FilterListOptions(
                placeholder=strings.PLACEMENT_PLACEHOLDER,
                title=strings.PLACEMENT_TITLE,
            ),
            parent=self._parent,
        )
        if dialog.exec() and (chosen := dialog.chosen()) is not None:
            return cast(PlacementMode, chosen.payload)
        return None

    def _place(self, mode: PlacementMode, create: PlaceFn) -> None:
        if mode is PlacementMode.PAGE_CENTER:
            create(self._page_view.page_center(), True)
        elif mode is PlacementMode.VIEW_CENTER:
            create(self._page_view.viewport_center_scene(), True)
        elif mode is PlacementMode.CUSTOM:
            self._pending_create = create
            self._mode_bar.set_hint(strings.PLACEMENT_HINT)
            self._page_view.begin_custom_placement(self._custom_placement_done)
        else:
            create(None, False)

    def _custom_placement_done(self, point: QPointF | None) -> None:
        self._mode_bar.clear_hint()
        create, self._pending_create = self._pending_create, None
        if point is not None and create is not None:
            create(point, True)
