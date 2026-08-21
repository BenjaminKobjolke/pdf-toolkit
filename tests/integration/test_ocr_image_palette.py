"""Integration: OCR-image command gating, picker flow, clipboard and save paths."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtGui import QGuiApplication

from app.gui import commands
from app.ocr.provider import WindowsOcrProvider
from app.pdf.file_format import FileFormat

if TYPE_CHECKING:
    from pathlib import Path

    from app.gui.filter_list_dialog import ListEntry
    from app.gui.main_window import MainWindow
    from tests.conftest import MakeImage


@pytest.fixture
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(WindowsOcrProvider, "is_available", lambda self: True)
    monkeypatch.setattr(
        WindowsOcrProvider, "recognize", lambda self, path, language=None: "hello ocr"
    )


def _choose(monkeypatch: pytest.MonkeyPatch, index: int) -> list[ListEntry]:
    """Patch the picker dialog to select entry ``index``; returns shown entries."""
    captured: list[ListEntry] = []

    class _FakeDialog:
        def __init__(self, entries: list[ListEntry], *_args: object, **_kw: object) -> None:
            captured.extend(entries)

        def exec(self) -> int:
            return 1

        def chosen(self) -> ListEntry:
            return captured[index]

    monkeypatch.setattr("app.gui.filter_list_dialog.FilterListDialog", _FakeDialog)
    return captured


def _errors(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture error-dialog texts (failed OpResults surface via show_message)."""
    from app.gui import confirm_dialog

    texts: list[str] = []
    monkeypatch.setattr(
        confirm_dialog, "show_message", lambda _parent, _title, text, *a, **k: texts.append(text)
    )
    return texts


def test_command_gating(window: MainWindow, make_image: MakeImage) -> None:
    command = commands.find(window._registry, commands.OCR_IMAGE)
    assert command.available(None) is False
    assert command.available(FileFormat.PDF) is False
    window.open_pdf(make_image("png"))
    assert command.available(window.current_format()) is True


def test_copy_to_clipboard(
    window: MainWindow,
    make_image: MakeImage,
    monkeypatch: pytest.MonkeyPatch,
    fake_ocr: None,
) -> None:
    window.open_pdf(make_image("png"))
    _choose(monkeypatch, 0)
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert QGuiApplication.clipboard().text() == "hello ocr"


def test_save_to_new_file(
    window: MainWindow,
    make_image: MakeImage,
    monkeypatch: pytest.MonkeyPatch,
    fake_ocr: None,
) -> None:
    image = make_image("png", name="scan.png")
    window.open_pdf(image)
    _choose(monkeypatch, 1)
    commands.find(window._registry, commands.OCR_IMAGE).run()
    target = image.with_suffix(".txt")
    assert target.read_text(encoding="utf-8") == "hello ocr"


def test_save_overwrite_confirmed_and_declined(
    window: MainWindow,
    make_image: MakeImage,
    monkeypatch: pytest.MonkeyPatch,
    fake_ocr: None,
) -> None:
    from app.gui import confirm_dialog

    image = make_image("png", name="scan.png")
    target = image.with_suffix(".txt")
    target.write_text("old", encoding="utf-8")
    window.open_pdf(image)
    _choose(monkeypatch, 1)

    monkeypatch.setattr(
        confirm_dialog, "confirm", lambda *a, **k: confirm_dialog.DialogResult.SECONDARY
    )
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert target.read_text(encoding="utf-8") == "old"

    monkeypatch.setattr(
        confirm_dialog, "confirm", lambda *a, **k: confirm_dialog.DialogResult.PRIMARY
    )
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert target.read_text(encoding="utf-8") == "hello ocr"


