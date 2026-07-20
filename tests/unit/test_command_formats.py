"""Unit tests for command format-capability gating (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui import commands
from app.gui.commands import HAS_TEXT, PDF_ONLY, TRANSFORMABLE, VIEWABLE, Command
from app.gui.main_window import MainWindow
from app.pdf.file_format import IMAGE_FORMATS, TEXT_FORMATS, FileFormat
from tests.conftest import gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def _cmd(formats: frozenset[FileFormat] | None, *, enabled: bool = True) -> Command:
    return Command("id", "title", lambda: None, lambda: enabled, formats)


def _format_gate_stub(cmd: Command) -> Command:
    """Copy with is_enabled stubbed True so only the format gate is exercised."""
    return Command(cmd.command_id, cmd.title, cmd.run, lambda: True, cmd.formats)


def test_available_agnostic_always_on() -> None:
    cmd = _cmd(None)
    assert cmd.available(FileFormat.PDF)
    assert cmd.available(FileFormat.TXT)
    assert cmd.available(None)


def test_available_pdf_only() -> None:
    cmd = _cmd(PDF_ONLY)
    assert cmd.available(FileFormat.PDF)
    assert not cmd.available(FileFormat.TXT)
    assert not cmd.available(FileFormat.MD)
    assert not cmd.available(None)


def test_available_viewable_covers_all_rendered_formats() -> None:
    cmd = _cmd(VIEWABLE)
    assert cmd.available(FileFormat.PDF)
    assert cmd.available(FileFormat.TXT)
    assert cmd.available(FileFormat.MD)
    assert cmd.available(FileFormat.PNG)
    assert cmd.available(FileFormat.WEBP)
    assert not cmd.available(None)


def test_available_has_text_excludes_images() -> None:
    cmd = _cmd(HAS_TEXT)
    assert cmd.available(FileFormat.PDF)
    assert cmd.available(FileFormat.TXT)
    assert cmd.available(FileFormat.MD)
    assert not cmd.available(FileFormat.PNG)
    assert not cmd.available(None)


def test_available_respects_is_enabled() -> None:
    assert not _cmd(None, enabled=False).available(FileFormat.PDF)


def test_registry_format_annotations(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    assert commands.find(registry, commands.DELETE_PAGE).formats == PDF_ONLY
    assert commands.find(registry, commands.INSERT_PAGE).formats == PDF_ONLY
    assert commands.find(registry, commands.EDIT_MODE).formats == PDF_ONLY
    assert commands.find(registry, commands.OPEN_LINK).formats == HAS_TEXT
    assert commands.find(registry, commands.COPY_LINK).formats == HAS_TEXT
    assert commands.find(registry, commands.SEARCH_PDF).formats == HAS_TEXT
    assert commands.find(registry, commands.COPY_PAGE_TEXT).formats == HAS_TEXT
    assert commands.find(registry, commands.SELECT_MODE).formats == HAS_TEXT
    assert commands.find(registry, commands.NEXT_PAGE).formats == VIEWABLE
    assert commands.find(registry, commands.NEXT_FILE).formats == VIEWABLE
    assert commands.find(registry, commands.PREV_FILE).formats == VIEWABLE
    for cid in ("copy_page_image", "copy_page_image_50", "copy_page_image_25"):
        assert commands.find(registry, cid).formats == VIEWABLE
    assert commands.find(registry, commands.COPY_VIEW_IMAGE).formats == VIEWABLE
    for pct in (50, 25):
        assert commands.find(registry, f"copy_view_image_{pct}").formats == VIEWABLE
    for cid in (
        commands.ROTATE_LEFT,
        commands.ROTATE_RIGHT,
        commands.ROTATE_180,
        commands.FLIP_HORIZONTAL,
        commands.FLIP_VERTICAL,
        commands.SAVE,
        commands.SAVE_AS,
    ):
        assert commands.find(registry, cid).formats == TRANSFORMABLE
    assert commands.find(registry, commands.OPEN).formats is None
    assert commands.find(registry, commands.OPEN_DIR).formats is None
    assert commands.find(registry, commands.MERGE_FOLDER).formats is None


def test_text_appearance_commands_gated_to_text_formats(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    for command_id in (commands.TEXT_DARK_MODE, commands.TEXT_FONT_SIZE):
        cmd = commands.find(registry, command_id)
        assert cmd.formats == TEXT_FORMATS
        assert cmd.available(FileFormat.TXT)
        assert cmd.available(FileFormat.MD)
        assert not cmd.available(FileFormat.PDF)
        assert not cmd.available(None)


def test_image_background_command_gated_to_image_formats(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    cmd = commands.find(registry, commands.IMAGE_BACKGROUND)
    assert cmd.formats == IMAGE_FORMATS
    assert cmd.available(FileFormat.PNG)
    assert cmd.available(FileFormat.WEBP)
    assert not cmd.available(FileFormat.PDF)
    assert not cmd.available(FileFormat.TXT)
    assert not cmd.available(None)


def test_text_document_gates_page_ops_but_not_viewers(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    delete_on = _format_gate_stub(commands.find(registry, commands.DELETE_PAGE))
    link_on = _format_gate_stub(commands.find(registry, commands.OPEN_LINK))
    for fmt in (FileFormat.TXT, FileFormat.MD):
        assert not delete_on.available(fmt)
        assert link_on.available(fmt)


def test_image_document_gates_text_and_page_ops_but_not_viewers(window: MainWindow) -> None:
    registry = commands.build_commands(window)
    gated = (commands.DELETE_PAGE, commands.SEARCH_PDF, commands.COPY_PAGE_TEXT)
    open_ok = (
        commands.ZOOM_IN,
        commands.NEXT_PAGE,
        commands.PRINT,
        commands.NEXT_FILE,
        commands.SAVE,
        commands.ROTATE_RIGHT,
        commands.FLIP_HORIZONTAL,
    )
    for command_id in gated:
        stub = _format_gate_stub(commands.find(registry, command_id))
        assert not stub.available(FileFormat.PNG)
    for command_id in open_ok:
        stub = _format_gate_stub(commands.find(registry, command_id))
        assert stub.available(FileFormat.PNG)
