"""Unit tests for the thumbnails-view controller (mocked Qt collaborators)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.config.thumbnail_settings import (
    THUMB_PX_MAX,
    THUMB_PX_MIN,
    ThumbnailSettings,
    ThumbnailSettingsStore,
)
from app.gui.file_browser_model import FileFilter
from app.gui.thumbnails_controller import ThumbnailsController


def _controller(
    source: Path | None = None,
    size: int = 256,
) -> tuple[ThumbnailsController, dict[str, MagicMock]]:
    mocks = {
        "store": MagicMock(spec=ThumbnailSettingsStore),
        "stack": MagicMock(),
        "page_view": MagicMock(),
        "view": MagicMock(),
        "open_file": MagicMock(),
    }
    mocks["store"].load.return_value = ThumbnailSettings(size=size)
    controller = ThumbnailsController(
        store=mocks["store"],
        stack=mocks["stack"],
        page_view=mocks["page_view"],
        view=mocks["view"],
        source=lambda: source,
        current_filter=lambda: FileFilter("all", ()),
        open_file=mocks["open_file"],
    )
    return controller, mocks


def test_inactive_by_default() -> None:
    controller, _ = _controller()
    assert controller.is_active() is False


def test_enter_without_document_is_noop() -> None:
    controller, mocks = _controller(source=None)
    controller.enter()
    assert controller.is_active() is False
    mocks["stack"].setCurrentWidget.assert_not_called()


def test_enter_populates_switches_and_focuses(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    controller, mocks = _controller(source=doc)
    controller.enter()
    assert controller.is_active() is True
    mocks["view"].set_thumb_size.assert_called_once_with(256)
    mocks["view"].populate.assert_called_once_with([doc], doc)
    mocks["stack"].setCurrentWidget.assert_called_once_with(mocks["view"])
    mocks["view"].setFocus.assert_called_once()
    mocks["page_view"].graphics_scene.return_value.clearSelection.assert_called_once()


def test_leave_restores_page_view(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    controller, mocks = _controller(source=doc)
    controller.enter()
    controller.leave()
    assert controller.is_active() is False
    mocks["stack"].setCurrentWidget.assert_called_with(mocks["page_view"])
    mocks["page_view"].setFocus.assert_called_once()


def test_leave_when_inactive_is_noop() -> None:
    controller, mocks = _controller()
    controller.leave()
    mocks["stack"].setCurrentWidget.assert_not_called()
    mocks["page_view"].setFocus.assert_not_called()


def test_toggle_flips(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    controller, _ = _controller(source=doc)
    controller.toggle()
    assert controller.is_active() is True
    controller.toggle()
    assert controller.is_active() is False


def test_zoom_in_steps_ten_percent_and_persists() -> None:
    controller, mocks = _controller(size=256)
    controller.zoom_in()
    mocks["view"].set_thumb_size.assert_called_with(282)
    mocks["store"].save.assert_called_once_with(ThumbnailSettings(size=282))


def test_zoom_out_steps_down() -> None:
    controller, mocks = _controller(size=256)
    controller.zoom_out()
    mocks["view"].set_thumb_size.assert_called_with(233)


@pytest.mark.parametrize(
    ("start", "direction", "expected"),
    [(THUMB_PX_MAX, 1, THUMB_PX_MAX), (THUMB_PX_MIN, -1, THUMB_PX_MIN)],
)
def test_zoom_clamps_at_bounds(start: int, direction: int, expected: int) -> None:
    controller, mocks = _controller(size=start)
    if direction > 0:
        controller.zoom_in()
    else:
        controller.zoom_out()
    mocks["view"].set_thumb_size.assert_called_with(expected)


def test_selected_path_none_while_inactive() -> None:
    controller, mocks = _controller()
    assert controller.selected_path() is None
    mocks["view"].selected_path.assert_not_called()


def test_selected_path_delegates_to_view_while_active(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    controller, mocks = _controller(source=doc)
    controller.enter()
    mocks["view"].selected_path.return_value = doc
    assert controller.selected_path() == doc


def test_refresh_while_inactive_is_noop() -> None:
    controller, mocks = _controller()
    controller.refresh()
    mocks["view"].populate.assert_not_called()


def test_refresh_repopulates_with_new_listing_and_selection(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    controller, mocks = _controller(source=doc)
    controller.enter()
    renamed = tmp_path / "b.pdf"
    doc.rename(renamed)
    controller.refresh(select=renamed)
    mocks["view"].populate.assert_called_with([renamed], renamed)


def test_open_selected_leaves_then_opens(tmp_path: Path) -> None:
    doc = tmp_path / "a.pdf"
    doc.write_text("x")
    other = tmp_path / "b.pdf"
    other.write_text("x")
    controller, mocks = _controller(source=doc)
    controller.enter()
    controller.open_selected(other)
    assert controller.is_active() is False
    mocks["open_file"].assert_called_once_with(other)
