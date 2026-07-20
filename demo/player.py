"""FastFileViewer's demo player: the connector's key-event player + OpenFile."""

from __future__ import annotations

from typing import TYPE_CHECKING

from automated_screenshot_connector.qt import KeyEventDemoPlayer

from demo.steps import OpenFile

if TYPE_CHECKING:
    from automated_screenshot_connector import DemoClient, DemoScript

    from app.gui.main_window import MainWindow


class ViewerDemoPlayer(KeyEventDemoPlayer):
    """Adds the OpenFile step; all key/typing playback is inherited."""

    def __init__(
        self,
        window: MainWindow,
        client: DemoClient,
        script: DemoScript,
        hwnd: int | None,
    ) -> None:
        super().__init__(window, client, script, hwnd)
        self._main_window = window

    def handle_step(self, step: object) -> None:
        if isinstance(step, OpenFile):
            self._main_window.open_pdf(step.path())
            return
        super().handle_step(step)

    def _finish(self) -> None:
        # Demos mutate the working copy (rotate etc.) but never save; drop the
        # edits so quitting doesn't pop the unsaved-changes dialog.
        self._main_window.discard_changes()
        super()._finish()
