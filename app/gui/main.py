"""QApplication bootstrap for the GUI viewer."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.config.instance_settings import InstanceSettingsStore
from app.config.settings import Settings
from app.gui import single_instance
from app.gui.main_window import MainWindow
from app.gui.resources import app_icon, set_app_user_model_id
from app.gui.single_instance import InstanceServer
from app.logging_setup import configure_logging, log
from app.storage.factory import make_backend

__all__ = ["InstanceServer", "main", "single_instance"]


def main(argv: list[str] | None = None) -> int:
    """Launch the viewer. ``argv`` may carry a PDF path to open on startup."""
    args = list(sys.argv[1:]) if argv is None else argv
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    set_app_user_model_id()
    # Keep fractional Windows display scaling (125/150%) un-rounded so the page
    # renders at the screen's true pixel density instead of being upscaled blurry.
    # Must be set before the QApplication exists.
    if QApplication.instance() is None:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication([])
    app.setWindowIcon(app_icon())

    path = Path(args[0]) if args else None
    reuse = InstanceSettingsStore(make_backend(settings.database_url)).load().reuse_window
    if reuse and single_instance.try_send_to_running(path):
        log.info("single-instance: forwarded to running viewer, exiting")
        return 0

    window = MainWindow(settings)
    # Always listen, even with reuse off: the running viewer can serve future
    # launches the moment the user toggles the setting on — no restart needed.
    server = InstanceServer(lambda p: _open_in(window, p))
    server.start()
    if path is not None:
        window.open_pdf(path)
    window.show()
    exit_code = int(app.exec())
    server.stop()
    return exit_code


def _open_in(window: MainWindow, path: Path | None) -> None:
    """Handle a forwarded open request: load the file, then bring us frontmost."""
    if path is not None:
        window.open_pdf(path)  # unsaved-changes prompt handled inside
    if not window.instance_controller.focus_on_forward:
        return
    window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
    window.show()
    window.raise_()
    window.activateWindow()


if __name__ == "__main__":
    sys.exit(main())
