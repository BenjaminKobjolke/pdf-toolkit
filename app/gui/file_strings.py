"""UI strings for the file-utility commands (save-as, clipboard, open folder).

Kept out of ``strings.py``, which is already at the file-length cap, matching the
existing domain string modules (``overlay_strings``, ``default_app_strings``).
"""

from __future__ import annotations

CMD_SAVE_AS = "Save file as…"
CMD_COPY_FILE_PATH = "Copy file path to clipboard"
CMD_COPY_FILE_NAME = "Copy file name to clipboard"
CMD_COPY_FILE_NAME_NO_EXT = "Copy file name without extension to clipboard"
CMD_COPY_PAGE_TEXT = "Copy all text from current page"
CMD_COPY_PAGE_IMAGE = "Copy page as image to clipboard"
CMD_COPY_VIEW_IMAGE = "Copy current view to clipboard"
# Shared title suffixes for the copy-as-image command families (page + view).
FMT_AT_PCT = "{base} at {pct}%"
FMT_PX = "{base} ({w}×{h} px)"
FMT_AT_PCT_PX = "{base} at {pct}% ({w}×{h} px)"
CMD_OPEN_FOLDER = "Open containing folder in native file explorer"
CMD_FILE_INFO = "File information"
CMD_OPEN_WITH = "Open with…"
CMD_OPEN_WITH_ADD_FILE = "[ Add from file… ]"
CMD_OPEN_WITH_ADD_PROCESS = "[ Add from running process… ]"

OPEN_WITH_TITLE = "Open with — Enter opens, Del removes, Esc closes"
OPEN_WITH_PLACEHOLDER = "Filter applications…"
OPEN_WITH_ADD_TITLE = "Choose an application"
OPEN_WITH_PROCESS_TITLE = "Add from running process — Enter adds, Esc closes"
OPEN_WITH_PROCESS_PLACEHOLDER = "Filter running processes…"
MSG_OPEN_WITH_LAUNCHED_FMT = "opened with {app}"
MSG_OPEN_WITH_ADDED_FMT = "added application: {app}"
MSG_OPEN_WITH_REMOVED_FMT = "removed application: {app}"
MSG_OPEN_WITH_FAILED_FMT = "could not open with application: {error}"

DIALOG_SAVE_AS_TITLE = "Save file as"

FILE_INFO_TITLE = "File information — Enter copies, Esc closes"
FILE_INFO_PLACEHOLDER = "Filter values…"
FILE_INFO_COPIED_MARK = "   ✓ copied"
MSG_COPIED_INFO = "copied value to clipboard"

# Row labels for the File information dialog.
LABEL_NAME = "Name"
LABEL_PATH = "Path"
LABEL_FORMAT = "Format"
LABEL_SIZE = "Size"
LABEL_PAGES = "Pages"
LABEL_CURRENT_PAGE = "Current page"
LABEL_WIDTH = "Width"
LABEL_HEIGHT = "Height"
LABEL_TITLE = "Title"
LABEL_AUTHOR = "Author"
LABEL_SUBJECT = "Subject"
LABEL_KEYWORDS = "Keywords"
LABEL_CREATOR = "Creator"
LABEL_PRODUCER = "Producer"

MSG_SAVED_AS_FMT = "saved a copy to: {name}"
MSG_COPIED_PATH = "copied file path to clipboard"
MSG_COPIED_NAME = "copied file name to clipboard"
MSG_COPIED_NAME_NO_EXT = "copied file name (no extension) to clipboard"
MSG_COPIED_PAGE_TEXT = "copied page text to clipboard"
MSG_COPIED_PAGE_IMAGE = "copied page image to clipboard"
MSG_COPIED_VIEW_IMAGE = "copied current view to clipboard"
MSG_NO_PAGE_TEXT = "this page has no selectable text"
MSG_OPEN_FOLDER_FAILED_FMT = "could not open folder: {error}"
