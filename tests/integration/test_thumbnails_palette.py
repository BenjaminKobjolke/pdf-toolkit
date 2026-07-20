"""Integration: thumbnails view command, zoom redirection, persistence, Remembered list."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.thumbnail_settings import ThumbnailSettings, ThumbnailSettingsStore
from app.gui import commands
from app.gui.main_window import MainWindow
from tests.conftest import MakePdf, gui_backend, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def _drain_render_queue(window: MainWindow) -> None:
    view = window._thumbnails_view
    while view._pending:
        view._render_next()


def test_command_hidden_without_document(window: MainWindow) -> None:
    command = commands.find(window._registry, commands.THUMBNAILS_VIEW)
    assert command.available(None) is False


def test_toggle_shows_grid_with_current_file_selected(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    make_pdf([(100, 100)], name="a.pdf")
    doc = make_pdf([(100, 100)], name="b.pdf")
    make_pdf([(100, 100)], name="c.pdf")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    assert window._view_stack.currentWidget() is window._thumbnails_view
    grid = window._thumbnails_view
    assert grid.count() == 3
    assert grid.currentItem().text() == "b.pdf"

    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()
    assert window._view_stack.currentWidget() is window.page_view


def test_grid_renders_real_previews(window: MainWindow, make_pdf: MakePdf) -> None:
    doc = make_pdf([(100, 100)], name="a.pdf")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()
    _drain_render_queue(window)
    assert window._thumbnails_view._pixmaps[doc].width() > 0


def test_icons_are_uniform_squares(window: MainWindow, make_pdf: MakePdf) -> None:
    # A portrait page must still yield a square (center-cropped) icon, so the
    # selection frame hugs every cell identically.
    doc = make_pdf([(100, 200)], name="tall.pdf")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()
    _drain_render_queue(window)
    sizes = window._thumbnails_view.item(0).icon().availableSizes()
    assert sizes[0].width() == sizes[0].height() == 256


def test_zoom_redirects_to_thumbnails_while_active(
    window: MainWindow, make_pdf: MakePdf, tmp_path: Path
) -> None:
    doc = make_pdf([(100, 100)])
    window.open_pdf(doc)
    page_zoom_before = window.page_view.current_zoom()
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    commands.find(window._registry, commands.ZOOM_IN).run()
    assert window._thumbnails_view.iconSize().width() == 282
    assert window.page_view.current_zoom() == page_zoom_before
    # Persisted: a fresh store on the same DB sees the new size.
    assert ThumbnailSettingsStore(gui_backend(tmp_path)).load() == ThumbnailSettings(size=282)

    commands.find(window._registry, commands.ZOOM_OUT).run()
    assert window._thumbnails_view.iconSize().width() == 256


def test_zoom_still_zooms_page_when_inactive(window: MainWindow, make_pdf: MakePdf) -> None:
    doc = make_pdf([(100, 100)])
    window.open_pdf(doc)
    before = window.page_view.current_zoom()
    commands.find(window._registry, commands.ZOOM_IN).run()
    assert window.page_view.current_zoom() != before


def test_open_requested_opens_file_and_leaves_grid(window: MainWindow, make_pdf: MakePdf) -> None:
    doc = make_pdf([(100, 100)], name="a.pdf")
    other = make_pdf([(200, 200)], name="b.pdf")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    window._thumbnails_view.open_requested.emit(other)
    assert window._view_stack.currentWidget() is window.page_view
    assert window._source == other


def test_opening_from_elsewhere_dismisses_grid(window: MainWindow, make_pdf: MakePdf) -> None:
    doc = make_pdf([(100, 100)], name="a.pdf")
    other = make_pdf([(200, 200)], name="b.pdf")
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()

    window.open_pdf(other)
    assert window._thumbnails.is_active() is False
    assert window._view_stack.currentWidget() is window.page_view


def test_remembered_size_applied_on_next_entry(
    qapp: object, tmp_path: Path, make_pdf: MakePdf
) -> None:
    settings = gui_settings(tmp_path)
    ThumbnailSettingsStore(gui_backend(tmp_path)).save(ThumbnailSettings(size=512))
    window = MainWindow(settings)
    doc = make_pdf([(100, 100)])
    window.open_pdf(doc)
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()
    assert window._thumbnails_view.iconSize().width() == 512


def test_store_in_remembered_list(window: MainWindow) -> None:
    labels = [store.label for store in window._remembered._stores]
    assert ThumbnailSettingsStore.LABEL in labels
