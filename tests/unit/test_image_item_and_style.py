"""Unit tests for ImageItem scaling and the image_style bridge (offscreen Qt)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsItem

from app.gui import image_style
from app.gui.image_item import ImageItem
from app.pdf.image_spec import ImageFieldSpec
from tests.conftest import MakeImage


def test_scale_updates_on_page_size(qapp: object, make_image: MakeImage) -> None:
    img = make_image("png", size=(20, 10))
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    item.set_scale_factor(3.0)
    assert item.current_width() == 60
    assert item.current_height() == 30


def test_scale_about_center_keeps_center(qapp: object, make_image: MakeImage) -> None:
    img = make_image("png", size=(20, 10))
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    item.setPos(100, 100)  # 20x10 -> center (110, 105)
    item.scale_about_center(2.0)  # 40x20 -> top-left should move to (90, 95)
    assert (item.pos().x(), item.pos().y()) == (90, 95)
    cx = item.pos().x() + item.current_width() / 2
    cy = item.pos().y() + item.current_height() / 2
    assert (cx, cy) == (110, 105)


def test_set_editable_toggles_flags(qapp: object, make_image: MakeImage) -> None:
    img = make_image("png")
    item = ImageItem(QPixmap(str(img)), "x.png", absolute=True)
    item.set_editable(True)
    assert item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    item.setSelected(True)
    item.set_editable(False)
    assert not item.isSelected()


def test_item_spec_round_trip(qapp: object, make_image: MakeImage, tmp_path: Path) -> None:
    img = make_image("png", size=(20, 10))
    item = image_style.build_item(img, "assets/x.png", absolute=False)
    item.set_scale_factor(2.0)
    item.setPos(5, 6)
    spec = image_style.item_to_spec(item, 3)
    assert spec.page_index == 3
    assert spec.path == "assets/x.png"
    assert spec.absolute is False
    assert (spec.x, spec.y) == (5, 6)
    assert (spec.width, spec.height) == (40, 20)


def test_spec_to_item_recovers_scale(qapp: object, make_image: MakeImage, tmp_path: Path) -> None:
    img = make_image("png", size=(20, 10))
    spec = ImageFieldSpec(0, 1.0, 2.0, 40.0, 20.0, str(img), absolute=True)
    item = image_style.spec_to_item(spec, tmp_path)
    assert round(item.scale_factor(), 3) == 2.0
