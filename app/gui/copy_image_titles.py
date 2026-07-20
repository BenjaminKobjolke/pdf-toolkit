"""Live pixel-size titles for the copy-page/copy-view clipboard commands.

The command registry is built once at startup, so these run lazily as
``Command.title_fn`` at palette-open time — the shown pixel size tracks the
open document, current page, and window size. Without a document (e.g. the
shortcut-config picker on the empty viewer) they fall back to the static
titles. Both families share one naming scheme: ``<base> at <pct>% (<w>×<h> px)``,
with 100% dropping the percent part.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.gui import file_strings
from app.gui.render import DEFAULT_ZOOM

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def _static_title(base: str, percent: int) -> str:
    if percent == 100:
        return base
    return file_strings.FMT_AT_PCT.format(base=base, pct=percent)


def _px_title(base: str, percent: int, w: int, h: int) -> str:
    if percent == 100:
        return file_strings.FMT_PX.format(base=base, w=w, h=h)
    return file_strings.FMT_AT_PCT_PX.format(base=base, pct=percent, w=w, h=h)


def static_page_title(percent: int) -> str:
    """Static (dimension-free) title for the page-copy command at ``percent``."""
    return _static_title(file_strings.CMD_COPY_PAGE_IMAGE, percent)


def static_view_title(percent: int) -> str:
    """Static (dimension-free) title for the view-copy command at ``percent``."""
    return _static_title(file_strings.CMD_COPY_VIEW_IMAGE, percent)


def page_image_title(window: MainWindow, percent: int) -> str:
    """Title showing the page-render output size in pixels at ``percent``.

    100% is original size: one pixel per PDF point — for image documents that
    is the image's native pixel size.
    """
    rect = window.page_view.graphics_scene().sceneRect()
    if not window.has_document() or rect.isEmpty():
        return static_page_title(percent)
    # Scene rect is points × DEFAULT_ZOOM; the render output is points × pct/100.
    scale = percent / 100 / DEFAULT_ZOOM
    return _px_title(
        file_strings.CMD_COPY_PAGE_IMAGE,
        percent,
        round(rect.width() * scale),
        round(rect.height() * scale),
    )


def view_image_title(window: MainWindow, percent: int) -> str:
    """Title showing the clipped view-grab output size in pixels at ``percent``.

    Sizes come from ``PageView.visible_page_rect`` — the same rect
    ``grab_page_area`` copies — so the title always matches the output.
    """
    rect = window.page_view.visible_page_rect()
    if not window.has_document() or rect.isEmpty():
        return static_view_title(percent)
    dpr = window.page_view.viewport().devicePixelRatioF()
    w = round(rect.width() * dpr * percent / 100)
    h = round(rect.height() * dpr * percent / 100)
    return _px_title(file_strings.CMD_COPY_VIEW_IMAGE, percent, w, h)
