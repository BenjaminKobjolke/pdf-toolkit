"""Unit tests for the pure file-browser filesystem logic (no Qt)."""

from __future__ import annotations

from pathlib import Path

from app.gui.file_browser_model import (
    FileFilter,
    FsEntry,
    drives,
    is_root,
    list_dir,
    parent_of,
    substring_filter,
)

PDF = FileFilter("pdf", (".pdf",))
ALL = FileFilter("all", ())


def _touch(path: Path) -> None:
    path.write_text("x")


def test_list_dir_dirs_first_then_alpha(tmp_path: Path) -> None:
    (tmp_path / "zeta").mkdir()
    (tmp_path / "alpha").mkdir()
    _touch(tmp_path / "b.pdf")
    _touch(tmp_path / "a.pdf")
    assert [e.name for e in list_dir(tmp_path, PDF)] == ["alpha", "zeta", "a.pdf", "b.pdf"]


def test_list_dir_filters_by_extension(tmp_path: Path) -> None:
    _touch(tmp_path / "keep.pdf")
    _touch(tmp_path / "skip.txt")
    assert [e.name for e in list_dir(tmp_path, PDF)] == ["keep.pdf"]


def test_list_dir_all_filter_keeps_every_file(tmp_path: Path) -> None:
    _touch(tmp_path / "a.txt")
    _touch(tmp_path / "b.bin")
    assert {e.name for e in list_dir(tmp_path, ALL)} == {"a.txt", "b.bin"}


def test_list_dir_skips_dotfiles(tmp_path: Path) -> None:
    _touch(tmp_path / ".hidden.pdf")
    _touch(tmp_path / "shown.pdf")
    assert [e.name for e in list_dir(tmp_path, PDF)] == ["shown.pdf"]


def test_list_dir_extension_match_is_case_insensitive(tmp_path: Path) -> None:
    _touch(tmp_path / "UP.PDF")
    assert [e.name for e in list_dir(tmp_path, PDF)] == ["UP.PDF"]


def test_list_dir_unreadable_returns_empty(tmp_path: Path) -> None:
    assert list_dir(tmp_path / "missing", PDF) == []


def test_list_dir_marks_directories(tmp_path: Path) -> None:
    (tmp_path / "d").mkdir()
    _touch(tmp_path / "f.pdf")
    assert {e.name: e.is_dir for e in list_dir(tmp_path, PDF)} == {"d": True, "f.pdf": False}


def test_parent_of_goes_up(tmp_path: Path) -> None:
    child = tmp_path / "sub"
    child.mkdir()
    assert parent_of(child) == tmp_path


def test_parent_of_clamps_at_root() -> None:
    root = Path(Path.cwd().anchor)
    assert parent_of(root) == root


def test_substring_filter_is_case_insensitive() -> None:
    entries = [
        FsEntry("Report.pdf", Path("Report.pdf"), False),
        FsEntry("notes.txt", Path("notes.txt"), False),
    ]
    assert [e.name for e in substring_filter(entries, "REP")] == ["Report.pdf"]


def test_substring_filter_empty_keeps_all() -> None:
    entries = [FsEntry("a", Path("a"), False)]
    assert substring_filter(entries, "") == entries


def test_is_root_true_at_anchor() -> None:
    assert is_root(Path(Path.cwd().anchor))


def test_is_root_false_for_subdir(tmp_path: Path) -> None:
    assert not is_root(tmp_path)


def test_drives_look_like_roots() -> None:
    # Empty on POSIX, ≥1 on Windows. Don't stat paths here — a listed-but-empty
    # card reader stats False yet is a real drive letter; that's why drives()
    # reads the bitmask instead of probing exists().
    listed = drives()
    assert all(entry.is_dir and entry.name.endswith(":\\") for entry in listed)
    assert all(entry.name == str(entry.path) for entry in listed)
