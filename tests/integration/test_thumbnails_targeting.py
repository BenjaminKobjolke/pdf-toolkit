"""Integration: palette commands target the selected thumbnail while the grid shows."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from app.gui import commands
from app.gui.main_window import MainWindow
from app.pdf.file_format import FileFormat
from tests.conftest import MakeImage, MakePdf, MakeSearchablePdf, silence_dialogs

# The ``window`` fixture comes from tests/conftest.py.


@pytest.fixture(autouse=True)
def _quiet_dialogs(monkeypatch: pytest.MonkeyPatch) -> None:
    # _report pops a modal success/error dialog after most commands - it would
    # block the headless run.
    silence_dialogs(monkeypatch)


def _enter_grid(window: MainWindow) -> None:
    commands.find(window._registry, commands.THUMBNAILS_VIEW).run()


def _select(window: MainWindow, path: Path) -> None:
    grid = window._thumbnails_view
    for i in range(grid.count()):
        if grid.item(i).data(Qt.ItemDataRole.UserRole) == path:
            grid.setCurrentRow(i)
            return
    raise AssertionError(f"{path.name} not in grid")


def test_current_format_follows_selected_thumbnail(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    image = make_image(name="z.png")
    window.open_pdf(doc)
    _enter_grid(window)

    _select(window, image)
    assert window.current_format() is FileFormat.PNG

    window._thumbnails.leave()
    assert window.current_format() is FileFormat.PDF


def test_copy_file_path_copies_selected_thumbnail(window: MainWindow, make_pdf: MakePdf) -> None:
    make_pdf([(100, 100)], name="a.pdf")
    doc = make_pdf([(100, 100)], name="b.pdf")
    other = make_pdf([(100, 100)], name="c.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    commands.find(window._registry, commands.COPY_FILE_PATH).run()
    assert QGuiApplication.clipboard().text() == str(other)


def test_copy_page_text_reads_selected_first_page(
    window: MainWindow, make_searchable_pdf: MakeSearchablePdf
) -> None:
    other = make_searchable_pdf(["text from a"], name="a.pdf")
    doc = make_searchable_pdf(["text from b"], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    commands.find(window._registry, commands.COPY_PAGE_TEXT).run()
    assert "text from a" in QGuiApplication.clipboard().text()


def test_action_sources_resolve_selected_file(window: MainWindow, make_pdf: MakePdf) -> None:
    other = make_pdf([(100, 100)], name="a.pdf")
    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    assert window._file_actions._source() == other
    assert window._file_info_actions._source() == other
    assert window._open_with_actions._source() == other
    assert window._print_actions._source() == other

    window._thumbnails.leave()
    assert window._file_actions._source() == doc
    # Print renders the working copy (not the original) once the grid is gone.
    assert window._print_actions._source() == window._working_doc.working()


def test_working_copy_commands_hidden_while_grid_active(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)

    hidden = [
        commands.SAVE,
        commands.SAVE_AS,
        commands.CLOSE_DOC,
        commands.RELOAD_DOC,
        commands.RELOAD_WATCH_SESSION,
        commands.NEXT_PAGE,
        commands.ZOOM_FIT,
        commands.ZOOM_ACTUAL,
        commands.DELETE_PAGE,
        commands.ROTATE_RIGHT,
        commands.MOVE_NEXT,
        commands.SEARCH_PDF,
        commands.EDIT_MODE,
        commands.EXPORT_TEXT,
        commands.COPY_VIEW_IMAGE,
    ]
    for command_id in hidden:
        command = commands.find(window._registry, command_id)
        assert command.available(window.current_format()) is False, command_id

    window._thumbnails.leave()
    for command_id in hidden:
        command = commands.find(window._registry, command_id)
        assert command.available(window.current_format()) is True, command_id


def test_retargeted_commands_stay_available_while_grid_active(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)

    for command_id in [
        commands.COPY_FILE_PATH,
        commands.COPY_FILE_NAME,
        commands.COPY_FILE_NAME_NO_EXT,
        commands.OPEN_FOLDER,
        commands.FILE_INFO,
        commands.OPEN_WITH,
        commands.COPY_PAGE_TEXT,
        commands.COPY_PAGE_IMAGE,
        commands.PRINT,
        commands.RENAME_FILE,
        commands.DELETE_SAVED_FIELDS,
    ]:
        command = commands.find(window._registry, command_id)
        assert command.available(window.current_format()) is True, command_id


def test_zoom_toggle_and_sibling_commands_survive_nonviewable_selection(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    image = make_image(name="z.png")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, image)

    for command_id in [
        commands.THUMBNAILS_VIEW,
        commands.ZOOM_IN,
        commands.ZOOM_OUT,
        commands.NEXT_FILE,
        commands.PREV_FILE,
    ]:
        command = commands.find(window._registry, command_id)
        assert command.available(window.current_format()) is True, command_id


def test_delete_saved_fields_gated_by_selection_format(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    doc = make_pdf([(100, 100)], name="b.pdf")
    image = make_image(name="z.png")
    window.open_pdf(doc)
    _enter_grid(window)

    command = commands.find(window._registry, commands.DELETE_SAVED_FIELDS)
    _select(window, image)
    assert command.available(window.current_format()) is False
    _select(window, doc)
    assert command.available(window.current_format()) is True


def test_copy_page_image_title_shows_selected_files_first_page_size(
    window: MainWindow, make_pdf: MakePdf
) -> None:
    doc = make_pdf([(100, 100)], name="a.pdf")
    other = make_pdf([(200, 300)], name="b.pdf")
    window.open_pdf(doc)
    _enter_grid(window)
    _select(window, other)

    full = commands.find(window._registry, commands.COPY_PAGE_IMAGE)
    assert "(200×300 px)" in full.display_title()
    half = commands.find(window._registry, f"{commands.COPY_PAGE_IMAGE}_50")
    assert "(100×150 px)" in half.display_title()
