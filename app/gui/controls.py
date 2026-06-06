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
        self._doc_buttons: list[QPushButton] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._button(strings.BTN_PREV, self.prev_requested, doc_only=True))
        layout.addWidget(self._button(strings.BTN_NEXT, self.next_requested, doc_only=True))
        layout.addWidget(self._page_label)
        layout.addStretch(1)
        layout.addWidget(self._button(strings.BTN_DELETE_PAGE, self.delete_page_requested, True))
        layout.addWidget(self._button(strings.BTN_DELETE_RANGE, self.delete_range_requested, True))
        layout.addWidget(self._button(strings.BTN_SWAP, self.swap_requested, doc_only=True))
        layout.addWidget(self._button(strings.BTN_INSERT_PAGE, self.insert_page_requested, True))
        layout.addWidget(self._button(strings.BTN_EXTRACT_PAGE, self.extract_page_requested, True))
        layout.addWidget(self._button(strings.BTN_MERGE_FOLDER, self.merge_folder_requested))

        self.set_enabled_for_doc(False)

    def set_enabled_for_doc(self, has_doc: bool) -> None:
        """Enable the buttons that require an open document."""
        for button in self._doc_buttons:
            button.setEnabled(has_doc)

    def set_page_label(self, current: int, total: int) -> None:
        self._page_label.setText(strings.LABEL_PAGE_FMT.format(current=current, total=total))

    def _button(self, text: str, signal: SignalInstance, doc_only: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(signal.emit)
        if doc_only:
            self._doc_buttons.append(button)
        return button
