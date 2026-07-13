"""Unit tests for the text/markdown -> HTML builder."""

from __future__ import annotations

from app.config.text_view_settings import TextViewSettings
from app.pdf.text_html import DARK_BG, LIGHT_BG, render_html


def test_markdown_heading_becomes_h2() -> None:
    html = render_html("## Hello", is_markdown=True, settings=TextViewSettings())
    assert "<h2>" in html
    assert "Hello" in html
    assert "##" not in html  # raw markdown must not survive


def test_markdown_bold_and_list() -> None:
    html = render_html("**b**\n\n- a\n- b\n", is_markdown=True, settings=TextViewSettings())
    assert "<strong>b</strong>" in html
    assert "<li>a</li>" in html


def test_plain_text_wraps_in_pre_and_escapes() -> None:
    html = render_html("a < b & <script>", is_markdown=False, settings=TextViewSettings())
    assert "<pre" in html
    assert "&lt;script&gt;" in html
    assert "a &lt; b &amp; " in html


def test_font_size_embedded() -> None:
    html = render_html("x", is_markdown=False, settings=TextViewSettings(font_pt=27))
    assert "27pt" in html


def test_dark_mode_uses_dark_background() -> None:
    dark = render_html("x", is_markdown=True, settings=TextViewSettings(dark_mode=True))
    light = render_html("x", is_markdown=True, settings=TextViewSettings(dark_mode=False))
    assert DARK_BG in dark
    assert LIGHT_BG in light
    assert DARK_BG not in light
