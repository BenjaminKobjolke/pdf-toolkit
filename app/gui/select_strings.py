"""String constants for vim-style text select / copy mode.

Split out of :mod:`app.gui.strings` (which is at the file-length cap) and kept
together by domain, matching the project's other ``*_strings`` modules.
"""

from __future__ import annotations

# Command palette / shortcut title
CMD_SELECT_MODE = "Toggle text select mode (vim)"

# Status-bar hints shown while the mode is active
MODE_SELECT = "Select Mode (h/j/k/l move · v select · y copy · Esc/q exit)"
MODE_SELECT_VISUAL = "Select Mode -- VISUAL -- (y copy · Esc/q exit)"
