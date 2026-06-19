"""UI strings for the release-notes menu entry, command, and dialog.

Split out of :mod:`app.gui.strings` (which is at its size limit) so the
release-notes feature owns its display strings in one domain-grouped place.
"""

from __future__ import annotations

ACTION_RELEASE_NOTES = "Release notes…"
CMD_RELEASE_NOTES = "Show release notes / what's new"

TITLE = "Release notes"
EMPTY = "No release notes yet."
OLDER = "← Older"
NEWER = "Newer →"
HEADER_FMT = "{title}  —  {label}  ({date})        {position}/{total}"
BULLET = "•  {note}"
