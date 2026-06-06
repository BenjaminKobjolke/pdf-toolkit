"""Move the current page to a new position (deferred to the working copy)."""

from __future__ import annotations

from app.gui.deferred_ops import DeferredOps
from app.pdf.mover import move_page


class MoveActions:
    """Move-current-page commands bound to the open document."""

    def __init__(self, deferred: DeferredOps) -> None:
        self._deferred = deferred
        self._page_view = deferred.page_view

    def move_to_next(self) -> None:
        self._move(self._page_view.current_page_one_based() + 1)

    def move_to_prev(self) -> None:
        self._move(self._page_view.current_page_one_based() - 1)

    def move_to_first(self) -> None:
        self._move(1)

    def move_to_last(self) -> None:
        self._move(self._page_view.total_pages())

    def _move(self, to_page: int) -> None:
        if self._deferred.working() is None:
            return
        current = self._page_view.current_page_one_based()
        total = self._page_view.total_pages()
        if to_page < 1 or to_page > total or to_page == current:
            return
        self._deferred.run(lambda p: move_page(p, current, to_page), follow_page=to_page)
