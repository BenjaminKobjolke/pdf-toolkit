"""Keyboard-first numeric prompts (int and float) built on :class:`FormDialog`.

Drop-in replacements for ``QInputDialog.getInt`` / ``getDouble`` that adopt the
shared palette chrome. ``None`` means the user cancelled.
"""

from __future__ import annotations

from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QSpinBox, QWidget

from app.gui.form_dialog import FormDialog, exec_value


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


def prompt_int(
    parent: QWidget | None, title: str, label: str, value: int, minimum: int, maximum: int
) -> int | None:
    """Prompt for a bounded integer; return it, or ``None`` if cancelled."""
    spin = QSpinBox()
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    dialog = NumberInputDialog(spin, title=title, label=label, parent=parent)
    return exec_value(dialog, lambda: int(spin.value()))


def prompt_float(
    parent: QWidget | None,
    title: str,
    label: str,
    value: float,
    minimum: float,
    maximum: float,
    decimals: int = 2,
) -> float | None:
    """Prompt for a bounded decimal; return it, or ``None`` if cancelled."""
    spin = QDoubleSpinBox()
    spin.setDecimals(decimals)
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    dialog = NumberInputDialog(spin, title=title, label=label, parent=parent)
    return exec_value(dialog, lambda: float(spin.value()))
