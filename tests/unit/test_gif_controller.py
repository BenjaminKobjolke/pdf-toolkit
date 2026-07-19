"""Unit tests for animated-GIF playback (offscreen Qt).

Exercises :class:`app.gui.gif_controller.GifController` against a real
:class:`~app.gui.page_view.PageView`, plus the palette toggle's gating/title.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.gui import commands, strings
from app.gui.commands import Command
from app.gui.gif_controller import GifController
from app.gui.main_window import MainWindow
from app.gui.page_view import PageView
from app.pdf.file_format import FileFormat
from tests.conftest import gui_settings


def _animated_gif(path: Path, frames: int = 4, size: tuple[int, int] = (16, 16)) -> Path:
    # Frames must genuinely differ — a moving square — or PIL collapses solid
    # frames into one and QMovie reports frameCount 1 (i.e. "not animated").
    imgs = []
    for i in range(frames):
        frame = Image.new("RGB", size, (0, 0, 0))
        for x in range(3):
            for y in range(3):
                frame.putpixel(((i * 3 + x) % size[0], y), (255, 255, 255))
        imgs.append(frame)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=80, loop=0, disposal=2)
    return path


def _static_gif(path: Path, size: tuple[int, int] = (16, 16)) -> Path:
    Image.new("RGB", size, (20, 40, 60)).save(path)
    return path


@pytest.fixture
def page_view(qapp: object) -> PageView:
    return PageView()


def test_animated_gif_autoplays(page_view: PageView, tmp_path: Path) -> None:
    gif = _animated_gif(tmp_path / "spin.gif")
    page_view.load(gif)
    ctl = GifController(page_view)
    ctl.on_document_opened(gif, FileFormat.GIF)
    assert ctl.is_animated()
    assert ctl.is_playing()


def test_toggle_pauses_and_resumes(page_view: PageView, tmp_path: Path) -> None:
    gif = _animated_gif(tmp_path / "spin.gif")
    page_view.load(gif)
    ctl = GifController(page_view)
    ctl.on_document_opened(gif, FileFormat.GIF)

    ctl.toggle()
    assert not ctl.is_playing()
    ctl.toggle()
    assert ctl.is_playing()


def test_static_gif_is_not_animated(page_view: PageView, tmp_path: Path) -> None:
    gif = _static_gif(tmp_path / "flat.gif")
    page_view.load(gif)
    ctl = GifController(page_view)
    ctl.on_document_opened(gif, FileFormat.GIF)
    assert not ctl.is_animated()
    assert not ctl.is_playing()


def test_non_gif_is_not_animated(page_view: PageView, tmp_path: Path) -> None:
    png = tmp_path / "pic.png"
    Image.new("RGB", (16, 16), (10, 20, 30)).save(png)
    page_view.load(png)
    ctl = GifController(page_view)
    ctl.on_document_opened(png, FileFormat.PNG)
    assert not ctl.is_animated()


def test_close_drops_animation_and_unsuspends(page_view: PageView, tmp_path: Path) -> None:
    gif = _animated_gif(tmp_path / "spin.gif")
    page_view.load(gif)
    ctl = GifController(page_view)
    ctl.on_document_opened(gif, FileFormat.GIF)
    assert page_view.is_render_suspended()

    ctl.on_document_closed()
    page_view.reset()
    assert not ctl.is_animated()
    assert not page_view.is_render_suspended()


def _gif_command(window: MainWindow) -> Command:
    return commands.find(commands.build_commands(window), commands.GIF_TOGGLE)


def test_gif_toggle_gated_to_gif(qapp: object, tmp_path: Path) -> None:
    window = MainWindow(gui_settings(tmp_path))
    cmd = _gif_command(window)
    assert cmd.formats == frozenset({FileFormat.GIF})
    assert not cmd.available(FileFormat.PNG)
    assert not cmd.available(FileFormat.PDF)


def test_gif_toggle_stable_searchable_title(qapp: object, tmp_path: Path) -> None:
    # A stable label (not flipped by state) keeps the row findable by "play" OR
    # "pause" in the type-to-filter palette, whether the GIF is playing or paused.
    window = MainWindow(gui_settings(tmp_path))
    gif = _animated_gif(tmp_path / "spin.gif")
    window.open_pdf(gif)
    cmd = _gif_command(window)

    assert cmd.available(FileFormat.GIF)
    assert cmd.display_title() == strings.CMD_GIF_TOGGLE
    assert "play" in cmd.display_title() and "pause" in cmd.display_title()

    window.toggle_gif_playback()  # pause it — the label must not change
    assert cmd.available(FileFormat.GIF)
    assert cmd.display_title() == strings.CMD_GIF_TOGGLE


def test_switching_away_releases_gif_file(qapp: object, tmp_path: Path) -> None:
    # QMovie holds the working copy open; if it is not released before the next
    # open, working_doc.open() fails to delete it on Windows. Regression guard.
    window = MainWindow(gui_settings(tmp_path))
    gif = _animated_gif(tmp_path / "spin.gif")
    png = tmp_path / "still.png"
    Image.new("RGB", (12, 12), (1, 2, 3)).save(png)

    window.open_pdf(gif)
    assert window.is_animated_gif()
    window.open_pdf(png)  # must not raise PermissionError deleting the GIF working copy
    assert not window.is_animated_gif()
    assert not window.page_view.is_render_suspended()
