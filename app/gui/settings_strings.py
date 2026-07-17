"""Settings & appearance dialog strings (palette, outline, default-zoom, per-document memory).

Split out of :mod:`app.gui.strings` to keep that module under the 300-line cap.
Consumers import this module directly, mirroring ``file_strings`` / ``select_strings``.
The command *titles* for these flows stay in :mod:`app.gui.strings` beside the other
``CMD_*`` titles (they are consumed only by the command registry).
"""

from __future__ import annotations

# Command-palette appearance dialogs
DIALOG_PALETTE_WIDTH_TITLE = "Palette width"
DIALOG_PALETTE_HEIGHT_TITLE = "Palette height"
DIALOG_PALETTE_FONT_TITLE = "Palette font size"
DIALOG_PALETTE_OPACITY_TITLE = "Palette opacity"
PROMPT_PALETTE_WIDTH = "Width (% of window):"
PROMPT_PALETTE_HEIGHT = "Height (% of window):"
PROMPT_PALETTE_FONT = "Font size (pt, 0 = default):"
PROMPT_PALETTE_OPACITY = "Opacity (%):"

# Text/Markdown appearance dialogs
DIALOG_TEXT_FONT_TITLE = "Text/Markdown font size"
PROMPT_TEXT_FONT = "Font size (pt):"

# Open-dialog filter dialogs
DIALOG_OPEN_FILTER_TITLE = "Open dialog file extensions"
PROMPT_OPEN_FILTER_EXTENSIONS = "Extensions (e.g. pdf, txt, md):"

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
