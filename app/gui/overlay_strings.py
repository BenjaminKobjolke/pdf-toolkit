"""UI strings for the rectangle element and element layering (edit mode).

Kept in their own domain module (like ``release_strings`` / ``default_app_strings``)
so the central ``strings`` module stays under the file-length cap.
"""

from __future__ import annotations

# Add-rectangle + layering commands
CMD_ADD_RECT = "Add rectangle"
CMD_LAYER_FORWARD = "Layer: move forward"
CMD_LAYER_BACKWARD = "Layer: move backward"
CMD_LAYER_TO_FRONT = "Layer: bring to front"
CMD_LAYER_TO_BACK = "Layer: send to back"

# Active-rectangle commands (shown only while a rectangle is selected)
CMD_RECT_FILL_COLOR = "Rectangle: fill color…"
CMD_RECT_WIDTH = "Rectangle: width…"
CMD_RECT_HEIGHT = "Rectangle: height…"
CMD_RECT_DELETE = "Rectangle: delete"

DIALOG_RECT_WIDTH_TITLE = "Rectangle width"
PROMPT_RECT_WIDTH = "Width (px):"
DIALOG_RECT_HEIGHT_TITLE = "Rectangle height"
PROMPT_RECT_HEIGHT = "Height (px):"

# Edit-bar button
BTN_ADD_RECT = "Add rectangle"
