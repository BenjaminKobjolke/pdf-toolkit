"""Unit tests for the live pixel-size titles of the copy-as-image commands.

Split out of ``test_commands.py`` (file-length cap); the titles are produced by
:mod:`app.gui.copy_image_titles` through the command registry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def test_copy_image_titles_fall_back_to_static_without_document(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, "copy_page_image").display_title() == (
        "Copy page as image to clipboard"
    )
    assert commands.find(registry, "copy_page_image_50").display_title() == (
        "Copy page as image to clipboard at 50%"
    )
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).display_title() == (
        "Copy current view to clipboard"
    )
    assert commands.find(registry, "copy_view_image_50").display_title() == (
        "Copy current view to clipboard at 50%"
    )


def test_page_image_titles_show_pixels_with_document(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 100)]))
    registry = commands.build_commands(window)
    assert commands.find(registry, "copy_page_image").display_title() == (
        "Copy page as image to clipboard (200×100 px)"
    )
    assert commands.find(registry, "copy_page_image_50").display_title() == (
        "Copy page as image to clipboard at 50% (100×50 px)"
    )
    assert commands.find(registry, "copy_page_image_25").display_title() == (
        "Copy page as image to clipboard at 25% (50×25 px)"
    )


def test_view_image_titles_show_visible_page_pixels(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(200, 100)]))
    registry = commands.build_commands(window)
    viewport = window.page_view.viewport()
    dpr = viewport.devicePixelRatioF()
    rect = window.page_view.visible_page_rect()
    assert not rect.isEmpty()
    # Titles report the clipped page area (what grab_page_area copies), not the viewport.
    w = round(rect.width() * dpr)
    h = round(rect.height() * dpr)
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).display_title() == (
        f"Copy current view to clipboard ({w}×{h} px)"
    )
    assert commands.find(registry, "copy_view_image_50").display_title() == (
        f"Copy current view to clipboard at 50% ({round(w * 0.5)}×{round(h * 0.5)} px)"
    )
