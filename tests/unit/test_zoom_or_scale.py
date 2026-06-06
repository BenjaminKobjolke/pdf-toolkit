"""Unit tests for the zoom-keys-double-as-resize wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.gui.commands import Command
from app.gui.field_actions import FieldActions
from app.gui.image_controller import ImageController
from app.gui.main_window import MainWindow
from app.gui.page_view import PageView


def _window(scale: float | None = None, text_selected: bool = False) -> MagicMock:
    images = MagicMock(spec=ImageController)
    images.selected_scale.return_value = scale
    page_view = MagicMock(spec=PageView)
    page_view.selected_text_item.return_value = object() if text_selected else None
    window = MagicMock(spec=MainWindow)
    window.images = images
    window.page_view = page_view
    window.field_actions = MagicMock(spec=FieldActions)
    return window


def _run(window: MagicMock, factor: float) -> None:
    from app.gui.window_input import _zoom_or_scale

    _zoom_or_scale(window, Command("zoom_in", "Zoom in", MagicMock()), factor)()


def test_text_field_font_scaled() -> None:
    window = _window(text_selected=True)
    _run(window, 1.1)
    window.field_actions.scale_font.assert_called_once_with(1.1)
    window.images.set_selected_scale.assert_not_called()


def test_image_scaled_when_no_text_selected() -> None:
    window = _window(scale=2.0)
    _run(window, 1.1)
    window.images.set_selected_scale.assert_called_once_with(2.2)
    window.field_actions.scale_font.assert_not_called()


def test_zooms_when_nothing_selected() -> None:
    window = _window()
    run = MagicMock()
    from app.gui.window_input import _zoom_or_scale

    _zoom_or_scale(window, Command("zoom_in", "Zoom in", run), 1.1)()
    run.assert_called_once()
    window.field_actions.scale_font.assert_not_called()
    window.images.set_selected_scale.assert_not_called()
