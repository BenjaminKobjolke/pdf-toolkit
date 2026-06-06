"""Unit tests for sidecar v2 image persistence and v1 backward compatibility."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pdf.image_spec import ImageFieldSpec, SidecarDocument
from app.pdf.sidecar import SIDECAR_VERSION, load_sidecar, save_sidecar, sidecar_path
from app.pdf.text_spec import TextFieldSpec


def _field() -> TextFieldSpec:
    return TextFieldSpec(0, 1.0, 2.0, 3.0, 4.0, "hi", "Helvetica", 18.0, "#000000", None)


def _image() -> ImageFieldSpec:
    return ImageFieldSpec(1, 5.0, 6.0, 30.0, 40.0, "assets/x.png", absolute=False, opacity=0.8)


def test_round_trips_fields_and_images(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    doc = SidecarDocument(fields=(_field(),), images=(_image(),))
    save_sidecar(pdf, doc)
    assert load_sidecar(pdf) == doc


def test_writes_current_version(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    save_sidecar(pdf, SidecarDocument(images=(_image(),)))
    raw = json.loads(sidecar_path(pdf).read_text(encoding="utf-8"))
    assert raw["version"] == SIDECAR_VERSION == 2


def test_v1_sidecar_loads_with_no_images(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    sidecar_path(pdf).write_text(
        json.dumps(
            {
                "version": 1,
                "fields": [
                    {
                        "page_index": 0,
                        "x": 1.0,
                        "y": 2.0,
                        "width": 3.0,
                        "height": 4.0,
                        "text": "hi",
                        "font_family": "Helvetica",
                        "font_size": 18.0,
                        "color": "#000000",
                        "bg_color": None,
                        "bold": False,
                        "italic": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    doc = load_sidecar(pdf)
    assert len(doc.fields) == 1
    assert doc.images == ()


def test_malformed_image_raises(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    sidecar_path(pdf).write_text(
        json.dumps({"version": 2, "fields": [], "images": [{"page_index": 0}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_sidecar(pdf)
