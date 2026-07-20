"""The keyboard-first "File information" dialog and its metadata rows.

Reuses the palette's :class:`FilterListDialog` so navigation, filtering, sizing
and chrome come for free; the only new behaviour is that **Enter copies the
highlighted value and keeps the dialog open** (marking the row ``✓ copied``) so
several values can be copied without reopening.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from app.gui import file_strings, render
from app.gui.filter_list_dialog import FilterListDialog, FilterListOptions, ListEntry
from app.gui.operations import OpResult
from app.gui.palette_controller import PaletteController
from app.pdf.file_format import IMAGE_FORMATS, FileFormat


@dataclass(frozen=True)
class FileInfoField:
    """One label/value row shown in the File information dialog."""

    label: str
    value: str


def _human_size(num_bytes: int) -> str:
    # ponytail: display formatter (1024-based, 1-decimal), not exact IEC units.
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"  # pragma: no cover - loop always returns first


def _dimension_fields(source: Path, page_index: int, is_image: bool) -> list[FileInfoField]:
    if is_image:
        # fitz reports an image page rect in points; readers expect native pixels.
        with Image.open(source) as img:
            width, height = float(img.width), float(img.height)
        unit = "px"
    else:
        width, height = render.page_size(source, page_index)
        unit = "pt"
    return [
        FileInfoField(file_strings.LABEL_WIDTH, f"{width:g} {unit}"),
        FileInfoField(file_strings.LABEL_HEIGHT, f"{height:g} {unit}"),
    ]


def _metadata_fields(source: Path) -> list[FileInfoField]:
    meta = render.doc_metadata(source)
    pairs = (
        (file_strings.LABEL_TITLE, meta.title),
        (file_strings.LABEL_AUTHOR, meta.author),
        (file_strings.LABEL_SUBJECT, meta.subject),
        (file_strings.LABEL_KEYWORDS, meta.keywords),
        (file_strings.LABEL_CREATOR, meta.creator),
        (file_strings.LABEL_PRODUCER, meta.producer),
    )
    return [FileInfoField(label, value) for label, value in pairs if value]


def collect_file_info(source: Path, page_index: int) -> list[FileInfoField]:
    """Gather the copyable info rows for ``source`` at 0-based ``page_index``."""
    fmt = FileFormat.of(source)
    is_image = fmt in IMAGE_FORMATS
    is_pdf = fmt is FileFormat.PDF
    fields = [
        FileInfoField(file_strings.LABEL_NAME, source.name),
        FileInfoField(file_strings.LABEL_PATH, str(source)),
        FileInfoField(file_strings.LABEL_FORMAT, fmt.name if fmt is not None else "?"),
        FileInfoField(file_strings.LABEL_SIZE, _human_size(source.stat().st_size)),
    ]
    if is_pdf:  # only PDFs have meaningful multi-page counts to page through
        fields.append(FileInfoField(file_strings.LABEL_PAGES, str(render.page_count(source))))
        fields.append(FileInfoField(file_strings.LABEL_CURRENT_PAGE, str(page_index + 1)))
    fields.extend(_dimension_fields(source, page_index, is_image))
    if is_pdf:
        fields.extend(_metadata_fields(source))
    return fields


class FileInfoDialog(FilterListDialog):
    """Filter list whose Enter copies the row's value and stays open."""

    def __init__(
        self,
        entries: list[ListEntry],
        options: FilterListOptions,
        on_copy: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(entries, options, parent=parent)
        self._on_copy = on_copy

    def accept_current(self) -> None:  # noqa: D102 - overrides "accept + close"
        entry = self.current_entry()
        if entry is None:
            return
        self._on_copy(str(entry.payload))
        item = self._list.item(self._list.currentRow())
        if item is not None:
            item.setText(f"{entry.title}{file_strings.FILE_INFO_COPIED_MARK}")

    def _on_row_changed(self) -> None:
        """Clear the ``✓ copied`` marker once the selection moves elsewhere."""
        for i in range(min(self._list.count(), self.visible_count())):
            item = self._list.item(i)
            if item is not None:
                item.setText(self.visible_entry(i).title)


class FileInfoActions:
    """Open the File information dialog for the current document."""

    def __init__(
        self,
        parent: QWidget,
        palette: PaletteController,
        source: Callable[[], Path | None],
        current_page: Callable[[], int],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._palette = palette
        self._source = source
        self._current_page = current_page
        self._report = report

    def show(self) -> None:
        source = self._source()
        if source is None:
            return
        entries = [
            ListEntry(title=f"{field.label}: {field.value}", payload=field.value)
            for field in collect_file_info(source, self._current_page())
        ]
        dialog = FileInfoDialog(
            entries,
            FilterListOptions(
                placeholder=file_strings.FILE_INFO_PLACEHOLDER,
                title=file_strings.FILE_INFO_TITLE,
            ),
            self._copy,
            parent=self._parent,
        )
        self._palette.apply_to(dialog, self._parent.size())
        dialog.exec()

    def _copy(self, value: str) -> None:
        QGuiApplication.clipboard().setText(value)
        self._report(OpResult(True, file_strings.MSG_COPIED_INFO))
