"""Unit tests for the shared type-to-filter list dialog."""

from __future__ import annotations

from pathlib import Path

from app.gui.filter_list_dialog import FilterListDialog, ListEntry


def _titles(dialog: FilterListDialog) -> list[str]:
    return [dialog.visible_entry(i).title for i in range(dialog.visible_count())]


def test_shows_all_enabled_entries(qapp: object) -> None:
    entries = [ListEntry(title="Zoom in"), ListEntry(title="Zoom out")]
    dialog = FilterListDialog(entries)
    assert _titles(dialog) == ["Zoom in", "Zoom out"]


def test_substring_filter_narrows_case_insensitive(qapp: object) -> None:
    entries = [
        ListEntry(title="Zoom in"),
        ListEntry(title="Next page"),
        ListEntry(title="Zoom out"),
    ]
    dialog = FilterListDialog(entries)
    dialog.set_filter("zoom")
    assert _titles(dialog) == ["Zoom in", "Zoom out"]


def test_disabled_entries_are_skipped(qapp: object) -> None:
    entries = [ListEntry(title="Open"), ListEntry(title="Close", enabled=False)]
    dialog = FilterListDialog(entries)
    assert _titles(dialog) == ["Open"]


def test_enter_accepts_highlighted_command_payload(qapp: object) -> None:
    entries = [ListEntry(title="A", payload="pa"), ListEntry(title="B", payload="pb")]
    dialog = FilterListDialog(entries)
    dialog.set_filter("b")
    dialog.accept_current()
    chosen = dialog.chosen()
    assert chosen is not None
    assert chosen.payload == "pb"


def test_enter_accepts_path_payload_for_history(qapp: object) -> None:
    entries = [ListEntry(title="doc.pdf", subtitle="/docs/doc.pdf", payload=Path("/docs/doc.pdf"))]
    dialog = FilterListDialog(entries)
    dialog.accept_current()
    chosen = dialog.chosen()
    assert chosen is not None
    assert chosen.payload == Path("/docs/doc.pdf")


def test_move_selection_wraps(qapp: object) -> None:
    entries = [ListEntry(title="A"), ListEntry(title="B")]
    dialog = FilterListDialog(entries)
    dialog.move_selection(1)  # A -> B
    dialog.move_selection(1)  # B -> A (wrap)
    current = dialog.current_entry()
    assert current is not None
    assert current.title == "A"


def test_no_match_yields_no_chosen(qapp: object) -> None:
    dialog = FilterListDialog([ListEntry(title="A")])
    dialog.set_filter("zzz")
    dialog.accept_current()
    assert dialog.chosen() is None
