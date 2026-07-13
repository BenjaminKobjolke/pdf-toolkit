"""The toolbar of navigation + operation buttons. Emit-only; no business logic."""

from __future__ import annotations

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.gui import strings


class OperationBar(QWidget):
    """Navigation and operation buttons; the window connects to its signals."""

    prev_requested = Signal()
    next_requested = Signal()
    swap_requested = Signal()
    delete_page_requested = Signal()
    delete_range_requested = Signal()
    insert_page_requested = Signal()
    extract_page_requested = Signal()
    merge_folder_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._page_label = QLabel(strings.LABEL_NO_DOC)
        # Nav buttons need only an open doc; the page-op buttons are PDF-only.
        # ponytail: a fixed 6-button toolbar, so a nav-vs-pdf split is simpler
        # than driving it from the command registry (which stays authoritative).
        self._nav_buttons: list[QPushButton] = []
        self._pdf_buttons: list[QPushButton] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._button(strings.BTN_PREV, self.prev_requested, self._nav_buttons))
        layout.addWidget(self._button(strings.BTN_NEXT, self.next_requested, self._nav_buttons))
        layout.addWidget(self._page_label)
        layout.addStretch(1)
        layout.addWidget(
            self._button(strings.BTN_DELETE_PAGE, self.delete_page_requested, self._pdf_buttons)
        )
        layout.addWidget(
            self._button(strings.BTN_DELETE_RANGE, self.delete_range_requested, self._pdf_buttons)
        )
        layout.addWidget(self._button(strings.BTN_SWAP, self.swap_requested, self._pdf_buttons))
        layout.addWidget(
            self._button(strings.BTN_INSERT_PAGE, self.insert_page_requested, self._pdf_buttons)
        )
        layout.addWidget(
            self._button(strings.BTN_EXTRACT_PAGE, self.extract_page_requested, self._pdf_buttons)
        )
        layout.addWidget(self._button(strings.BTN_MERGE_FOLDER, self.merge_folder_requested))

        self.update_for(has_doc=False, is_pdf=False)

    def update_for(self, has_doc: bool, is_pdf: bool) -> None:
        """Enable nav buttons for any open doc; page-op buttons only for PDFs."""
        for button in self._nav_buttons:
            button.setEnabled(has_doc)
        for button in self._pdf_buttons:
            button.setEnabled(has_doc and is_pdf)

    def set_page_label(self, current: int, total: int) -> None:
        self._page_label.setText(strings.LABEL_PAGE_FMT.format(current=current, total=total))

    def _button(
        self, text: str, signal: SignalInstance, group: list[QPushButton] | None = None
    ) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(signal.emit)
        if group is not None:
            group.append(button)
        return button
