"""Integration tests for the GUI window wiring (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.settings import Settings
from app.config.window_geometry import WindowGeometry, WindowGeometryStore
from app.gui import confirm_dialog
from app.gui.main_window import MainWindow
from app.storage.factory import make_backend
from tests.conftest import MakeImage, MakePdf, PageSizesOf, gui_settings, silence_dialogs


def _settings(tmp_path: Path) -> Settings:
    return gui_settings(tmp_path)


@pytest.fixture
def window(qapp: object, tmp_path: Path) -> MainWindow:
    return MainWindow(_settings(tmp_path))


def test_delete_current_page_shrinks_document(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    silence_dialogs(monkeypatch)

    window.page_actions.delete_current_page()

    # Deferred: the view + working copy shrink; the original is intact until save.
    assert window._page_view.total_pages() == 2
    assert window._working_doc.is_dirty()
    assert page_sizes_of(pdf) == [(100, 200), (300, 400), (120, 120)]

    window.save_changes()
    assert page_sizes_of(pdf) == [(300, 400), (120, 120)]


def test_open_image_renders_single_page(window: MainWindow, make_image: MakeImage) -> None:
    image = make_image("png")
    window.open_pdf(image)

    assert window._page_view.total_pages() == 1


def test_footer_shows_file_position_and_page(window: MainWindow, make_pdf: MakePdf) -> None:
    make_pdf([(100, 200)], "a.pdf")
    target = make_pdf([(100, 200), (300, 400)], "b.pdf")
    make_pdf([(100, 200)], "c.pdf")

    window.open_pdf(target)

    assert window.mode_bar.file_text() == "File 2/3"
    assert window.mode_bar.page_text() == "Page 1/2"


def test_footer_compact_for_image(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    make_pdf([(100, 200)], "a.pdf")
    image = make_image("png", "b.png")

    window.open_pdf(image)

    assert window.mode_bar.file_text() == "2/2"
    assert window.mode_bar.page_text() == ""


def test_footer_labeled_again_after_image(
    window: MainWindow, make_pdf: MakePdf, make_image: MakeImage
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)], "a.pdf")
    window.open_pdf(make_image("png", "b.png"))

    window.open_pdf(pdf)

    assert window.mode_bar.file_text() == "File 1/2"
    assert window.mode_bar.page_text() == "Page 1/2"


def test_footer_clears_on_close(window: MainWindow, make_pdf: MakePdf) -> None:
    window.open_pdf(make_pdf([(100, 200)]))
    window.close_document()

    assert window.mode_bar.file_text() == ""
    assert window.mode_bar.page_text() == ""


def test_swap_pages_through_window(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400)])
    window.open_pdf(pdf)
    monkeypatch.setattr(confirm_dialog, "show_message", lambda *a, **k: None)

    window.page_actions.swap()

    # Deferred: the original changes only after an explicit save.
    assert page_sizes_of(pdf) == [(100, 200), (300, 400)]
    window.save_changes()
    assert page_sizes_of(pdf) == [(300, 400), (100, 200)]


def test_invalid_swap_reports_error_and_keeps_file(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    make_pdf: MakePdf,
    page_sizes_of: PageSizesOf,
) -> None:
    pdf = make_pdf([(100, 200), (300, 400), (120, 120)])
    window.open_pdf(pdf)
    captured: list[str] = []
    monkeypatch.setattr(
        confirm_dialog, "show_message", lambda parent, title, msg, *a, **k: captured.append(msg)
    )

    window.page_actions.swap()

    assert captured  # an error dialog was shown
    assert page_sizes_of(pdf) == [(100, 200), (300, 400), (120, 120)]


def test_psd_rotate_previews_without_dirty(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, make_image: MakeImage
) -> None:
    from PIL import Image

    psd = make_image("psd", size=(16, 8))
    window.open_pdf(psd)
    silence_dialogs(monkeypatch)
    original_bytes = psd.read_bytes()

    window.rotate_actions.rotate_right()

    working = window._working_doc.working()
    assert working is not None and working.suffix == ".png"
    with Image.open(working) as img:
        assert img.size == (8, 16)
    # Preview-only: never dirty, no Modified marker, original untouched.
    assert not window._working_doc.is_dirty()
    assert window.mode_bar.dirty_text() == ""
    assert psd.read_bytes() == original_bytes


def test_open_corrupt_psd_warns_and_aborts(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad = tmp_path / "bad.psd"
    bad.write_bytes(b"8BPS garbage")
    captured: list[str] = []
    monkeypatch.setattr(
        confirm_dialog, "show_message", lambda parent, title, msg, *a, **k: captured.append(msg)
    )

    window.open_pdf(bad)

    assert captured  # a warning dialog was shown
    assert not window.has_document()


def test_psd_save_as_suggests_and_exports_png(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, make_image: MakeImage, tmp_path: Path
) -> None:
    from PIL import Image

    from app.gui import file_dialogs

    psd = make_image("psd")
    window.open_pdf(psd)
    silence_dialogs(monkeypatch)
    dest = tmp_path / "exported.png"
    captured: list[Path] = []

    def fake_prompt(parent: object, title: str, suggestion: Path, filt: object) -> Path:
        captured.append(suggestion)
        return dest

    monkeypatch.setattr(file_dialogs, "prompt_save_file", fake_prompt)
    window.document_actions.save_as()

    assert captured and captured[0].suffix == ".png"
    with Image.open(dest) as img:
        assert img.format == "PNG"


def test_window_geometry_restored_on_construct(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    WindowGeometryStore(make_backend(settings.database_url)).save(
        WindowGeometry(x=120, y=90, width=640, height=480)
    )
    win = MainWindow(settings)
    assert win.width() == 640
    assert win.height() == 480


def test_offscreen_geometry_pulled_back_on_screen(qapp: object, tmp_path: Path) -> None:
    # Saved position points at a monitor that no longer exists (display changed):
    # the window must be relocated onto a connected screen, not left invisible.
    from PySide6.QtGui import QGuiApplication

    settings = _settings(tmp_path)
    WindowGeometryStore(make_backend(settings.database_url)).save(
        WindowGeometry(x=99999, y=99999, width=640, height=480)
    )
    win = MainWindow(settings)
    assert QGuiApplication.screenAt(win.frameGeometry().center()) is not None


def test_close_event_persists_geometry(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    win.resize(700, 500)
    win.close()
    geom = WindowGeometryStore(make_backend(settings.database_url)).load()
    assert geom is not None
    assert (geom.width, geom.height) == (700, 500)


def test_toggle_statusbar_hides_and_persists(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    assert win._mode_bar.isHidden() is False

    win.toggle_statusbar()
    assert win._mode_bar.isHidden() is True

    # Persisted: a fresh window restores the hidden status bar.
    reopened = MainWindow(settings)
    assert reopened._mode_bar.isHidden() is True


def test_toggle_fullscreen_is_session_only(qapp: object, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    win.toggle_fullscreen()
    assert win.isFullScreen() is True
    win.toggle_fullscreen()
    assert win.isFullScreen() is False


def test_leaving_fullscreen_restores_pre_fullscreen_size(qapp: object, tmp_path: Path) -> None:
    # Exercise the controller's snapshot/restore directly: the offscreen platform
    # won't actually grow the window on showFullScreen(), so simulate the OS
    # resizing it while fullscreen and confirm exit restores the entry rect — the
    # bug was exit losing the pre-fullscreen size.
    settings = _settings(tmp_path)
    win = MainWindow(settings)
    win.resize(640, 480)
    win.show()
    before = (win.width(), win.height())

    win._geometry.enter_fullscreen()
    win.resize(1920, 1080)  # stand in for the OS resizing the window to the screen
    win._geometry.exit_fullscreen()

    assert win.isFullScreen() is False
    assert (win.width(), win.height()) == before
