"""Unit tests for effective_target — which file palette commands act on."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest

from app.gui import effective_target
from app.gui.page_view import PageView
from app.gui.thumbnails_controller import ThumbnailsController

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


class _StubWindow:
    """Just the attributes effective_target reads off the real window."""

    def __init__(
        self,
        source: Path | None,
        page_view: PageView,
        thumbnails: ThumbnailsController | None = None,
    ) -> None:
        self._source = source
        self._page_view = page_view
        if thumbnails is not None:
            self._thumbnails = thumbnails


def _window(
    source: Path | None = None,
    grid_active: bool | None = None,
    selected: Path | None = None,
    page_index: int = 3,
) -> MainWindow:
    page_view = MagicMock(spec=PageView)
    page_view.current_page_index.return_value = page_index
    thumbnails = None
    if grid_active is not None:
        thumbnails = MagicMock(spec=ThumbnailsController)
        thumbnails.is_active.return_value = grid_active
        thumbnails.selected_path.return_value = selected
    return cast("MainWindow", _StubWindow(source, page_view, thumbnails))


def test_grid_active_tolerates_missing_thumbnails_attr() -> None:
    window = _window(source=Path("a.pdf"))
    assert effective_target.grid_active(window) is False
    assert effective_target.effective_source(window) == Path("a.pdf")


def test_effective_source_is_open_doc_while_grid_inactive() -> None:
    window = _window(source=Path("a.pdf"), grid_active=False, selected=Path("b.png"))
    assert effective_target.effective_source(window) == Path("a.pdf")


def test_effective_source_is_selection_while_grid_active() -> None:
    window = _window(source=Path("a.pdf"), grid_active=True, selected=Path("b.png"))
    assert effective_target.effective_source(window) == Path("b.png")


def test_effective_source_falls_back_when_grid_empty() -> None:
    window = _window(source=Path("a.pdf"), grid_active=True, selected=None)
    assert effective_target.effective_source(window) == Path("a.pdf")


def test_effective_page_index_zero_for_selection() -> None:
    window = _window(source=Path("a.pdf"), grid_active=True, selected=Path("b.pdf"))
    assert effective_target.effective_page_index(window) == 0


def test_effective_page_index_current_page_without_grid() -> None:
    window = _window(source=Path("a.pdf"), grid_active=False)
    assert effective_target.effective_page_index(window) == 3


@pytest.mark.parametrize(
    ("source", "grid_active", "expected"),
    [
        (None, None, False),
        (Path("a.pdf"), None, True),
        (Path("a.pdf"), False, True),
        (Path("a.pdf"), True, False),
    ],
)
def test_doc_in_view_truth_table(
    source: Path | None, grid_active: bool | None, expected: bool
) -> None:
    window = _window(source=source, grid_active=grid_active)
    assert effective_target.doc_in_view(window) is expected
