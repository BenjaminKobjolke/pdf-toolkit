"""Unit tests for the shared type-to-filter list dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

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


def test_bold_entry_renders_with_bold_font(qapp: object) -> None:
    entries = [ListEntry(title="Recent", bold=True), ListEntry(title="Other")]
    dialog = FilterListDialog(entries)
    assert dialog._list.item(0).font().bold() is True
    assert dialog._list.item(1).font().bold() is False


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


def test_multi_token_filter_ignores_word_order_and_punctuation(qapp: object) -> None:
    entries = [ListEntry(title="Field: delete"), ListEntry(title="Field: change text…")]
    dialog = FilterListDialog(entries)
    dialog.set_filter("field del")
    assert _titles(dialog) == ["Field: delete"]


def test_token_filter_requires_all_tokens(qapp: object) -> None:
    entries = [ListEntry(title="Zoom in"), ListEntry(title="Zoom out")]
    dialog = FilterListDialog(entries)
    dialog.set_filter("zoom out")
    assert _titles(dialog) == ["Zoom out"]


def test_no_match_yields_no_chosen(qapp: object) -> None:
    dialog = FilterListDialog([ListEntry(title="A")])
    dialog.set_filter("zzz")
    dialog.accept_current()
    assert dialog.chosen() is None


def _provider_titles(dialog: FilterListDialog) -> list[str]:
    return [dialog.visible_entry(i).title for i in range(dialog.visible_count())]


def test_provider_mode_below_min_chars_shows_nothing(qapp: object) -> None:
    calls: list[str] = []

    def provider(text: str) -> list[ListEntry]:
        calls.append(text)
        return [ListEntry(title=f"hit:{text}")]

    dialog = FilterListDialog([], provider=provider, min_chars=3)
    dialog.set_filter("ab")
    assert _provider_titles(dialog) == []


def test_provider_mode_runs_at_min_chars(qapp: object) -> None:
    def provider(text: str) -> list[ListEntry]:
        return [ListEntry(title=f"hit:{text}", payload=text)]

    dialog = FilterListDialog([], provider=provider, min_chars=3)
    dialog.set_filter("abc")
    assert _provider_titles(dialog) == ["hit:abc"]


def test_provider_reruns_per_keystroke(qapp: object) -> None:
    calls: list[str] = []

    def provider(text: str) -> list[ListEntry]:
        calls.append(text)
        return [ListEntry(title=text)]

    dialog = FilterListDialog([], provider=provider, min_chars=1)
    dialog.set_filter("a")
    dialog.set_filter("ab")
    assert calls == ["a", "ab"]


def test_shortcut_carried_on_item_role_when_shown(qapp: object) -> None:
    entries = [ListEntry(title="Exit", shortcut="Alt+W")]
    dialog = FilterListDialog(entries, show_shortcuts=True)
    assert dialog._list.item(0).data(Qt.ItemDataRole.UserRole) == "Alt+W"


def test_delete_key_invokes_on_delete_with_current_entry(qapp: object) -> None:
    deleted: list[str] = []
    entries = [ListEntry(title="Exit", payload="exit")]
    dialog = FilterListDialog(entries, on_delete=lambda entry: deleted.append(entry.payload))
    assert dialog._on_delete_key() is True
    assert deleted == ["exit"]


def test_delete_key_noop_without_callback(qapp: object) -> None:
    dialog = FilterListDialog([ListEntry(title="Exit")])
    assert dialog._on_delete_key() is False


def test_provider_accept_returns_payload(qapp: object) -> None:
    def provider(text: str) -> list[ListEntry]:
        return [ListEntry(title="match", payload=(1, 2))]

    dialog = FilterListDialog([], provider=provider, min_chars=3)
    dialog.set_filter("abc")
    dialog.accept_current()
    chosen = dialog.chosen()
    assert chosen is not None
    assert chosen.payload == (1, 2)
