"""QApplication bootstrap for the GUI viewer."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.config.settings import Settings
from app.gui.main_window import MainWindow
from app.logging_setup import configure_logging


def main(argv: list[str] | None = None) -> int:
    """Launch the viewer. ``argv`` may carry a PDF path to open on startup."""
    args = list(sys.argv[1:]) if argv is None else argv
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    app = QApplication.instance() or QApplication([])
    window = MainWindow(settings)
    if args:
        window.open_pdf(Path(args[0]))
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
