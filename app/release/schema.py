"""String constants for the release-notes JSON schema and on-disk layout.

One release lives in ``release_notes/<version>_<build>/<locale>.json``. Only
``en.json`` is authored by hand; other locales are produced by the translation
bat from that English source. The actual release text is the :data:`KEY_NOTES`
array; the other keys are metadata.
"""

from __future__ import annotations

# Folder / file names
RELEASE_NOTES_DIRNAME = "release_notes"
BUILD_FILE_NAME = "build_version.txt"
DEFAULT_LOCALE = "en"
LOCALE_FILE_FMT = "{locale}.json"
FOLDER_NAME_FMT = "{version}_{build}"

# JSON keys
KEY_VERSION = "version"
KEY_BUILD = "build"
KEY_DATE = "date"
KEY_TITLE = "title"
KEY_NOTES = "notes"
