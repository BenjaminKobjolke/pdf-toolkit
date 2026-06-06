"""Shared runner for deferred page operations.

Bundles the collaborators every page-op action class needs (per "objects for
related values") and drives the run → reload → follow-page → mark-dirty flow once,
so :class:`PageActions`, :class:`RotateActions`, and :class:`MoveActions` don't
each repeat it. Success is silent — the re-render and the status-bar "Modified"
marker are the feedback; only failures raise a dialog.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.gui.operations import GuiOperationRunner, OpResult
from app.gui.page_view import PageView


@dataclass(frozen=True)
class DeferredOps:
    """Run a core op on the working copy, then refresh the view and mark dirty."""

    runner: GuiOperationRunner
    page_view: PageView
    working: Callable[[], Path | None]
    mark_dirty: Callable[[], None]
    report: Callable[[OpResult], None]

    def run(self, op: Callable[[Path], None], follow_page: int | None = None) -> None:
        """Run ``op`` on the working copy.

        On success, re-render (optionally jumping to ``follow_page``, 1-based) and
        mark the document dirty. On failure, surface the error.
        """
        target = self.working()
        if target is None:
            return
        result = self.runner.run_on_working(target, op)
        if not result.ok:
            self.report(result)
            return
        self.page_view.reload()
        if follow_page is not None:
            self.page_view.go_to_page(follow_page - 1)
        self.mark_dirty()
