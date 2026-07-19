"""Resolve a font family + style to an embeddable font file for fitz.

Qt exposes no API returning a font's file path, so on Windows we read the
installed-fonts registry (display names already carry family + style) and map
each entry to its file under ``%WINDIR%\\Fonts``. When nothing matches — or a
bold/italic variant has no dedicated file (fitz won't synthesise styles on an
embedded font) — we fall back to a guaranteed Base14 builtin.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.app_logger import log

# Reserved PyMuPDF Base14 font codes (need no embedded file).
BASE14_REGULAR = "helv"
BASE14_BOLD = "hebo"
BASE14_ITALIC = "heit"
BASE14_BOLD_ITALIC = "hebi"

_FONT_EXTENSIONS = (".ttf", ".otf", ".ttc")
_STYLE_WORDS = ("bold", "italic", "oblique")
_REGISTRY_SUFFIX = re.compile(r"\s*\((truetype|opentype)\)\s*$", re.IGNORECASE)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class FontRequest:
    """A requested font: a family name plus style flags."""

    family: str
    bold: bool
    italic: bool


@dataclass(frozen=True)
class ResolvedFont:
    """A font ready for fitz: an embed alias and the file, or a Base14 builtin."""

    fontname: str
    fontfile: Path | None  # None => fontname is a Base14 builtin


def resolve_font(req: FontRequest) -> ResolvedFont:
    """Resolve ``req`` to a font file, falling back to Base14. Never raises."""
    try:
        index = _font_index()
        path = index.get((req.family.lower(), req.bold, req.italic))
    except OSError as err:
        log.warning("font index unavailable, using builtin: %s", err)
        path = None

    if path is not None and path.is_file():
        return ResolvedFont(fontname=_alias(req), fontfile=path)
    return ResolvedFont(fontname=_builtin_for(req.bold, req.italic), fontfile=None)


def _builtin_for(bold: bool, italic: bool) -> str:
    if bold and italic:
        return BASE14_BOLD_ITALIC
    if bold:
        return BASE14_BOLD
    if italic:
        return BASE14_ITALIC
    return BASE14_REGULAR


def _alias(req: FontRequest) -> str:
    base = _NON_ALNUM.sub("", req.family.lower()) or "font"
    return f"{base}{'b' if req.bold else ''}{'i' if req.italic else ''}"


@lru_cache(maxsize=1)
def _font_index() -> dict[tuple[str, bool, bool], Path]:
    """Build a ``(family_lower, bold, italic) -> Path`` map of installed fonts."""
    index: dict[tuple[str, bool, bool], Path] = {}
    for display_name, file_value in _registry_entries():
        path = _resolve_file(file_value)
        if path is None:
            continue
        family, bold, italic = _parse_display_name(display_name)
        if not family:
            continue
        index.setdefault((family.lower(), bold, italic), path)
    return index


def _registry_entries() -> list[tuple[str, str]]:
    """Return (display_name, file) pairs from the Windows fonts registry."""
    try:
        import winreg
    except ImportError:
        return []  # Non-Windows: rely on Base14 fallback.

    entries: list[tuple[str, str]] = []
    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, key_path) as key:
                count = winreg.QueryInfoKey(key)[1]
                for i in range(count):
                    name, value, _ = winreg.EnumValue(key, i)
                    if isinstance(value, str):
                        entries.append((name, value))
        except OSError:
            continue
    return entries


def _resolve_file(file_value: str) -> Path | None:
    candidate = Path(file_value)
    if candidate.suffix.lower() not in _FONT_EXTENSIONS:
        return None
    if candidate.is_absolute() and candidate.is_file():
        return candidate
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    in_fonts = fonts_dir / candidate.name
    return in_fonts if in_fonts.is_file() else None


def _parse_display_name(display_name: str) -> tuple[str, bool, bool]:
    """Split ``'Arial Bold (TrueType)'`` into ``('Arial', True, False)``."""
    name = _REGISTRY_SUFFIX.sub("", display_name)
    lowered = name.lower()
    bold = "bold" in lowered
    italic = "italic" in lowered or "oblique" in lowered
    tokens = [tok for tok in name.split() if tok.lower() not in _STYLE_WORDS]
    return " ".join(tokens).strip(), bold, italic
