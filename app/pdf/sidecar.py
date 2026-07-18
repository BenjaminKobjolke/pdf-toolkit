"""Load and save the per-PDF JSON sidecar holding placed text fields and images.

The sidecar lives next to the PDF as ``<stem>.json``. Only the typed
:class:`SidecarDocument` crosses this module's boundary; raw dicts stay private.
Writes are atomic (tmp + ``os.replace``), matching the core PDF ops.

Version history: v1 held only ``fields``; v2 adds ``images``; v3 adds ``rects``
and a per-element ``z`` stacking order. Older files still load and are silently
upgraded on the next save. Pre-v3 files have no ``z``, so one is assigned on load
that preserves the old fixed stacking (all fields below all images below rects).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import MISSING, asdict, fields, replace
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

from app.io.json_store import write_json_atomic
from app.pdf.image_spec import ImageFieldSpec, SidecarDocument
from app.pdf.rect_spec import RectFieldSpec
from app.pdf.text_spec import TextFieldSpec

SIDECAR_SUFFIX = ".json"
SIDECAR_VERSION = 3
_SUPPORTED_VERSIONS = (1, 2, 3)
_FIRST_Z_VERSION = 3


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

    version = raw.get("version")
    fields_raw = raw.get("fields", [])
    if not isinstance(fields_raw, list):
        raise ValueError(f"sidecar {path} 'fields' must be a list")
    images_raw = raw.get("images", [])
    if not isinstance(images_raw, list):
        raise ValueError(f"sidecar {path} 'images' must be a list")
    rects_raw = raw.get("rects", [])
    if not isinstance(rects_raw, list):
        raise ValueError(f"sidecar {path} 'rects' must be a list")

    fields = tuple(_spec_from_dict(TextFieldSpec, item, "text field") for item in fields_raw)
    images = tuple(_spec_from_dict(ImageFieldSpec, item, "image") for item in images_raw)
    rects = tuple(_spec_from_dict(RectFieldSpec, item, "rect") for item in rects_raw)
    if version is not None and version < _FIRST_Z_VERSION:
        fields, images, rects = _assign_legacy_z(fields, images, rects)
    return SidecarDocument(fields=fields, images=images, rects=rects)


def _assign_legacy_z(
    fields: tuple[TextFieldSpec, ...],
    images: tuple[ImageFieldSpec, ...],
    rects: tuple[RectFieldSpec, ...],
) -> tuple[tuple[TextFieldSpec, ...], tuple[ImageFieldSpec, ...], tuple[RectFieldSpec, ...]]:
    """Stamp a stacking order onto pre-v3 content (no ``z``).

    Old files drew all fields, then all images on top (rects did not exist). One
    rising counter across fields -> images -> rects reproduces that order; cross-
    page values are irrelevant since export filters by page.
    """
    counter = 0
    new_fields = []
    for field in fields:
        new_fields.append(replace(field, z=float(counter)))
        counter += 1
    new_images = []
    for image in images:
        new_images.append(replace(image, z=float(counter)))
        counter += 1
    new_rects = []
    for rect in rects:
        new_rects.append(replace(rect, z=float(counter)))
        counter += 1
    return tuple(new_fields), tuple(new_images), tuple(new_rects)


def save_sidecar(pdf: Path, doc: SidecarDocument) -> None:
    """Write ``doc`` to ``pdf``'s sidecar atomically (always as the current version)."""
    payload = {
        "version": SIDECAR_VERSION,
        "fields": [asdict(field) for field in doc.fields],
        "images": [asdict(image) for image in doc.images],
        "rects": [asdict(rect) for rect in doc.rects],
    }
    write_json_atomic(sidecar_path(pdf), payload)


_SpecT = TypeVar("_SpecT", TextFieldSpec, ImageFieldSpec, RectFieldSpec)

# Resolved once — get_type_hints re-evaluates string annotations on every call.
_SPEC_HINTS: dict[type, dict[str, Any]] = {
    cls: get_type_hints(cls) for cls in (TextFieldSpec, ImageFieldSpec, RectFieldSpec)
}


def _coercer_for(hint: Any) -> Callable[[dict[str, Any], str], Any]:
    if hint is bool:
        return _as_bool
    if hint is int:
        return _as_int
    if hint is float:
        return _as_float
    if hint is str:
        return _as_str
    if hint == (str | None):
        return _as_opt_str
    raise TypeError(f"unsupported spec field type: {hint!r}")


def _spec_from_dict(cls: type[_SpecT], item: Any, label: str) -> _SpecT:
    """Build ``cls`` from a raw sidecar entry.

    The dataclass is the contract: a field without a default is required, and
    every present value is validated against the field's annotated type.
    """
    if not isinstance(item, dict):
        raise ValueError(f"{label} must be a JSON object, got {type(item).__name__}")
    hints = _SPEC_HINTS[cls]
    kwargs: dict[str, Any] = {}
    try:
        for field in fields(cls):
            if field.name not in item and field.default is not MISSING:
                continue
            kwargs[field.name] = _coercer_for(hints[field.name])(item, field.name)
    except KeyError as err:
        raise ValueError(f"{label} missing key: {err}") from err
    return cls(**kwargs)


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
