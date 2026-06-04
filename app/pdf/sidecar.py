"""Load and save the per-PDF JSON sidecar holding placed text fields.

The sidecar lives next to the PDF as ``<stem>.json``. Only typed
:class:`TextDocumentSpec` objects cross this module's boundary; raw dicts stay
private. Writes are atomic (tmp + ``os.replace``), matching the core PDF ops.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.io.json_store import write_json_atomic
from app.pdf.text_spec import TextDocumentSpec, TextFieldSpec

SIDECAR_SUFFIX = ".json"
SIDECAR_VERSION = 1


def sidecar_path(pdf: Path) -> Path:
    """Return the sidecar path for ``pdf`` (``document.pdf`` -> ``document.json``)."""
    return pdf.with_suffix(SIDECAR_SUFFIX)


def load_sidecar(pdf: Path) -> TextDocumentSpec:
    """Load the sidecar for ``pdf``.

    Returns an empty :class:`TextDocumentSpec` when the file is absent or holds
    no fields. Raises ``ValueError`` if the file is present but malformed.
    """
    path = sidecar_path(pdf)
    if not path.is_file():
        return TextDocumentSpec(fields=())

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"could not read sidecar {path}: {err}") from err

    if not isinstance(raw, dict):
        raise ValueError(f"sidecar {path} must contain a JSON object")
    if raw.get("version") != SIDECAR_VERSION:
        raise ValueError(f"unsupported sidecar version in {path}: {raw.get('version')!r}")

    fields_raw = raw.get("fields", [])
    if not isinstance(fields_raw, list):
        raise ValueError(f"sidecar {path} 'fields' must be a list")

    return TextDocumentSpec(fields=tuple(_field_from_dict(item) for item in fields_raw))


def save_sidecar(pdf: Path, doc: TextDocumentSpec) -> None:
    """Write ``doc`` to ``pdf``'s sidecar atomically."""
    payload = {
        "version": SIDECAR_VERSION,
        "fields": [_field_to_dict(field) for field in doc.fields],
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
