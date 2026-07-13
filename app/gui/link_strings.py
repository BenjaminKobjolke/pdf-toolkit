"""String constants for the vim-style 'open link' hint mode.

Split out of :mod:`app.gui.strings` (which is at the file-length cap) and kept
together by domain, matching the project's other ``*_strings`` modules.
"""

from __future__ import annotations

# Command palette / shortcut titles
CMD_OPEN_LINK = "Open link"
CMD_COPY_LINK = "Copy link"
CMD_LINK_FONT = "Link overlay: font size…"
CMD_LINK_TEXT_COLOR = "Link overlay: text color…"
CMD_LINK_BG_COLOR = "Link overlay: background color…"
CMD_LINK_BOX_COLOR = "Link overlay: box color…"

# Status-bar hints
MODE_OPEN_LINK = "Open Link (type letter to open · Esc cancel)"
MODE_COPY_LINK = "Copy Link (type letter to copy · Esc cancel)"
NO_LINKS = "No links on this page"

# Appearance dialog / prompt text
DIALOG_LINK_FONT_TITLE = "Link overlay font size"
PROMPT_LINK_FONT = "Letter font size (points):"
DIALOG_LINK_TEXT_COLOR_TITLE = "Link overlay text color"
DIALOG_LINK_BG_COLOR_TITLE = "Link overlay background color"
DIALOG_LINK_BOX_COLOR_TITLE = "Link overlay box color"
