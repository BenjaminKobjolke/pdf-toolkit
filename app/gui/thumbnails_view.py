"""The thumbnails grid widget: previews of every openable file in a directory.

A ``QListWidget`` in icon mode. Navigation (arrows) and the selection highlight
are native; Enter and Esc are surfaced as signals for
:class:`~app.gui.thumbnails_controller.ThumbnailsController` to act on. Previews
are rendered lazily — one file per zero-interval timer tick — through the same
:func:`app.gui.render.render_page` seam the viewer uses, so PDFs, images, and
text documents all get real first-page previews.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QKeyEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.app_logger import log
from app.gui import render
from app.gui.file_browser_model import matches_all_terms

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

# Base render resolution: previews are rasterised once with their longest side
# at this many pixels, then only rescaled as the thumbnail size changes.
# ponytail: thumbnails above 512 px show slight softness; re-render at the
# current size if that ever matters.
_BASE_PX = 512
_PLACEHOLDER_GRAY = "#D0D0D0"
# Room around the icon for the filename label under each cell.
_CELL_PAD_X, _CELL_PAD_Y = 20, 40
# The selection frame is painted into the icon pixmap itself (stylesheet item
# borders mis-render on large cells). This only suppresses Qt's own current-item
# chrome: the focus rectangle (outline) and the native selection pill
# (background + border) that would otherwise frame the whole cell and its text.
_STYLE = """
QListWidget { outline: 0; }
QListWidget::item:selected { background: transparent; border: none; color: palette(text); }
"""
_HIGHLIGHT = "#FF8000"
_STROKE_PX = 4  # constant on screen — thumbnails are shown 1:1, never scaled up


class ThumbnailsView(QListWidget):
    """Icon-mode grid of file previews with keyboard-first navigation."""

    open_requested = Signal(object)  # Path of the activated file
    dismiss_requested = Signal()
    filter_changed = Signal(str)  # the current type-to-filter query
    filter_mode_changed = Signal(bool)  # filter mode entered/left

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setWordWrap(True)
        self.setStyleSheet(_STYLE)
        self._thumb_px = 0
        self._filter_text = ""
        self._filter_mode = False
        self._pixmaps: dict[Path, QPixmap] = {}
        self._pending: list[QListWidgetItem] = []
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self._render_next)
        self.itemDoubleClicked.connect(self._activate)
        self.currentItemChanged.connect(self._on_current_changed)

    def set_thumb_size(self, px: int) -> None:
        """Set the preview edge length and rescale already-rendered previews."""
        self._thumb_px = px
        self.setIconSize(QSize(px, px))
        self.setGridSize(QSize(px + _CELL_PAD_X, px + _CELL_PAD_Y))
        for index in range(self.count()):
            self._apply_icon(self.item(index))
        self._relayout()

    def populate(self, paths: list[Path], current: Path) -> None:
        """Fill the grid with ``paths``, selecting ``current`` (or the first)."""
        self._render_timer.stop()
        self._pixmaps.clear()
        self.clear()
        for path in paths:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.addItem(item)
        selected = next((i for i in range(self.count()) if _path_of(self.item(i)) == current), 0)
        if self.count():
            self.setCurrentRow(selected)
        # Render outward from the selected file so what's on screen fills first.
        items = [self.item(i) for i in range(self.count())]
        self._pending = items[selected:] + items[:selected]
        for item in items:
            self._apply_icon(item)
        if self._pending:
            self._render_timer.start()
        self._apply_filter()

    def selected_path(self) -> Path | None:
        """Path of the highlighted thumbnail, or ``None`` with nothing selected."""
        item = self.currentItem()
        return None if item is None else _path_of(item)

    def start_filter(self) -> None:
        """Enter filter mode: typing edits the query, shortcuts are muted."""
        if not self._filter_mode:
            self._filter_mode = True
            self.filter_mode_changed.emit(True)
            self.filter_changed.emit(self._filter_text)

    def clear_filter(self) -> None:
        """Leave filter mode and drop the query, showing every file again."""
        if self._filter_text:
            self._set_filter("")
        if self._filter_mode:
            self._filter_mode = False
            self.filter_mode_changed.emit(False)

    def event(self, event: QEvent) -> bool:
        """Claim every key from the window's shortcuts while filter mode is on.

        Accepting ``ShortcutOverride`` makes Qt deliver the key to
        ``keyPressEvent`` instead of any bound ``QShortcut`` — user bindings
        (including bare letters) must not steal typed filter characters.
        """
        if event.type() == QEvent.Type.ShortcutOverride and self._filter_mode:
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Enter opens, Esc leaves (filter mode first, then the grid)."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._activate(self.currentItem())
            return
        if self._filter_mode and self._handle_filter_key(event):
            return
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss_requested.emit()
            return
        super().keyPressEvent(event)

    def _handle_filter_key(self, event: QKeyEvent) -> bool:
        """Filter-mode key handling; False lets navigation keys pass through."""
        if event.key() == Qt.Key.Key_Escape:
            self.clear_filter()
            return True
        if event.key() == Qt.Key.Key_Backspace:
            self._set_filter(self._filter_text[:-1])
            return True
        text = event.text()
        blocked = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        if text and text.isprintable() and not event.modifiers() & blocked:
            self._set_filter(self._filter_text + text)
            return True
        return False

    def _set_filter(self, text: str) -> None:
        self._filter_text = text
        self._apply_filter()
        self.filter_changed.emit(text)

    def _apply_filter(self) -> None:
        """Hide non-matching items and keep the selection on a visible one."""
        for index in range(self.count()):
            item = self.item(index)
            item.setHidden(not matches_all_terms(item.text(), self._filter_text))
        current = self.currentItem()
        if current is None or current.isHidden():
            visible = (self.item(i) for i in range(self.count()))
            first = next((item for item in visible if not item.isHidden()), None)
            if first is None:
                self.setCurrentRow(-1)
            else:
                self.setCurrentItem(first)
        self._relayout()

    def _activate(self, item: QListWidgetItem | None) -> None:
        if item is not None:
            self.open_requested.emit(_path_of(item))

    def _relayout(self) -> None:
        # QListView caches cell geometry; after swapping items or resizing them
        # it keeps painting with the stale layout (cells clip or collapse) until
        # forced to lay out again — then keep the selection in view.
        self.doItemsLayout()
        if self.currentItem() is not None:
            self.scrollToItem(self.currentItem())

    def _on_current_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        # The frame lives in the icon pixmap, so both items need repainting.
        self._apply_icon(previous)
        self._apply_icon(current)

    def _render_next(self) -> None:
        if not self._pending:
            self._render_timer.stop()
            return
        item = self._pending.pop(0)
        path = _path_of(item)
        try:
            width, height = render.page_size(path, 0)
            zoom = _BASE_PX / max(width, height, 1.0)
            self._pixmaps[path] = QPixmap.fromImage(render.render_page(path, 0, zoom=zoom))
        except Exception as err:  # noqa: BLE001 — one bad file must not stop the queue
            log.warning("thumbnail render failed for %s: %s", path, err)
            return
        self._apply_icon(item)

    def _apply_icon(self, item: QListWidgetItem | None) -> None:
        if item is None or self._thumb_px <= 0:
            return
        pixmap = self._pixmaps.get(_path_of(item))
        if pixmap is None:
            pixmap = QPixmap(self._thumb_px, self._thumb_px)
            pixmap.fill(QColor(_PLACEHOLDER_GRAY))
        square = _center_crop_square(pixmap, self._thumb_px)
        if item is self.currentItem():
            square = _framed(square)
        item.setIcon(QIcon(square))


def _path_of(item: QListWidgetItem) -> Path:
    path: Path = item.data(Qt.ItemDataRole.UserRole)
    return path


def _center_crop_square(pixmap: QPixmap, px: int) -> QPixmap:
    """Scale ``pixmap`` to fill a ``px``-square, cropping the overflow centered.

    Uniform squares keep every grid cell (and the selection frame around it)
    the same size regardless of the source aspect ratio.
    """
    scaled = pixmap.scaled(
        px,
        px,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = (scaled.width() - px) // 2
    y = (scaled.height() - px) // 2
    return scaled.copy(x, y, px, px)


def _framed(pixmap: QPixmap) -> QPixmap:
    """A copy of ``pixmap`` with the selection stroke drawn along its edges."""
    framed = QPixmap(pixmap)
    stroke = _STROKE_PX
    painter = QPainter(framed)
    pen = QPen(QColor(_HIGHLIGHT))
    pen.setWidth(stroke)
    painter.setPen(pen)
    inset = stroke // 2
    painter.drawRect(inset, inset, framed.width() - stroke, framed.height() - stroke)
    painter.end()
    return framed
