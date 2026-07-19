"""Vim-style text select / copy mode for the page view.

A peer of View/Edit mode: a keyboard cursor hops between PDF words (geometry from
:func:`app.pdf.words.page_words`), `v` starts a visual selection, and `y` copies
the span to the clipboard. Motion math lives in :mod:`app.gui.select_motions`;
this controller owns the mode state and wires it to the scene overlay
(:class:`SelectionHighlights`), the status bar, and the clipboard.

Single-page scope: the selection never spans page boundaries; changing pages
reloads the words and resets the cursor.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.gui import render, select_strings
from app.gui import select_motions as motions
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.page_view import PageView
from app.pdf.words import WordBox, page_words

# text() -> motion. Letters are matched on their exact glyph so `g`/`G` differ.
_MOTIONS: dict[str, Callable[[list[WordBox], int], int]] = {
    "h": motions.prev_word,
    "l": motions.next_word,
    "b": motions.prev_word,
    "w": motions.next_word,
    "j": motions.line_down,
    "k": motions.line_up,
    "0": motions.line_start,
    "$": motions.line_end,
    "G": motions.last_word,
}

# Arrow keys mirror h/j/k/l (they carry no event.text(), so dispatch by key).
_ARROW_MOTIONS: dict[Qt.Key, Callable[[list[WordBox], int], int]] = {
    Qt.Key.Key_Left: motions.prev_word,
    Qt.Key.Key_Right: motions.next_word,
    Qt.Key.Key_Down: motions.line_down,
    Qt.Key.Key_Up: motions.line_up,
}


class SelectController:
    """Owns select-mode state and dispatches its keys for a :class:`PageView`."""

    def __init__(
        self, page_view: PageView, mode_bar: ModeStatusBar, exit_edit_mode: Callable[[], None]
    ) -> None:
        self._page_view = page_view
        self._mode_bar = mode_bar
        self._exit_edit_mode = exit_edit_mode
        self._active = False
        self._words: list[WordBox] = []
        self._cursor = 0
        self._anchor: int | None = None  # None => not in visual selection
        self._pending_g = False  # first `g` of a `gg` motion
        page_view.page_changed.connect(self._on_page_changed)

    # --- mode lifecycle -----------------------------------------------------

    def is_active(self) -> bool:
        return self._active

    def toggle(self) -> None:
        self.set_active(not self._active)

    def set_active(self, on: bool) -> None:
        """Enter/leave select mode. Entering first leaves edit mode (mutually exclusive)."""
        if on == self._active:
            return
        self._active = on
        if on:
            self._exit_edit_mode()
            self._load()
            self._seed_from_search()
            self._refresh()
        else:
            self._page_view.selection_highlights().clear()
            self._mode_bar.set_edit_mode(False)

    def on_edit_mode_toggled(self, edit_on: bool) -> None:
        """Leave select mode whenever edit mode is switched on (mutually exclusive)."""
        if edit_on:
            self.set_active(False)

    def _seed_from_search(self) -> None:
        """Start the cursor on the active search match, if one is highlighted."""
        rects = self._page_view.highlight_rects_points()
        if not (rects and self._words):
            return
        idx = motions.word_in_rect(self._words, rects[0])
        if idx is not None:
            self._cursor = idx
            self._page_view.clear_highlights()  # gold seed consumed; blue cursor takes over

    # --- mouse --------------------------------------------------------------

    def handle_click(self, scene_pt: QPointF) -> bool:
        """Place the cursor on the clicked word. Returns True when active (modal)."""
        if not self._active:
            return False
        if self._words:
            z = render.DEFAULT_ZOOM
            idx = motions.word_at_point(self._words, scene_pt.x() / z, scene_pt.y() / z)
            if idx is not None:
                self._cursor = idx
                self._refresh()
        return True

    # --- key handling -------------------------------------------------------

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle a key while active. Returns True when consumed."""
        if not self._active:
            return False
        key = Qt.Key(event.key())
        if key == Qt.Key.Key_Escape:
            self.set_active(False)
            return True
        text = event.text()
        if text != "g":
            self._pending_g = False
        if text == "q":
            self.set_active(False)
            return True
        if text == "v":
            self._anchor = None if self._anchor is not None else self._cursor
            self._refresh()
            return True
        if text == "y":
            self._yank()
            return True
        if text == "g":
            return self._handle_g()
        motion = _MOTIONS.get(text) or _ARROW_MOTIONS.get(key)
        if motion is not None and self._words:
            self._cursor = motion(self._words, self._cursor)
            self._refresh()
            return True
        return False

    def _handle_g(self) -> bool:
        if self._pending_g and self._words:
            self._cursor = motions.first_word(self._words, self._cursor)
            self._pending_g = False
            self._refresh()
        else:
            self._pending_g = True
        return True

    def _yank(self) -> None:
        if not self._words:
            return
        start = self._cursor if self._anchor is None else self._anchor
        QApplication.clipboard().setText(motions.span_text(self._words, start, self._cursor))
        self._anchor = None  # leave visual selection after a yank, like vim
        self._refresh()

    # --- state --------------------------------------------------------------

    def _load(self) -> None:
        source = self._page_view.source()
        self._words = page_words(source, self._page_view.current_page_index()) if source else []
        self._cursor = 0
        self._anchor = None
        self._pending_g = False

    def _on_page_changed(self, _current: int, _total: int) -> None:
        if not self._active:
            return
        self._load()
        self._refresh()

    def _refresh(self) -> None:
        highlights = self._page_view.selection_highlights()
        if not self._words:
            highlights.clear()
            self._mode_bar.set_hint(select_strings.MODE_SELECT)
            return
        highlights.set_cursor(self._words[self._cursor])
        if self._anchor is not None:
            lo, hi = sorted((self._anchor, self._cursor))
            highlights.set_span(self._words[lo : hi + 1])
            self._mode_bar.set_hint(select_strings.MODE_SELECT_VISUAL)
        else:
            highlights.set_span([])
            self._mode_bar.set_hint(select_strings.MODE_SELECT)
