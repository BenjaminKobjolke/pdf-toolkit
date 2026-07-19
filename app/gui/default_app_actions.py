"""Palette action to manage the viewer's Windows file-type associations.

Association only makes the viewer a *choosable* handler; Windows blocks apps
from silently forcing the default, so after applying we open the Default Apps
settings page (deep-linked to the app on Win11) and tell the user how to
finish. See ``app.os_integration.file_association``.
"""

from __future__ import annotations

import os

from PySide6.QtWidgets import QWidget

from app.app_logger import log
from app.gui import default_app_strings as ds
from app.gui.confirm_dialog import Severity, show_message
from app.gui.file_association_dialog import ask_associations
from app.os_integration import file_association

# Must match the RegisteredApplications value name; Win10 ignores the query
# part and just opens the plain Default Apps page.
_DEFAULT_APPS_URI = f"ms-settings:defaultapps?registeredAppUser={file_association.APP_NAME}"


class DefaultAppActions:
    """Edit the viewer's file-type associations from the palette."""

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent

    def configure_file_associations(self) -> None:
        """Show the checklist dialog and make the registry match the answer."""
        if not file_association.is_supported():
            self._warn(ds.WINDOWS_ONLY)
            return
        checked = file_association.registered_extensions()
        selection = ask_associations(self._parent, checked=checked)
        if selection is None:
            return
        result = file_association.set_associations(selection)
        if not result.ok:
            self._error(ds.FAILED_FMT.format(error=result.error))
            return
        if selection:
            show_message(self._parent, ds.TITLE, ds.APPLIED_INSTRUCTIONS)
            self._open_default_apps_settings()
        else:
            show_message(self._parent, ds.TITLE, ds.REMOVED_ALL)

    def _open_default_apps_settings(self) -> None:
        """Open the Windows Default Apps page; non-fatal if it cannot open."""
        try:
            os.startfile(_DEFAULT_APPS_URI)  # noqa: S606
        except OSError as err:
            log.warning("could not open default-apps settings: %s", err)

    def _warn(self, message: str) -> None:
        show_message(self._parent, ds.TITLE, message, Severity.WARNING)

    def _error(self, message: str) -> None:
        show_message(self._parent, ds.TITLE, message, Severity.ERROR)
