"""Unit tests for the release-notes dialog navigation and rendering."""

from __future__ import annotations

from app.gui import release_strings
from app.gui.release_notes_dialog import ReleaseNotesDialog
from app.release.notes_loader import ReleaseNote


def _note(version: str, build: int, title: str) -> ReleaseNote:
    return ReleaseNote(version, build, "2026-01-01", title, ("a", "b"))


def test_empty_shows_placeholder_and_disables_nav(qapp: object) -> None:
    dialog = ReleaseNotesDialog([])
    assert dialog._heading.text() == release_strings.EMPTY
    assert dialog._older.isEnabled() is False
    assert dialog._newer.isEnabled() is False


def test_starts_on_newest(qapp: object) -> None:
    notes = [_note("0.2.0", 1, "Newest"), _note("0.1.0", 1, "Older")]
    dialog = ReleaseNotesDialog(notes)
    assert "Newest" in dialog._heading.text()
    # Newest shown: cannot go newer, can go older.
    assert dialog._newer.isEnabled() is False
    assert dialog._older.isEnabled() is True


def test_older_then_newer_navigates(qapp: object) -> None:
    notes = [_note("0.2.0", 1, "Newest"), _note("0.1.0", 1, "Older")]
    dialog = ReleaseNotesDialog(notes)
    dialog._show_older()
    assert "Older" in dialog._heading.text()
    assert dialog._older.isEnabled() is False  # oldest reached
    dialog._show_newer()
    assert "Newest" in dialog._heading.text()


def test_body_lists_notes_as_bullets(qapp: object) -> None:
    dialog = ReleaseNotesDialog([_note("0.1.0", 1, "T")])
    body = dialog._body.toPlainText()
    assert "a" in body
    assert "b" in body
