"""Pure keymap merge/mutations and the JSON-backed override store."""

from __future__ import annotations

from pathlib import Path

from app.config.key_bindings import (
    KeyBindingStore,
    KeyOverride,
    assign,
    merge_keymap,
    remove_chord,
    remove_command,
)
from app.storage.sqlite_backend import SqliteBackend

_DEFAULTS = [
    ("Ctrl+S", "save"),
    ("Ctrl++", "zoom_in"),
    ("Ctrl+=", "zoom_in"),
    ("Ctrl+Shift+P", "command_palette"),
]


def _store(tmp_path: Path) -> KeyBindingStore:
    return KeyBindingStore(SqliteBackend(tmp_path / "db.sqlite"))


# --- merge --------------------------------------------------------------------


def test_merge_defaults_only() -> None:
    keymap = merge_keymap(_DEFAULTS, ())
    assert keymap.command_for("Ctrl+S") == "save"
    assert keymap.chords_for("zoom_in") == ("Ctrl++", "Ctrl+=")


def test_override_adds_new_chord() -> None:
    keymap = merge_keymap(_DEFAULTS, (KeyOverride("Alt+W", "exit"),))
    assert keymap.command_for("Alt+W") == "exit"
    assert keymap.command_for("Ctrl+S") == "save"


def test_override_reassigns_default_chord() -> None:
    keymap = merge_keymap(_DEFAULTS, (KeyOverride("Ctrl+S", "exit"),))
    assert keymap.command_for("Ctrl+S") == "exit"
    assert keymap.chords_for("save") == ()


def test_tombstone_deletes_default() -> None:
    keymap = merge_keymap(_DEFAULTS, (KeyOverride("Ctrl+S", None),))
    assert keymap.command_for("Ctrl+S") is None
    assert keymap.chords_for("save") == ()


def test_new_future_default_appears_unless_tombstoned() -> None:
    defaults = [*_DEFAULTS, ("F5", "refresh")]
    assert merge_keymap(defaults, ()).command_for("F5") == "refresh"
    tombstoned = merge_keymap(defaults, (KeyOverride("F5", None),))
    assert tombstoned.command_for("F5") is None


# --- mutations ----------------------------------------------------------------


def test_assign_upserts_unique_chord() -> None:
    overrides = assign((KeyOverride("Alt+W", "exit"),), "Alt+W", "save")
    assert overrides == (KeyOverride("Alt+W", "save"),)


def test_remove_command_tombstones_every_chord() -> None:
    overrides = remove_command((), _DEFAULTS, "zoom_in")
    keymap = merge_keymap(_DEFAULTS, overrides)
    assert keymap.chords_for("zoom_in") == ()
    assert keymap.command_for("Ctrl+S") == "save"


def test_remove_command_includes_user_added_chord() -> None:
    overrides = assign((), "Alt+S", "save")
    overrides = remove_command(overrides, _DEFAULTS, "save")
    keymap = merge_keymap(_DEFAULTS, overrides)
    assert keymap.chords_for("save") == ()


def test_remove_chord_tombstones_only_named_chord() -> None:
    overrides = remove_chord((), "Ctrl++")
    keymap = merge_keymap(_DEFAULTS, overrides)
    assert keymap.chords_for("zoom_in") == ("Ctrl+=",)  # sibling chord survives


# --- store --------------------------------------------------------------------


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert _store(tmp_path).load() == ()


def test_save_then_load_round_trips_with_tombstone(tmp_path: Path) -> None:
    store = _store(tmp_path)
    overrides = (KeyOverride("Alt+W", "exit"), KeyOverride("Ctrl+S", None))
    store.save(overrides)
    assert store.load() == overrides


def test_store_has_remembered_label(tmp_path: Path) -> None:
    assert _store(tmp_path).label == "Keyboard shortcuts"
