"""Integration test: bundled release-notes tree loads into ordered dialog input."""

from __future__ import annotations

import json
from pathlib import Path

from app.gui.release_notes_dialog import ReleaseNotesDialog
from app.release import schema
from app.release.notes_loader import load_release_notes


def _seed(root: Path, version: str, build: int, title: str) -> None:
    folder = root / schema.FOLDER_NAME_FMT.format(version=version, build=build)
    folder.mkdir(parents=True)
    payload = {
        schema.KEY_VERSION: version,
        schema.KEY_BUILD: build,
        schema.KEY_DATE: "2026-06-19",
        schema.KEY_TITLE: title,
        schema.KEY_NOTES: [f"{title} note 1", f"{title} note 2"],
    }
    (folder / "en.json").write_text(json.dumps(payload), encoding="utf-8")


def test_tree_loads_ordered_and_feeds_dialog(qapp: object, tmp_path: Path) -> None:
    _seed(tmp_path, "0.1.0", 1, "First")
    _seed(tmp_path, "0.1.0", 2, "Second")
    _seed(tmp_path, "0.2.0", 1, "Third")

    notes = load_release_notes(root=tmp_path)
    assert [n.label for n in notes] == ["0.2.0_1", "0.1.0_2", "0.1.0_1"]

    dialog = ReleaseNotesDialog(notes)
    assert "Third" in dialog._heading.text()
    assert dialog._body.toPlainText().startswith("•")
