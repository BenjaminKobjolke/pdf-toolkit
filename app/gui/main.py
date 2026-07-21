"""QApplication bootstrap for the GUI viewer.

Supports the automation-demo contract via the automated-screenshot-connector
library: ``--automation-demo <id>`` plays a scripted, recordable demo against
a wiped temp settings DB and exits.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from automated_screenshot_connector import DemoOptions, parse_demo_args
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.app_logger import configure_logging, log
from app.config.instance_settings import InstanceSettingsStore
from app.config.settings import Settings
from app.gui import single_instance
from app.gui.main_window import MainWindow
from app.gui.resources import app_icon, set_app_user_model_id
from app.gui.single_instance import InstanceServer
from app.storage.factory import make_backend

__all__ = ["InstanceServer", "main", "single_instance"]


def main(argv: list[str] | None = None) -> int:
    """Launch the viewer. ``argv`` may carry a PDF path to open on startup."""
    args = list(sys.argv[1:]) if argv is None else argv
    options, args = parse_demo_args(args)
    settings = Settings.from_env()
    if options.demo is not None:
        from demo.bootstrap import prepare_demo_database
        from demo.scripts import DEMOS

        if options.demo not in DEMOS:
            print(f"unknown demo id {options.demo} (available: {sorted(DEMOS)})", file=sys.stderr)
            return 2
        # Deterministic clean state; the user's real settings DB stays untouched.
        settings = replace(settings, database_url=prepare_demo_database(options.demo_settings))
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

    if options.demo is not None:
        return _run_demo(app, settings, options)

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


def _run_demo(app: QApplication, settings: Settings, options: DemoOptions) -> int:
    """Play one scripted demo and exit. No single-instance forwarding/serving —
    the recording must never land in (or collide with) a real running viewer."""
    from automated_screenshot_connector import DemoClient

    from demo.player import ViewerDemoPlayer
    from demo.scripts import DEMOS
    from demo.steps import localize_viewer_script

    assert options.demo is not None
    window = MainWindow(settings)
    # No scrollbars in recordings: content is sized to the window, and a
    # scrollbar would show as a stray line in the capture.
    for orientation_off in (
        window.page_view.setVerticalScrollBarPolicy,
        window.page_view.setHorizontalScrollBarPolicy,
    ):
        orientation_off(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    script = localize_viewer_script(DEMOS[options.demo], dict(options.demo_texts))
    client = DemoClient(options.demo_port)
    window.show()
    # Fix the size AFTER show: the first show pass re-lays the window out to
    # Qt's screen-derived default and discards a pre-show resize. Fixed (not
    # just resized) so the mode status bar appearing on document open can't
    # grow the window and drift the recording off the configured aspect ratio.
    if options.demo_width is not None and options.demo_height is not None:
        window.setFixedSize(options.demo_width, options.demo_height)
    # winId() is the native HWND, valid once the window is shown
    player = ViewerDemoPlayer(window, client, script, hwnd=int(window.winId()))
    player.start()
    return int(app.exec())


def _raise_above_others(window: MainWindow) -> None:
    """Bring the window to the front of the Z-order WITHOUT taking keyboard focus.

    On Windows a background window can't reach the front with ``raise_()`` alone
    (that only reorders within our own app). Toggling the topmost flag on and off
    with ``SWP_NOACTIVATE`` reorders it above other apps' windows while leaving
    keyboard focus wherever the user is typing.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(window.winId())
        HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
        SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
        set_pos = ctypes.windll.user32.SetWindowPos
        set_pos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
        set_pos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    except (AttributeError, OSError):  # pragma: no cover - defensive, never fatal
        log.debug("single-instance: raise-above-others failed", exc_info=True)


def _open_in(window: MainWindow, path: Path | None) -> None:
    """Handle a forwarded open request: load the file, then surface the window."""
    if path is not None:
        window.open_pdf(path)  # unsaved-changes prompt handled inside
    # Always surface the window — a forwarded open must never look like nothing
    # happened. Only grab keyboard focus when the user opted in.
    window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
    window.show()
    window.raise_()
    if window.instance_controller.focus_on_forward:
        window.activateWindow()
    else:
        _raise_above_others(window)  # front, but don't steal focus


if __name__ == "__main__":
    sys.exit(main())
