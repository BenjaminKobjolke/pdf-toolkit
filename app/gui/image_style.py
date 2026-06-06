"""The Qt <-> spec mapping for placed images.

Keeps ``QPixmap`` loading and path resolution out of both the pure DTOs
(``image_spec``) and the controller, mirroring ``text_style`` for text fields.
The on-page size in the spec is the scaled pixmap size, so the scale factor is
recovered on load as ``spec.width / native_width``.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap

from app.gui.image_item import ImageItem
from app.pdf.image_assets import resolve_image_path
from app.pdf.image_spec import ImageFieldSpec


def item_to_spec(item: ImageItem, page_index: int) -> ImageFieldSpec:
    return ImageFieldSpec(
        page_index=page_index,
        x=item.pos().x(),
        y=item.pos().y(),
        width=item.current_width(),
        height=item.current_height(),
        path=item.path_str(),
        absolute=item.is_absolute(),
        opacity=item.opacity_value(),
    )


def spec_to_item(spec: ImageFieldSpec, base_dir: Path) -> ImageItem:
    resolved = resolve_image_path(spec.path, spec.absolute, base_dir)
    pixmap = QPixmap(str(resolved))
    factor = spec.width / pixmap.width() if pixmap.width() else 1.0
    item = build_item(resolved, spec.path, spec.absolute, spec.opacity, factor)
    item.setPos(spec.x, spec.y)
    return item


def build_item(
    load_from: Path,
    path_str: str,
    absolute: bool,
    opacity: float = 1.0,
    scale_factor: float = 1.0,
) -> ImageItem:
    """Create an :class:`ImageItem` from the pixmap at ``load_from``."""
    pixmap = QPixmap(str(load_from))
    return ImageItem(pixmap, path_str, absolute, opacity, scale_factor)
