"""Unit tests for the pure vim-style cursor motion math (no Qt, no PDF)."""

from __future__ import annotations

from app.gui import select_motions as m
from app.pdf.words import WordBox


def _w(index: int, x0: float, x1: float, line: int, text: str) -> WordBox:
    """Build a word on the given line; y derived from the line so lines stack."""
    y0 = 10.0 + line * 20.0
    return WordBox(index=index, x0=x0, y0=y0, x1=x1, y1=y0 + 10.0, text=text, block=0, line=line)


# Two lines:
#   line 0: Hello[0] world[1]
#   line 1: Foo[2]   Bar[3]   Baz[4]
WORDS = [
    _w(0, 10, 50, 0, "Hello"),
    _w(1, 60, 100, 0, "world"),
    _w(2, 10, 40, 1, "Foo"),
    _w(3, 50, 80, 1, "Bar"),
    _w(4, 90, 120, 1, "Baz"),
]


def test_next_word_clamps_at_end() -> None:
    assert m.next_word(WORDS, 0) == 1
    assert m.next_word(WORDS, 4) == 4


def test_prev_word_clamps_at_start() -> None:
    assert m.prev_word(WORDS, 3) == 2
    assert m.prev_word(WORDS, 0) == 0


def test_line_start_and_end() -> None:
    assert m.line_start(WORDS, 3) == 2  # Bar -> Foo
    assert m.line_end(WORDS, 2) == 4  # Foo -> Baz
    assert m.line_start(WORDS, 1) == 0  # world -> Hello
    assert m.line_end(WORDS, 0) == 1  # Hello -> world


def test_first_and_last_word() -> None:
    assert m.first_word(WORDS, 3) == 0
    assert m.last_word(WORDS, 1) == 4


def test_line_down_picks_nearest_by_center() -> None:
    assert m.line_down(WORDS, 0) == 2  # Hello (center 30) -> Foo (center 25)
    assert m.line_down(WORDS, 1) == 3  # world (center 80) -> Bar (center 65)


def test_line_up_picks_nearest_by_center() -> None:
    assert m.line_up(WORDS, 4) == 1  # Baz (center 105) -> world (center 80)
    assert m.line_up(WORDS, 2) == 0  # Foo (center 25) -> Hello (center 30)


def test_vertical_clamps_at_edges() -> None:
    assert m.line_up(WORDS, 0) == 0  # no line above
    assert m.line_down(WORDS, 4) == 4  # no line below


def test_span_text_joins_within_line_with_spaces() -> None:
    assert m.span_text(WORDS, 0, 1) == "Hello world"
    assert m.span_text(WORDS, 2, 4) == "Foo Bar Baz"


def test_span_text_breaks_lines_with_newline() -> None:
    assert m.span_text(WORDS, 1, 3) == "world\nFoo Bar"


def test_span_text_is_order_independent() -> None:
    assert m.span_text(WORDS, 3, 1) == m.span_text(WORDS, 1, 3)


def test_span_text_single_word() -> None:
    assert m.span_text(WORDS, 2, 2) == "Foo"


def test_word_in_rect_returns_first_overlapping() -> None:
    # A rect over "Bar" (x 50-80, line 1 at y 30-40).
    assert m.word_in_rect(WORDS, 52, 31, 78, 39) == 3
    # A rect spanning Foo+Bar -> first (lowest index) overlapping word.
    assert m.word_in_rect(WORDS, 20, 31, 60, 39) == 2


def test_word_in_rect_none_when_disjoint() -> None:
    assert m.word_in_rect(WORDS, 200, 200, 220, 220) is None


def test_word_at_point_inside_box() -> None:
    assert m.word_at_point(WORDS, 30, 15) == 0  # inside "Hello"
    assert m.word_at_point(WORDS, 65, 35) == 3  # inside "Bar"


def test_word_at_point_nearest_when_between() -> None:
    # Just right of "world" on its line; nearest centre is world, not the line below.
    assert m.word_at_point(WORDS, 100, 15) == 1


def test_word_at_point_none_on_empty() -> None:
    assert m.word_at_point([], 10, 10) is None
