"""Keyboard-first numeric prompts (int and float) built on :class:`FormDialog`.

Drop-in replacements for ``QInputDialog.getInt`` / ``getDouble`` that adopt the
shared palette chrome. ``None`` means the user cancelled.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QSpinBox, QWidget

from app.gui.form_dialog import FormDialog, exec_value


@dataclass(frozen=True)
class NumberPromptSpec:
    """Title, label, initial value, and bounds for a numeric prompt."""

    title: str
    label: str
    value: float
    minimum: float
    maximum: float
    decimals: int = 2  # float prompts only


class NumberInputDialog(FormDialog):
    """A label plus a spin box (int or float) with an OK/Cancel row."""

    def __init__(
        self,
        spin: QAbstractSpinBox,
        *,
        title: str,
        label: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title=title, message=label, parent=parent)
        self.add_content(spin)
        self.add_ok_cancel()
        spin.setFocus()
        spin.selectAll()


def prompt_int(parent: QWidget | None, spec: NumberPromptSpec) -> int | None:
    """Prompt for a bounded integer; return it, or ``None`` if cancelled."""
    spin = QSpinBox()
    spin.setRange(int(spec.minimum), int(spec.maximum))
    spin.setValue(int(spec.value))
    dialog = NumberInputDialog(spin, title=spec.title, label=spec.label, parent=parent)
    return exec_value(dialog, lambda: int(spin.value()))


def prompt_float(parent: QWidget | None, spec: NumberPromptSpec) -> float | None:
    """Prompt for a bounded decimal; return it, or ``None`` if cancelled."""
    spin = QDoubleSpinBox()
    spin.setDecimals(spec.decimals)
    spin.setRange(spec.minimum, spec.maximum)
    spin.setValue(spec.value)
    dialog = NumberInputDialog(spin, title=spec.title, label=spec.label, parent=parent)
    return exec_value(dialog, lambda: float(spin.value()))
