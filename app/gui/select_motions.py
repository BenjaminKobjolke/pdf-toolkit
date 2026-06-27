"""Pure vim-style cursor motions over a list of :class:`WordBox` (no Qt, no PDF).

Every motion takes the word list and the current cursor index and returns the new
index, clamped to the list. Kept Qt-free so the navigation logic is unit-tested
directly. The controller (:mod:`app.gui.select_controller`) wires these to keys,
the scene, and the clipboard.
"""

from __future__ import annotations

from app.pdf.words import WordBox


def next_word(words: list[WordBox], cursor: int) -> int:
    """Move to the next word in reading order (`l` / `w`)."""
    return min(cursor + 1, len(words) - 1)


def prev_word(words: list[WordBox], cursor: int) -> int:
    """Move to the previous word in reading order (`h` / `b`)."""
    return max(cursor - 1, 0)


def first_word(words: list[WordBox], cursor: int) -> int:
    """Jump to the first word on the page (`gg`)."""
    return 0


def last_word(words: list[WordBox], cursor: int) -> int:
    """Jump to the last word on the page (`G`)."""
    return len(words) - 1


def line_start(words: list[WordBox], cursor: int) -> int:
    """First word sharing the current word's line (`0`)."""
    key = words[cursor].line_key
    return next(i for i, w in enumerate(words) if w.line_key == key)


def line_end(words: list[WordBox], cursor: int) -> int:
    """Last word sharing the current word's line (`$`)."""
    key = words[cursor].line_key
    return max(i for i, w in enumerate(words) if w.line_key == key)


def line_down(words: list[WordBox], cursor: int) -> int:
    """Nearest word on the line below, by horizontal centre (`j`)."""
    return _vertical(words, cursor, step=1)


def line_up(words: list[WordBox], cursor: int) -> int:
    """Nearest word on the line above, by horizontal centre (`k`)."""
    return _vertical(words, cursor, step=-1)


def span_text(words: list[WordBox], a: int, b: int) -> str:
    """Join words ``a..b`` (inclusive, any order): spaces within a line, newline across."""
    lo, hi = sorted((a, b))
    out = ""
    prev_key: tuple[int, int] | None = None
    for word in words[lo : hi + 1]:
        if prev_key is None:
            out = word.text
        elif word.line_key != prev_key:
            out += "\n" + word.text
        else:
            out += " " + word.text
        prev_key = word.line_key
    return out


def word_in_rect(words: list[WordBox], x0: float, y0: float, x1: float, y1: float) -> int | None:
    """First word (lowest index) whose box intersects the rect; None if none.

    Used to seed the cursor from a search highlight: the match's first word.
    """
    for word in words:
        if word.x0 < x1 and word.x1 > x0 and word.y0 < y1 and word.y1 > y0:
            return word.index
    return None


def word_at_point(words: list[WordBox], x: float, y: float) -> int | None:
    """Word whose box contains (x, y), else the nearest by centre; None if empty.

    Used for click-to-place. Coordinates are in PDF points.
    """
    if not words:
        return None
    for word in words:
        if word.x0 <= x <= word.x1 and word.y0 <= y <= word.y1:
            return word.index
    return min(
        range(len(words)),
        key=lambda i: (_center_x(words[i]) - x) ** 2 + (_center_y(words[i]) - y) ** 2,
    )


def _line_order(words: list[WordBox]) -> list[tuple[int, int]]:
    """Distinct line keys in the order they first appear (reading order)."""
    order: list[tuple[int, int]] = []
    for word in words:
        if word.line_key not in order:
            order.append(word.line_key)
    return order


def _center_x(word: WordBox) -> float:
    return (word.x0 + word.x1) / 2.0


def _center_y(word: WordBox) -> float:
    return (word.y0 + word.y1) / 2.0


def _vertical(words: list[WordBox], cursor: int, step: int) -> int:
    """Move to the adjacent line (``step`` ±1), staying nearest by horizontal centre."""
    order = _line_order(words)
    target_pos = order.index(words[cursor].line_key) + step
    if not 0 <= target_pos < len(order):
        return cursor  # already at the top/bottom line
    target_key = order[target_pos]
    cx = _center_x(words[cursor])
    candidates = [i for i, w in enumerate(words) if w.line_key == target_key]
    return min(candidates, key=lambda i: abs(_center_x(words[i]) - cx))
