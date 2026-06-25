"""Unit tests for the JSON sidecar load/save boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pdf.image_spec import SidecarDocument
from app.pdf.rect_spec import RectFieldSpec
from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_spec import TextFieldSpec


def _field(**overrides: object) -> TextFieldSpec:
    base: dict[str, object] = {
        "page_index": 0,
        "x": 120.0,
        "y": 80.0,
        "width": 200.0,
        "height": 24.0,
        "text": "Hello",
        "font_family": "Arial",
        "font_size": 18.0,
        "color": "#ff0000",
        "bg_color": None,
        "bold": False,
        "italic": False,
    }
    base.update(overrides)
    return TextFieldSpec(**base)  # type: ignore[arg-type]


def test_sidecar_path_swaps_extension(tmp_path: Path) -> None:
    assert sidecar_path(tmp_path / "document.pdf") == tmp_path / "document.json"


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    doc = SidecarDocument(fields=(_field(), _field(page_index=1, bg_color="#ffff00", bold=True)))
    save_sidecar(pdf, doc)
    assert load_sidecar(pdf) == doc


def test_load_absent_returns_empty(tmp_path: Path) -> None:
    assert load_sidecar(tmp_path / "missing.pdf") == SidecarDocument(fields=())


def test_save_empty_then_load_returns_empty(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    save_sidecar(pdf, SidecarDocument(fields=()))
    assert sidecar_path(pdf).is_file()
    assert load_sidecar(pdf) == SidecarDocument(fields=())


def test_save_leaves_no_tmp_file(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    save_sidecar(pdf, SidecarDocument(fields=(_field(),)))
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_load_malformed_json_raises(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    sidecar_path(pdf).write_text("{ not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_sidecar(pdf)


def test_load_unknown_version_raises(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    sidecar_path(pdf).write_text(json.dumps({"version": 999, "fields": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_sidecar(pdf)


def test_load_missing_key_raises(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    payload = {"version": 1, "fields": [{"x": 1.0}]}
    sidecar_path(pdf).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_sidecar(pdf)


def test_load_wrong_type_raises(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    bad = _spec_dict()
    bad["page_index"] = "zero"
    sidecar_path(pdf).write_text(json.dumps({"version": 1, "fields": [bad]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_sidecar(pdf)


def test_z_round_trips(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    doc = SidecarDocument(fields=(_field(z=3.0), _field(page_index=1, z=7.0)))
    save_sidecar(pdf, doc)
    assert load_sidecar(pdf) == doc


def test_rects_round_trip(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    rect = RectFieldSpec(
        page_index=0, x=10.0, y=20.0, width=30.0, height=40.0, color="#00ff00", z=1.0
    )
    doc = SidecarDocument(rects=(rect,))
    save_sidecar(pdf, doc)
    assert load_sidecar(pdf) == doc


def test_v2_migration_assigns_z_with_images_above_fields(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    payload = {
        "version": 2,
        "fields": [_spec_dict(), _spec_dict()],
        "images": [_image_dict()],
    }
    sidecar_path(pdf).write_text(json.dumps(payload), encoding="utf-8")
    doc = load_sidecar(pdf)
    field_zs = [f.z for f in doc.fields]
    image_zs = [i.z for i in doc.images]
    assert field_zs == [0.0, 1.0]
    assert image_zs == [2.0]
    assert max(field_zs) < min(image_zs)


def _image_dict() -> dict[str, object]:
    return {
        "page_index": 0,
        "x": 1.0,
        "y": 2.0,
        "width": 3.0,
        "height": 4.0,
        "path": "assets/a.png",
        "absolute": False,
        "opacity": 1.0,
    }


def _spec_dict() -> dict[str, object]:
    return {
        "page_index": 0,
        "x": 1.0,
        "y": 2.0,
        "width": 3.0,
        "height": 4.0,
        "text": "x",
        "font_family": "Arial",
        "font_size": 12.0,
        "color": "#000000",
        "bg_color": None,
        "bold": False,
        "italic": False,
    }
