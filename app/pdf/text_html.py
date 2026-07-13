"""Build a styled HTML document from plain-text or Markdown source.

fitz can render HTML (via its ebook engine) but has no Markdown reader, so text
formats are turned into HTML here and opened with ``filetype="html"`` (see
:func:`app.pdf.file_format.open_fitz`). One CSS ``<style>`` block owns all three
tunable concerns — font size, the light/dark theme, and heading/markdown styling
— derived from :class:`~app.config.text_view_settings.TextViewSettings`.

Pure and fitz-free (takes an ``is_markdown`` bool, not a ``FileFormat``) so it
stays unit-testable and avoids an import cycle with ``file_format``.
"""

from __future__ import annotations

from html import escape

import markdown

from app.config.text_view_settings import TextViewSettings

# Reading themes: (foreground, background, link). Two constants own the colors.
LIGHT_FG, LIGHT_BG, LIGHT_LINK = "#000000", "#ffffff", "#0645ad"
DARK_FG, DARK_BG, DARK_LINK = "#dddddd", "#1e1e1e", "#6cb6ff"

_MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists"]


def render_html(text: str, *, is_markdown: bool, settings: TextViewSettings) -> str:
    """Return a full HTML document for ``text`` styled per ``settings``."""
    body = (
        markdown.markdown(text, extensions=_MD_EXTENSIONS)
        if is_markdown
        else f"<pre>{escape(text)}</pre>"
    )
    fg, bg, link = (
        (DARK_FG, DARK_BG, DARK_LINK)
        if settings.dark_mode
        else (
            LIGHT_FG,
            LIGHT_BG,
            LIGHT_LINK,
        )
    )
    style = (
        f"body{{font-size:{settings.font_pt}pt;color:{fg};background:{bg};"
        "font-family:sans-serif;line-height:1.4;margin:8px}"
        "pre{white-space:pre-wrap;word-wrap:break-word;font-family:monospace}"
        f"code,pre{{background:{_code_bg(settings.dark_mode)}}}"
        f"a{{color:{link}}}"
    )
    return f"<html><head><style>{style}</style></head><body>{body}</body></html>"


def _code_bg(dark_mode: bool) -> str:
    """Subtle fill behind inline/blocked code, tuned per theme."""
    return "#2b2b2b" if dark_mode else "#f0f0f0"
