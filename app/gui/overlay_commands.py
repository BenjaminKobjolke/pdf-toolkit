"""Command groups for rectangles and element layering.

Split out of :mod:`app.gui.commands` (which is at the file-length cap) and folded
into the registry by ``build_commands`` via a local import, so the new ids and
their wiring live here without growing the core file. ``Command`` is imported from
``commands``; the cycle is avoided because ``commands`` imports this module only
inside the ``build_commands`` function body.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.gui import commands, overlay_strings, strings
from app.gui.commands import Command

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow

# Command ids (UPPER_SNAKE_CASE), stable keys for menu/shortcut/palette lookups.
ADD_RECT = "add_rect"
RECT_FILL_COLOR = "rect_fill_color"
RECT_WIDTH = "rect_width"
RECT_HEIGHT = "rect_height"
RECT_DELETE = "rect_delete"
LAYER_FORWARD = "layer_forward"
LAYER_BACKWARD = "layer_backward"
LAYER_TO_FRONT = "layer_to_front"
LAYER_TO_BACK = "layer_to_back"

Predicate = Callable[[], bool]


def field_commands(window: MainWindow) -> list[Command]:
    """Commands shown only while a text field is selected."""
    fields = window.field_actions
    has_field: Predicate = lambda: window.page_view.selected_text_item() is not None  # noqa: E731
    c = commands
    return [
        Command(c.FIELD_CHANGE_TEXT, strings.CMD_FIELD_CHANGE_TEXT, fields.change_text, has_field),
        Command(c.FIELD_FONT_SIZE, strings.CMD_FIELD_FONT_SIZE, fields.change_size, has_field),
        Command(c.FIELD_FONT_FAMILY, strings.CMD_FIELD_FONT_FAMILY, fields.change_font, has_field),
        Command(
            c.FIELD_TEXT_COLOR, strings.CMD_FIELD_TEXT_COLOR, fields.change_text_color, has_field
        ),
        Command(c.FIELD_BG_COLOR, strings.CMD_FIELD_BG_COLOR, fields.change_bg_color, has_field),
        Command(c.FIELD_TOGGLE_BOLD, strings.CMD_FIELD_TOGGLE_BOLD, fields.toggle_bold, has_field),
        Command(
            c.FIELD_TOGGLE_ITALIC, strings.CMD_FIELD_TOGGLE_ITALIC, fields.toggle_italic, has_field
        ),
        Command(c.FIELD_DELETE, strings.CMD_FIELD_DELETE, fields.delete, has_field),
    ]


def image_commands(window: MainWindow) -> list[Command]:
    """Commands shown only while an image is selected."""
    images = window.image_actions
    has_image: Predicate = lambda: window.page_view.selected_image_item() is not None  # noqa: E731
    return [
        Command(commands.IMAGE_SCALE, strings.CMD_IMAGE_SCALE, images.change_scale, has_image),
        Command(commands.IMAGE_DELETE, strings.CMD_IMAGE_DELETE, images.delete, has_image),
    ]


def rectangle_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    """Add-rectangle (needs a doc) plus the selected-rectangle edit commands."""
    rects = window.rect_actions
    has_rect: Predicate = lambda: window.page_view.selected_rect_item() is not None  # noqa: E731
    s = overlay_strings
    return [
        Command(ADD_RECT, s.CMD_ADD_RECT, window.add_rect, has_doc),
        Command(RECT_FILL_COLOR, s.CMD_RECT_FILL_COLOR, rects.change_fill_color, has_rect),
        Command(RECT_WIDTH, s.CMD_RECT_WIDTH, rects.change_width, has_rect),
        Command(RECT_HEIGHT, s.CMD_RECT_HEIGHT, rects.change_height, has_rect),
        Command(RECT_DELETE, s.CMD_RECT_DELETE, rects.delete, has_rect),
    ]


def layer_commands(window: MainWindow) -> list[Command]:
    """Reorder the selected element; enabled only while one element is selected."""
    layers = window.layer_actions
    has_layer: Predicate = layers.has_selection
    s = overlay_strings
    return [
        Command(LAYER_FORWARD, s.CMD_LAYER_FORWARD, layers.move_forward, has_layer),
        Command(LAYER_BACKWARD, s.CMD_LAYER_BACKWARD, layers.move_backward, has_layer),
        Command(LAYER_TO_FRONT, s.CMD_LAYER_TO_FRONT, layers.bring_to_front, has_layer),
        Command(LAYER_TO_BACK, s.CMD_LAYER_TO_BACK, layers.send_to_back, has_layer),
    ]
