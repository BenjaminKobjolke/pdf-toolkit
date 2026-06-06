"""User-facing image commands: add, scale, delete.

``add`` prompts for a file, asks whether to copy it into the PDF's ``assets/``
folder or reference it in place (remembering the last choice), then reuses the
shared placement chooser. ``scale`` edits the selected image's uniform factor.
Mirrors :class:`FieldActions` for text fields.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from app.config.image_choice_settings import CHOICE_COPY, CHOICE_REFERENCE, ImageChoiceStore
from app.gui import strings
from app.gui.image_controller import ImageController
from app.gui.operations import OpResult
from app.gui.placement import PlacementController
from app.pdf.image_assets import copy_into_assets, resolve_image_path

_MIN_SCALE = 0.05
_MAX_SCALE = 50.0


class ImageActions:
    """Add / scale / delete commands for placed images."""

    def __init__(
        self,
        parent: QWidget,
        images: ImageController,
        placement: PlacementController,
        choice_store: ImageChoiceStore,
        base_dir: Callable[[], Path | None],
        report: Callable[[OpResult], None],
    ) -> None:
        self._parent = parent
        self._images = images
        self._placement = placement
        self._choice_store = choice_store
        self._base_dir = base_dir
        self._report = report

    def add(self) -> None:
        """Pick an image, choose copy/reference, then place it via the chooser."""
        base_dir = self._base_dir()
        if base_dir is None:
            return
        chosen, _ = QFileDialog.getOpenFileName(
            self._parent, strings.DIALOG_ADD_IMAGE_TITLE, "", strings.FILE_FILTER_IMAGE
        )
        if not chosen:
            return
        src = Path(chosen)
        meta = self._resolve_meta(src, base_dir)
        if meta is None:
            return  # cancelled the copy/reference prompt
        load_from, path_str, absolute = meta

        def create(anchor: QPointF | None, centered: bool) -> None:
            self._images.add_image(load_from, path_str, absolute, anchor, centered=centered)

        self._placement.choose_and_place(create)

    def change_scale(self) -> None:
        """Prompt for a new uniform scale for the selected image."""
        scale = self._images.selected_scale()
        if scale is None:
            self._report(OpResult(True, strings.MSG_NO_IMAGE_SELECTED))
            return
        value, ok = QInputDialog.getDouble(
            self._parent,
            strings.DIALOG_IMAGE_SCALE_TITLE,
            strings.PROMPT_IMAGE_SCALE,
            scale,
            _MIN_SCALE,
            _MAX_SCALE,
            2,
        )
        if ok:
            self._images.set_selected_scale(value)

    def delete(self) -> None:
        self._images.delete_selected()

    # --- internals ----------------------------------------------------------

    def _resolve_meta(self, src: Path, base_dir: Path) -> tuple[Path, str, bool] | None:
        """Ask copy-vs-reference and return ``(load_from, path_str, absolute)``."""
        copy = self._ask_copy(src)
        if copy is None:
            return None
        if copy:
            self._choice_store.save(CHOICE_COPY)
            rel = copy_into_assets(src, base_dir)
            return resolve_image_path(rel, False, base_dir), rel, False
        self._choice_store.save(CHOICE_REFERENCE)
        return src, str(src), True

    def _ask_copy(self, src: Path) -> bool | None:
        """Yes -> copy into assets, No -> reference, None -> cancelled."""
        default = (
            QMessageBox.StandardButton.No
            if self._choice_store.load() == CHOICE_REFERENCE
            else QMessageBox.StandardButton.Yes
        )
        choice = QMessageBox.question(
            self._parent,
            strings.CONFIRM_IMAGE_COPY_TITLE,
            strings.CONFIRM_IMAGE_COPY_TEXT,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            default,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return None
        return choice == QMessageBox.StandardButton.Yes
