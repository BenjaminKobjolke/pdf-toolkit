"""Unit tests for app.pdf.backup."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.pdf.backup import create_backup
from tests.conftest import MakePdf


def test_creates_backup_with_timestamp_prefix(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)], name="hello.pdf")
    backup_dir = tmp_path / "backup"

    backup_path = create_backup(source, backup_dir)

    assert backup_path.parent == backup_dir
    assert re.fullmatch(r"\d{8}-\d{4}-hello\.pdf", backup_path.name), backup_path.name


def test_creates_backup_dir_if_missing(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 200)])
    backup_dir = tmp_path / "does" / "not" / "exist"
    assert not backup_dir.exists()

    backup_path = create_backup(source, backup_dir)

    assert backup_dir.is_dir()
    assert backup_path.is_file()


def test_backup_is_byte_identical_to_source(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(50, 75), (200, 300)])
    backup_dir = tmp_path / "backup"

    backup_path = create_backup(source, backup_dir)

    assert backup_path.read_bytes() == source.read_bytes()


def test_timestamp_is_current_minute(tmp_path: Path, make_pdf: MakePdf) -> None:
    source = make_pdf([(100, 100)], name="x.pdf")
    backup_dir = tmp_path / "backup"

    before = datetime.now().replace(second=0, microsecond=0)
    backup_path = create_backup(source, backup_dir)
    after = datetime.now().replace(second=0, microsecond=0)

    stamp = backup_path.name.split("-x.pdf")[0]
    parsed = datetime.strptime(stamp, "%Y%m%d-%H%M")
    assert before <= parsed <= after
