"""Integration tests for vim-style open-link hint mode (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QGraphicsRectItem

from app.config.link_hint_settings import LinkHintSettingsStore
from app.gui import commands, link_strings
from app.gui.main_window import MainWindow
from tests.conftest import MakeSearchablePdf, gui_backend, gui_settings


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(gui_settings(tmp_path))


def _linked_pdf(tmp_path: Path) -> Path:
    target = tmp_path / "linked.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 80), "visit https://alpha.example/ now", fontsize=12)
    doc.save(str(target))
    doc.close()
    return target


def _press(window: MainWindow, text: str, key: Qt.Key = Qt.Key.Key_unknown) -> None:
    event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text)
    window.page_view.keyPressEvent(event)


def test_open_link_activates_and_shows_hint(window: MainWindow, tmp_path: Path) -> None:
    window.open_pdf(_linked_pdf(tmp_path))
    commands.find(commands.build_commands(window), commands.OPEN_LINK).run()
    assert window.link_hint_controller.is_active()
    assert window.mode_bar.mode_text() == link_strings.MODE_OPEN_LINK


def test_pressing_label_opens_url(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        "app.gui.link_hint_controller.webbrowser.open", lambda uri: opened.append(uri)
    )
    window.open_pdf(_linked_pdf(tmp_path))
    window.open_link_hints()
    _press(window, "a")  # the single link's label
    assert opened == ["https://alpha.example/"]
    assert not window.link_hint_controller.is_active()


def test_escape_cancels(window: MainWindow, tmp_path: Path) -> None:
    window.open_pdf(_linked_pdf(tmp_path))
    window.open_link_hints()
    assert window.link_hint_controller.is_active()
    _press(window, "\x1b", Qt.Key.Key_Escape)
    assert not window.link_hint_controller.is_active()


def test_no_links_shows_message_and_stays_inactive(
    window: MainWindow, tmp_path: Path, make_searchable_pdf: MakeSearchablePdf
) -> None:
    window.open_pdf(make_searchable_pdf(["no urls here"]))
    window.open_link_hints()
    assert not window.link_hint_controller.is_active()
    assert window.mode_bar.mode_text() == link_strings.NO_LINKS


def test_copy_link_copies_url_to_clipboard(window: MainWindow, tmp_path: Path) -> None:
    window.open_pdf(_linked_pdf(tmp_path))
    commands.find(commands.build_commands(window), commands.COPY_LINK).run()
    assert window.mode_bar.mode_text() == link_strings.MODE_COPY_LINK
    _press(window, "a")  # the single link's label
    assert QApplication.clipboard().text() == "https://alpha.example/"
    assert not window.link_hint_controller.is_active()


def test_font_size_command_persists(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.gui.link_hint_settings_controller.number_input_dialog.prompt_int",
        lambda *a, **k: 22,
    )
    commands.find(commands.build_commands(window), commands.LINK_FONT).run()
    assert LinkHintSettingsStore(gui_backend(tmp_path)).load().font_pt == 22


def test_box_color_command_applies_to_overlay(
    window: MainWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _FakePicker:
        def __init__(self, *a: object, **k: object) -> None: ...

        def exec(self) -> bool:
            return True

        def chosen(self) -> str:
            return "#123456"

    monkeypatch.setattr("app.gui.link_hint_settings_controller.ColorPickerDialog", _FakePicker)
    commands.find(commands.build_commands(window), commands.LINK_BOX_COLOR).run()
    assert LinkHintSettingsStore(gui_backend(tmp_path)).load().box_color == "#123456"

    window.open_pdf(_linked_pdf(tmp_path))
    window.open_link_hints()
    scene = window.page_view.graphics_scene()
    pen_colors = {
        item.pen().color().name() for item in scene.items() if isinstance(item, QGraphicsRectItem)
    }
    assert "#123456" in pen_colors
