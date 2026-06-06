"""Load and save the per-PDF JSON sidecar holding placed text fields and images.

The sidecar lives next to the PDF as ``<stem>.json``. Only the typed
:class:`SidecarDocument` crosses this module's boundary; raw dicts stay private.
Writes are atomic (tmp + ``os.replace``), matching the core PDF ops.

Version history: v1 held only ``fields``; v2 adds ``images``. v1 files still load
(with no images) and are silently upgraded to v2 on the next save.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.io.json_store import write_json_atomic
from app.pdf.image_spec import ImageFieldSpec, SidecarDocument
from app.pdf.text_spec import TextFieldSpec

SIDECAR_SUFFIX = ".json"
SIDECAR_VERSION = 2
_SUPPORTED_VERSIONS = (1, 2)


def sidecar_path(pdf: Path) -> Path:
    """Return the sidecar path for ``pdf`` (``document.pdf`` -> ``document.json``)."""
    return pdf.with_suffix(SIDECAR_SUFFIX)


def load_sidecar(pdf: Path) -> SidecarDocument:
    """Load the sidecar for ``pdf``.

    Returns an empty :class:`SidecarDocument` when the file is absent or holds no
    content. Raises ``ValueError`` if the file is present but malformed. v1 files
    load with an empty image list.
    """
    path = sidecar_path(pdf)
    if not path.is_file():
        return SidecarDocument(fields=(), images=())

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"could not read sidecar {path}: {err}") from err

    if not isinstance(raw, dict):
        raise ValueError(f"sidecar {path} must contain a JSON object")
    if raw.get("version") not in _SUPPORTED_VERSIONS:
        raise ValueError(f"unsupported sidecar version in {path}: {raw.get('version')!r}")

    fields_raw = raw.get("fields", [])
    if not isinstance(fields_raw, list):
        raise ValueError(f"sidecar {path} 'fields' must be a list")
    images_raw = raw.get("images", [])
    if not isinstance(images_raw, list):
        raise ValueError(f"sidecar {path} 'images' must be a list")

    return SidecarDocument(
        fields=tuple(_field_from_dict(item) for item in fields_raw),
        images=tuple(_image_from_dict(item) for item in images_raw),
    )


def save_sidecar(pdf: Path, doc: SidecarDocument) -> None:
    """Write ``doc`` to ``pdf``'s sidecar atomically (always as the current version)."""
    payload = {
        "version": SIDECAR_VERSION,
        "fields": [_field_to_dict(field) for field in doc.fields],
        "images": [_image_to_dict(image) for image in doc.images],
    }
    write_json_atomic(sidecar_path(pdf), payload)


def _field_to_dict(field: TextFieldSpec) -> dict[str, Any]:
    return {
        "page_index": field.page_index,
        "x": field.x,
        "y": field.y,
        "width": field.width,
        "height": field.height,
        "text": field.text,
        "font_family": field.font_family,
        "font_size": field.font_size,
        "color": field.color,
        "bg_color": field.bg_color,
        "bold": field.bold,
        "italic": field.italic,
    }


def _field_from_dict(item: Any) -> TextFieldSpec:
    if not isinstance(item, dict):
        raise ValueError(f"text field must be a JSON object, got {type(item).__name__}")
    try:
        return TextFieldSpec(
            page_index=_as_int(item, "page_index"),
            x=_as_float(item, "x"),
            y=_as_float(item, "y"),
            width=_as_float(item, "width"),
            height=_as_float(item, "height"),
            text=_as_str(item, "text"),
            font_family=_as_str(item, "font_family"),
            font_size=_as_float(item, "font_size"),
            color=_as_str(item, "color"),
            bg_color=_as_opt_str(item, "bg_color"),
            bold=_as_bool(item, "bold"),
            italic=_as_bool(item, "italic"),
        )
    except KeyError as err:
        raise ValueError(f"text field missing key: {err}") from err


def _image_to_dict(image: ImageFieldSpec) -> dict[str, Any]:
    return {
        "page_index": image.page_index,
        "x": image.x,
        "y": image.y,
        "width": image.width,
        "height": image.height,
        "path": image.path,
        "absolute": image.absolute,
        "opacity": image.opacity,
    }


def _image_from_dict(item: Any) -> ImageFieldSpec:
    if not isinstance(item, dict):
        raise ValueError(f"image must be a JSON object, got {type(item).__name__}")
    try:
        return ImageFieldSpec(
            page_index=_as_int(item, "page_index"),
            x=_as_float(item, "x"),
            y=_as_float(item, "y"),
            width=_as_float(item, "width"),
            height=_as_float(item, "height"),
            path=_as_str(item, "path"),
            absolute=_as_bool(item, "absolute"),
            opacity=_as_float_default(item, "opacity", 1.0),
        )
    except KeyError as err:
        raise ValueError(f"image missing key: {err}") from err


def _require(item: dict[str, Any], key: str) -> Any:
    if key not in item:
        raise KeyError(key)
    return item[key]


def _as_int(item: dict[str, Any], key: str) -> int:
    value = _require(item, key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an int, got {value!r}")
    return int(value)


def _as_float(item: dict[str, Any], key: str) -> float:
    value = _require(item, key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number, got {value!r}")
    return float(value)


def _as_float_default(item: dict[str, Any], key: str, default: float) -> float:
    if key not in item:
        return default
    return _as_float(item, key)


def _as_str(item: dict[str, Any], key: str) -> str:
    value = _require(item, key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string, got {value!r}")
    return value


def _as_opt_str(item: dict[str, Any], key: str) -> str | None:
    value = _require(item, key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null, got {value!r}")
    return value


def _as_bool(item: dict[str, Any], key: str) -> bool:
    value = _require(item, key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a bool, got {value!r}")
    return value
