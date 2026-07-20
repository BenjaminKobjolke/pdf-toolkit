"""Settings & appearance dialog strings (palette, outline, default-zoom, per-document memory).

Split out of :mod:`app.gui.strings` to keep that module under the 300-line cap.
Consumers import this module directly, mirroring ``file_strings`` / ``select_strings``.
The command *titles* for these flows stay in :mod:`app.gui.strings` beside the other
``CMD_*`` titles (they are consumed only by the command registry) — except the
reload titles below, added after ``strings`` hit the cap.
"""

from __future__ import annotations

# Command-palette appearance dialogs
DIALOG_PALETTE_WIDTH_TITLE = "Palette width"
DIALOG_PALETTE_HEIGHT_TITLE = "Palette height"
DIALOG_PALETTE_FONT_TITLE = "Palette font size"
DIALOG_PALETTE_OPACITY_TITLE = "Palette opacity"
DIALOG_DIALOG_SIZE_TITLE = "Dialog size"
PROMPT_PALETTE_WIDTH = "Width (% of window):"
PROMPT_PALETTE_HEIGHT = "Height (% of window):"
PROMPT_PALETTE_FONT = "Font size (pt, 0 = default):"
PROMPT_PALETTE_OPACITY = "Opacity (%):"
PROMPT_DIALOG_SIZE = "Size (% of window):"

# Text/Markdown appearance dialogs
DIALOG_TEXT_FONT_TITLE = "Text/Markdown font size"
PROMPT_TEXT_FONT = "Font size (pt):"

# Open-dialog filter dialogs
DIALOG_OPEN_FILTER_TITLE = "Open dialog file extensions"
PROMPT_OPEN_FILTER_EXTENSIONS = "Extensions (e.g. pdf, txt, md):"

# Single-instance toggle confirmations
MSG_REUSE_WINDOW_ON = "Reuse existing window: on. New launches open in this window."
MSG_REUSE_WINDOW_OFF = "Reuse existing window: off. Each launch opens its own window."
MSG_FOCUS_ON_FORWARD_ON = "Focus window on open: on. Forwarded files bring the window to the front."
MSG_FOCUS_ON_FORWARD_OFF = "Focus window on open: off. Forwarded files open in the background."

# Reload / reload-on-changes commands
CMD_RELOAD_DOC = "Reload"
CMD_RELOAD_WATCH_SESSION = "Reload on changes (this time)"
CMD_RELOAD_WATCH_DEFAULT = "Reload on changes (make default)"
MSG_RELOAD_WATCH_ON = "Reload on changes: on for this document."
MSG_RELOAD_WATCH_OFF = "Reload on changes: off for this document."
MSG_RELOAD_DEFAULT_ON = "Reload on changes by default: on."
MSG_RELOAD_DEFAULT_OFF = "Reload on changes by default: off."

# Image transparency backdrop (command title lives here — ``strings`` is at the cap)
CMD_IMAGE_BACKGROUND = "Image: transparency background…"
DIALOG_IMAGE_BACKGROUND_TITLE = "Transparency background"
IMAGE_BACKGROUND_PLACEHOLDER = "Type to filter backgrounds…"
IMAGE_BACKGROUND_WHITE = "White"
IMAGE_BACKGROUND_BLACK = "Black"
IMAGE_BACKGROUND_GREEN = "Greenscreen green"
IMAGE_BACKGROUND_BLUE = "Greenscreen blue"
IMAGE_BACKGROUND_CHECKER = "Checkered"

# Selected-item outline appearance dialogs
DIALOG_OUTLINE_WIDTH_TITLE = "Outline width"
DIALOG_OUTLINE_STYLE_TITLE = "Outline type"
DIALOG_OUTLINE_COLOR_TITLE = "Outline color"
PROMPT_OUTLINE_WIDTH = "Stroke width (px):"
OUTLINE_STYLE_PLACEHOLDER = "Type to filter line types…"
OUTLINE_STYLE_DASHED = "Dashed"
OUTLINE_STYLE_SOLID = "Solid"

# Default-zoom dialog (applied when a PDF first loads)
DIALOG_DEFAULT_ZOOM_TITLE = "Default zoom"
ZOOM_PLACEHOLDER = "Type to filter zoom levels…"
PROMPT_DEFAULT_ZOOM_PCT = "Zoom (%):"
ZOOM_FIT_LABEL = "Fit to window"
ZOOM_CUSTOM_LABEL = "Custom percentage…"
ZOOM_PERCENT_FMT = "{n}%"

# Per-document memory (zoom / page remembered per PDF). The two dimensions share
# one templated set of strings, instantiated per ``{noun}`` (zoom / page).
DOC_MEM_NOUN_ZOOM = "zoom"
DOC_MEM_NOUN_PAGE = "page"
DOC_MEM_MENU_TITLE_FMT = "Remember {noun} for documents"
DOC_MEM_PLACEHOLDER = "Type to filter…"
DOC_MEM_REMEMBER_FMT = "Remember {noun} for this document"
DOC_MEM_AUTO_ON_FMT = "Auto-remember {noun} for all documents: ON (turn off)"
DOC_MEM_AUTO_OFF_FMT = "Auto-remember {noun} for all documents: OFF (turn on)"
DOC_MEM_FORGET_FMT = "Forget {noun} for this document"
DOC_MEM_FORGET_ALL_FMT = "Forget {noun} for all documents"
DOC_MEM_MSG_REMEMBERED_FMT = "Remembered {noun} for this document."
DOC_MEM_MSG_FORGOT_FMT = "Forgot {noun} for this document."
DOC_MEM_MSG_FORGOT_ALL_FMT = "Forgot {noun} for all documents."
DOC_MEM_MSG_AUTO_ON_FMT = "Auto-remember {noun}: on."
DOC_MEM_MSG_AUTO_OFF_FMT = "Auto-remember {noun}: off."
DOC_MEM_MSG_NO_DOC = "Open a document first."
