"""Unit tests for the JSON sidecar load/save boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pdf.sidecar import load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec


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
    doc = TextDocumentSpec(fields=(_field(), _field(page_index=1, bg_color="#ffff00", bold=True)))
    save_sidecar(pdf, doc)
    assert load_sidecar(pdf) == doc


def test_load_absent_returns_empty(tmp_path: Path) -> None:
    assert load_sidecar(tmp_path / "missing.pdf") == TextDocumentSpec(fields=())


def test_save_empty_then_load_returns_empty(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    save_sidecar(pdf, TextDocumentSpec(fields=()))
    assert sidecar_path(pdf).is_file()
    assert load_sidecar(pdf) == TextDocumentSpec(fields=())


def test_save_leaves_no_tmp_file(tmp_path: Path) -> None:
    pdf = tmp_path / "document.pdf"
    save_sidecar(pdf, TextDocumentSpec(fields=(_field(),)))
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
