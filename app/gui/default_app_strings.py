"""UI strings for the 'Set as default PDF viewer' commands and dialogs.

Split out of :mod:`app.gui.strings` (which is at its size limit) so the
default-PDF-handler feature owns its display strings in one domain-grouped place.
See ``docs/DEFAULT_PDF_VIEWER.md``.
"""

from __future__ import annotations

CMD_SET_DEFAULT_PDF_VIEWER = "Set as default PDF viewer…"
CMD_REMOVE_PDF_HANDLER = "Remove as PDF handler"

TITLE = "Set as default PDF viewer"
WINDOWS_ONLY = "Setting the default PDF viewer is only supported on Windows."
FAILED_FMT = "Could not register as a PDF handler:\n{error}"
INSTRUCTIONS = (
    "FastPDFToolkit was registered as a PDF handler.\n\n"
    "Windows blocks apps from silently forcing the default. Press OK to open the "
    'Default Apps window, then find ".pdf", choose "PDF (pdf-toolkit viewer)", set default.'
)
REMOVED = "FastPDFToolkit was removed as a PDF handler."
REMOVE_FAILED_FMT = "Could not remove the PDF handler:\n{error}"
