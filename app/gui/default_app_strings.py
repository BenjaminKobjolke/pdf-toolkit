"""UI strings for the 'File type associations' command and dialog.

Split out of :mod:`app.gui.strings` (which is at its size limit) so the
file-association feature owns its display strings in one domain-grouped place.
See ``docs/FILE_ASSOCIATIONS.md``.
"""

from __future__ import annotations

CMD_FILE_TYPE_ASSOCIATIONS = "File type associations…"

TITLE = "File type associations"
WINDOWS_ONLY = "File type associations are only supported on Windows."
FAILED_FMT = "Could not update the file associations:\n{error}"
DIALOG_MESSAGE = (
    "Check the file types FastFileViewer should offer to open.\n\n"
    "Checking a type makes FastFileViewer choosable for it (right-click → Open "
    "with). Windows blocks apps from silently forcing the default, so making it "
    "the default is confirmed by you in the Default Apps window."
)
APPLIED_INSTRUCTIONS = (
    "The file associations were updated.\n\n"
    'Press OK to open the Default Apps window: pick "FastFileViewer", then set '
    "it as the default for the file types you want."
)
REMOVED_ALL = "FastFileViewer was removed from all file-type associations."

BTN_SELECT_ALL = "Select all"
BTN_UNSELECT_ALL = "Unselect all"

KIND_PDF = "PDF document"
KIND_TEXT = "Text"
KIND_MARKDOWN = "Markdown"
KIND_IMAGE = "Image"
