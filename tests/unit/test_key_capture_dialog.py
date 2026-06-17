"""Chord-string conversion and the two-phase capture dialog (offscreen Qt)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog

from app.gui.key_capture_dialog import KeyCaptureDialog, chord_from_event


def _press(
    dialog: KeyCaptureDialog,
    key: Qt.Key,
    mods: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    dialog.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, int(key), mods))


def test_chord_from_event_builds_portable_text() -> None:
    alt = Qt.KeyboardModifier.AltModifier
    ctrl_shift = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    assert chord_from_event(alt, Qt.Key.Key_W) == "Alt+W"
    assert chord_from_event(ctrl_shift, Qt.Key.Key_F) == "Ctrl+Shift+F"
    assert chord_from_event(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_0) == "Ctrl+0"


def test_chord_from_event_ignores_lone_modifier() -> None:
    assert chord_from_event(Qt.KeyboardModifier.NoModifier, Qt.Key.Key_Control) is None
    assert chord_from_event(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Shift) is None


def test_capture_then_confirm_yields_chord(qapp: object) -> None:
    dialog = KeyCaptureDialog("Exit")
    _press(dialog, Qt.Key.Key_W, Qt.KeyboardModifier.AltModifier)
    assert dialog.chosen_chord() == "Alt+W"
    _press(dialog, Qt.Key.Key_Return)
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_lone_modifier_does_not_capture(qapp: object) -> None:
    dialog = KeyCaptureDialog("Exit")
    _press(dialog, Qt.Key.Key_Shift, Qt.KeyboardModifier.ShiftModifier)
    assert dialog.chosen_chord() is None


def test_escape_before_capture_cancels(qapp: object) -> None:
    dialog = KeyCaptureDialog("Exit")
    _press(dialog, Qt.Key.Key_Escape)
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_escape_after_capture_clears_back_to_waiting(qapp: object) -> None:
    dialog = KeyCaptureDialog("Exit")
    _press(dialog, Qt.Key.Key_W, Qt.KeyboardModifier.AltModifier)
    _press(dialog, Qt.Key.Key_Escape)
    assert dialog.chosen_chord() is None
    assert dialog.result() != QDialog.DialogCode.Accepted
