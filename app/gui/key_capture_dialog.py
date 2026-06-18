"""Minimal modal that captures a single keyboard chord for the shortcut config.

A custom ``keyPressEvent`` widget rather than ``QKeySequenceEdit``: the latter
captures multi-key sequences and swallows Enter/Tab, which fights the
Enter-to-confirm flow and the ignore-lone-modifier rule. Two phases — *capture*
(press a chord) then *review* (Enter confirms, Esc clears/cancels). The chord
string is produced via ``QKeySequence.toString`` so it matches the spelling the
installer feeds back into ``QKeySequence`` exactly.
"""

from __future__ import annotations

from PySide6.QtCore import QKeyCombination, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.gui import strings
from app.gui.base_dialog import BaseDialog

_MODIFIER_KEYS = frozenset(
    {
        Qt.Key.Key_Control,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Meta,
        Qt.Key.Key_AltGr,
        Qt.Key.Key_Super_L,
        Qt.Key.Key_Super_R,
    }
)


def chord_from_event(modifiers: Qt.KeyboardModifier, key: Qt.Key) -> str | None:
    """Return the portable chord string (e.g. ``Alt+W``) or ``None`` for a lone modifier."""
    if key in _MODIFIER_KEYS:
        return None
    sequence = QKeySequence(QKeyCombination(modifiers, key))
    text = sequence.toString(QKeySequence.SequenceFormat.PortableText)
    return text or None


class KeyCaptureDialog(BaseDialog):
    """Capture one chord for ``command_title``; ``chosen_chord`` holds the result."""

    def __init__(self, command_title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(strings.CAPTURE_TITLE)
        self._command_title = command_title
        self._chord: str | None = None
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        self.resize(360, 140)
        self._refresh()

    def chosen_chord(self) -> str | None:
        """Return the captured chord (only meaningful once the dialog is accepted)."""
        return self._chord

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = Qt.Key(event.key())
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._chord is not None:
                self.accept()
            return
        if key == Qt.Key.Key_Escape:
            if self._chord is not None:
                self._chord = None
                self._refresh()
            else:
                self.reject()
            return
        chord = chord_from_event(event.modifiers(), key)
        if chord is None:
            return
        self._chord = chord
        self._refresh()

    def _refresh(self) -> None:
        if self._chord is None:
            self._label.setText(
                strings.CAPTURE_PROMPT_FMT.format(title=self._command_title)
                + "\n\n"
                + strings.CAPTURE_WAITING
            )
        else:
            self._label.setText(strings.CAPTURE_DETECTED_FMT.format(chord=self._chord))
