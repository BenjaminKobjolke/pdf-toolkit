"""Palette actions to register / unregister the app as the Windows PDF viewer.

Registration only makes the viewer a *choosable* handler; Windows blocks apps
from silently forcing the default, so after registering we open the Default Apps
settings page and tell the user how to finish. See ``app.os_integration``.
"""

from __future__ import annotations

import os

from PySide6.QtWidgets import QWidget

from app.gui import default_app_strings as ds
from app.gui.confirm_dialog import Severity, show_message
from app.logging_setup import log
from app.os_integration import pdf_association

_DEFAULT_APPS_URI = "ms-settings:defaultapps"


class DefaultAppActions:
    """Register / remove the viewer as a Windows PDF handler from the palette."""

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent

    def set_as_default_pdf_viewer(self) -> None:
        """Register as a PDF handler, then open Default Apps with instructions."""
        if not pdf_association.is_supported():
            self._warn(ds.WINDOWS_ONLY)
            return
        result = pdf_association.register_pdf_viewer()
        if not result.ok:
            self._error(ds.FAILED_FMT.format(error=result.error))
            return
        show_message(self._parent, ds.TITLE, ds.INSTRUCTIONS)
        self._open_default_apps_settings()

    def remove_pdf_handler(self) -> None:
        """Remove the PDF-handler registration created by the command above."""
        if not pdf_association.is_supported():
            self._warn(ds.WINDOWS_ONLY)
            return
        result = pdf_association.unregister_pdf_viewer()
        if not result.ok:
            self._error(ds.REMOVE_FAILED_FMT.format(error=result.error))
            return
        show_message(self._parent, ds.TITLE, ds.REMOVED)

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
