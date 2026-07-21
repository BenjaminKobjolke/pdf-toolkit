"""Unit tests for the pure file-browser filesystem logic (no Qt)."""

from __future__ import annotations

from pathlib import Path

from app.gui.file_browser_model import (
    FileFilter,
    FsEntry,
    drives,
    first_openable_file,
    is_root,
    list_dir,
    nearest_file,
    openable_files,
    parent_of,
    sibling_file,
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


def test_first_openable_file_alphabetical_first(tmp_path: Path) -> None:
    _touch(tmp_path / "b.pdf")
    _touch(tmp_path / "a.pdf")
    assert first_openable_file(tmp_path, PDF) == tmp_path / "a.pdf"


def test_first_openable_file_skips_directories(tmp_path: Path) -> None:
    (tmp_path / "aaa").mkdir()
    _touch(tmp_path / "z.pdf")
    assert first_openable_file(tmp_path, PDF) == tmp_path / "z.pdf"


def test_first_openable_file_skips_unrenderable_files(tmp_path: Path) -> None:
    # A binary under the all-files filter is listed but not openable.
    (tmp_path / "a.bin").write_bytes(b"\x00\x01")
    _touch(tmp_path / "b.txt")
    assert first_openable_file(tmp_path, ALL) == tmp_path / "b.txt"


def test_first_openable_file_none_when_empty(tmp_path: Path) -> None:
    assert first_openable_file(tmp_path, ALL) is None


def test_first_openable_file_none_when_only_unopenable(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"\x00\x01")
    assert first_openable_file(tmp_path, ALL) is None


def test_openable_files_sorted_files_only(tmp_path: Path) -> None:
    (tmp_path / "aaa").mkdir()
    _touch(tmp_path / "b.pdf")
    _touch(tmp_path / "a.pdf")
    assert openable_files(tmp_path, PDF) == [tmp_path / "a.pdf", tmp_path / "b.pdf"]


def test_openable_files_skips_unrenderable_and_honors_filter(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"\x00\x01")
    _touch(tmp_path / "b.txt")
    _touch(tmp_path / "c.pdf")
    assert openable_files(tmp_path, ALL) == [tmp_path / "b.txt", tmp_path / "c.pdf"]
    assert openable_files(tmp_path, PDF) == [tmp_path / "c.pdf"]


def test_openable_files_empty_dir(tmp_path: Path) -> None:
    assert openable_files(tmp_path, ALL) == []


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


def test_sibling_file_next_is_alphabetical(tmp_path: Path) -> None:
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.pdf")
    _touch(tmp_path / "c.pdf")
    assert sibling_file(tmp_path / "a.pdf", PDF, 1) == tmp_path / "b.pdf"


def test_sibling_file_previous_steps_back(tmp_path: Path) -> None:
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.pdf")
    assert sibling_file(tmp_path / "b.pdf", PDF, -1) == tmp_path / "a.pdf"


def test_sibling_file_wraps_at_both_ends(tmp_path: Path) -> None:
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.pdf")
    assert sibling_file(tmp_path / "b.pdf", PDF, 1) == tmp_path / "a.pdf"
    assert sibling_file(tmp_path / "a.pdf", PDF, -1) == tmp_path / "b.pdf"


def test_sibling_file_respects_filter(tmp_path: Path) -> None:
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.txt")
    _touch(tmp_path / "c.pdf")
    assert sibling_file(tmp_path / "a.pdf", PDF, 1) == tmp_path / "c.pdf"


def test_sibling_file_skips_unopenable_binary(tmp_path: Path) -> None:
    _touch(tmp_path / "a.txt")
    (tmp_path / "b.bin").write_bytes(b"\x00\x01\x02binary")
    _touch(tmp_path / "c.txt")
    assert sibling_file(tmp_path / "a.txt", ALL, 1) == tmp_path / "c.txt"


def test_sibling_file_anchors_current_outside_filter(tmp_path: Path) -> None:
    # A sniff-opened file (e.g. .ini) may not pass the open-dialog filter; stepping
    # still starts from its alphabetical position.
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.ini")
    _touch(tmp_path / "c.pdf")
    assert sibling_file(tmp_path / "b.ini", PDF, 1) == tmp_path / "c.pdf"
    assert sibling_file(tmp_path / "b.ini", PDF, -1) == tmp_path / "a.pdf"


def test_sibling_file_solo_file_returns_none(tmp_path: Path) -> None:
    _touch(tmp_path / "only.pdf")
    assert sibling_file(tmp_path / "only.pdf", PDF, 1) is None


def test_sibling_file_never_returns_current(tmp_path: Path) -> None:
    _touch(tmp_path / "a.txt")
    (tmp_path / "b.bin").write_bytes(b"\x00\x01")
    assert sibling_file(tmp_path / "a.txt", ALL, 1) is None


def test_sibling_file_missing_dir_returns_none(tmp_path: Path) -> None:
    assert sibling_file(tmp_path / "gone" / "x.pdf", PDF, 1) is None


def test_nearest_file_of_deleted_returns_successor(tmp_path: Path) -> None:
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "c.pdf")
    assert nearest_file(tmp_path / "b.pdf", PDF) == tmp_path / "c.pdf"


def test_nearest_file_of_deleted_last_returns_predecessor(tmp_path: Path) -> None:
    # No wrap: deleting the last file lands on the new last file, not the first.
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.pdf")
    assert nearest_file(tmp_path / "c.pdf", PDF) == tmp_path / "b.pdf"


def test_nearest_file_never_returns_the_file_itself(tmp_path: Path) -> None:
    # Callable before the deletion has happened on disk.
    _touch(tmp_path / "a.pdf")
    _touch(tmp_path / "b.pdf")
    assert nearest_file(tmp_path / "a.pdf", PDF) == tmp_path / "b.pdf"


def test_nearest_file_empty_dir_returns_none(tmp_path: Path) -> None:
    assert nearest_file(tmp_path / "x.pdf", PDF) is None


def test_drives_look_like_roots() -> None:
    # Empty on POSIX, ≥1 on Windows. Don't stat paths here — a listed-but-empty
    # card reader stats False yet is a real drive letter; that's why drives()
    # reads the bitmask instead of probing exists().
    listed = drives()
    assert all(entry.is_dir and entry.name.endswith(":\\") for entry in listed)
    assert all(entry.name == str(entry.path) for entry in listed)
