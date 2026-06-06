"""QApplication bootstrap for the GUI viewer."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.config.settings import Settings
from app.gui.main_window import MainWindow
from app.gui.resources import app_icon, set_app_user_model_id
from app.logging_setup import configure_logging


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
    window = MainWindow(settings)
    if args:
        window.open_pdf(Path(args[0]))
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