def test_empty_result_shows_message_without_picker(
    window: MainWindow, make_image: MakeImage, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import ocr_strings

    monkeypatch.setattr(WindowsOcrProvider, "is_available", lambda self: True)
    monkeypatch.setattr(WindowsOcrProvider, "recognize", lambda self, path, language=None: "   ")
    errors = _errors(monkeypatch)
    shown = _choose(monkeypatch, 0)
    window.open_pdf(make_image("png"))
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert errors == [ocr_strings.MSG_OCR_NO_TEXT]
    assert shown == []


def test_unavailable_provider_reports_and_skips_engine(
    window: MainWindow, make_image: MakeImage, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.gui import ocr_strings

    monkeypatch.setattr(WindowsOcrProvider, "is_available", lambda self: False)
    called: list[Path] = []

    def _recognize(_self: WindowsOcrProvider, path: Path, language: str | None = None) -> str:
        called.append(path)
        return ""

    monkeypatch.setattr(WindowsOcrProvider, "recognize", _recognize)
    errors = _errors(monkeypatch)
    window.open_pdf(make_image("png"))
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert errors == [ocr_strings.MSG_OCR_UNAVAILABLE]
    assert called == []


def test_language_command_gating(window: MainWindow, make_image: MakeImage) -> None:
    command = commands.find(window._registry, commands.OCR_LANGUAGE)
    assert command.available(None) is False
    assert command.available(FileFormat.PDF) is False
    window.open_pdf(make_image("png"))
    assert command.available(window.current_format()) is True


def test_language_picker_persists_choice(
    window: MainWindow,
    make_image: MakeImage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config.ocr_settings import OcrSettingsStore
    from app.ocr.provider import OcrLanguage
    from tests.conftest import gui_backend

    monkeypatch.setattr(
        WindowsOcrProvider,
        "available_languages",
        lambda self: [OcrLanguage(tag="de-DE", display_name="German (Germany)")],
    )
    window.open_pdf(make_image("png"))

    shown = _choose(monkeypatch, 1)  # entry 0 = automatic, entry 1 = de-DE
    commands.find(window._registry, commands.OCR_LANGUAGE).run()
    assert shown[0].payload == ""  # auto row listed first
    assert OcrSettingsStore(gui_backend(tmp_path)).load().language == "de-DE"

    _choose(monkeypatch, 0)  # now choose the auto row instead
    commands.find(window._registry, commands.OCR_LANGUAGE).run()
    assert OcrSettingsStore(gui_backend(tmp_path)).load().language == ""


def test_stored_language_reaches_engine(
    window: MainWindow,
    make_image: MakeImage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config.ocr_settings import OcrSettings, OcrSettingsStore
    from tests.conftest import gui_backend

    languages: list[str | None] = []

    def _recognize(_self: WindowsOcrProvider, path: Path, language: str | None = None) -> str:
        languages.append(language)
        return "text"

    monkeypatch.setattr(WindowsOcrProvider, "is_available", lambda self: True)
    monkeypatch.setattr(WindowsOcrProvider, "recognize", _recognize)
    _choose(monkeypatch, 0)
    window.open_pdf(make_image("png"))

    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert languages == [None]  # default setting → automatic

    OcrSettingsStore(gui_backend(tmp_path)).save(OcrSettings(language="de-DE"))
    commands.find(window._registry, commands.OCR_IMAGE).run()
    assert languages == [None, "de-DE"]


def test_ocr_store_in_remembered_list(window: MainWindow) -> None:
    from app.config.ocr_settings import OcrSettingsStore

    labels = [store.label for store in window._remembered._stores]
    assert OcrSettingsStore.LABEL in labels


def test_grid_selection_is_ocr_target(
    window: MainWindow,
    make_image: MakeImage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[Path] = []

    def _recognize(_self: WindowsOcrProvider, path: Path, language: str | None = None) -> str:
        seen.append(path)
        return "grid text"

    monkeypatch.setattr(WindowsOcrProvider, "is_available", lambda self: True)
    monkeypatch.setattr(WindowsOcrProvider, "recognize", _recognize)
    image = make_image("png", name="scan.png")
    window.open_pdf(image)
    window.thumbnails_controller.toggle()
    command = commands.find(window._registry, commands.OCR_IMAGE)
    assert command.available(window.current_format()) is True
    _choose(monkeypatch, 0)
    command.run()
    assert seen == [image]
