"""Keyboard-first confirmation and alert dialogs built on :class:`FormDialog`.

Replaces the bare ``QMessageBox`` calls so confirmations and alerts adopt the
shared palette chrome. :func:`confirm` covers the Yes/No and Save/Discard/Cancel
shapes; :func:`show_message` is the single-button alert (info/warning/error) — a
special case of the same dialog, so there is no separate ``MessageDialog`` class.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtWidgets import QDialogButtonBox, QWidget

from app.gui import strings
from app.gui.form_dialog import FormDialog


class DialogResult(Enum):
    """Which button the user chose in a :func:`confirm` dialog."""

    PRIMARY = auto()
    SECONDARY = auto()
    CANCEL = auto()


class Severity(Enum):
    """The level of a :func:`show_message` alert."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()


_SEVERITY_PREFIX: dict[Severity, str] = {
    Severity.INFO: "",
    Severity.WARNING: "⚠ ",
    Severity.ERROR: "✕ ",
}


@dataclass(frozen=True)
class ConfirmSpec:
    """Text and button labels for one confirmation dialog."""

    title: str
    message: str
    primary: str
    secondary: str | None = None
    cancel: str | None = None
    default: DialogResult = DialogResult.PRIMARY


class ConfirmDialog(FormDialog):
    """A message with up to three labelled buttons mapped to :class:`DialogResult`.

    Closing via Esc (or the window's close button) returns the most cautious
    available result — ``CANCEL`` if a cancel button exists, else ``SECONDARY``
    (the "No"-style choice), else ``PRIMARY``.
    """

    def __init__(self, spec: ConfirmSpec, parent: QWidget | None = None) -> None:
        super().__init__(title=spec.title, message=spec.message, parent=parent)
        self._result = self._fallback(spec.secondary, spec.cancel)
        box = QDialogButtonBox()
        self._add_button(box, spec.primary, DialogResult.PRIMARY, spec.default)
        if spec.secondary is not None:
            self._add_button(box, spec.secondary, DialogResult.SECONDARY, spec.default)
        if spec.cancel is not None:
            self._add_button(box, spec.cancel, DialogResult.CANCEL, spec.default)
        self.add_buttons(box)

    def _add_button(
        self, box: QDialogButtonBox, label: str, result: DialogResult, default: DialogResult
    ) -> None:
        button = box.addButton(label, QDialogButtonBox.ButtonRole.AcceptRole)
        button.clicked.connect(lambda: self._choose(result))
        if result == default:
            button.setDefault(True)

    def _choose(self, result: DialogResult) -> None:
        self._result = result
        self.accept()

    @staticmethod
    def _fallback(secondary: str | None, cancel: str | None) -> DialogResult:
        if cancel is not None:
            return DialogResult.CANCEL
        if secondary is not None:
            return DialogResult.SECONDARY
        return DialogResult.PRIMARY

    def result_choice(self) -> DialogResult:
        """Return the button the user chose (valid after the dialog closes)."""
        return self._result


def confirm(parent: QWidget | None, spec: ConfirmSpec) -> DialogResult:
    """Show a keyboard-first confirmation and return the chosen :class:`DialogResult`."""
    dialog = ConfirmDialog(spec, parent)
    dialog.exec()
    return dialog.result_choice()


def show_message(
    parent: QWidget | None, title: str, text: str, severity: Severity = Severity.INFO
) -> None:
    """Show a single-OK alert that adopts the shared palette chrome."""
    spec = ConfirmSpec(
        title=title, message=_SEVERITY_PREFIX[severity] + text, primary=strings.BTN_OK
    )
    ConfirmDialog(spec, parent).exec()
