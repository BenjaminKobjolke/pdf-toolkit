"""Unit tests for the keyboard-first color picker."""

from __future__ import annotations

from app.gui.color_picker_dialog import ColorPickerDialog


def test_typed_hex_is_accepted(qapp: object) -> None:
    dialog = ColorPickerDialog()
    dialog.set_query("#ff8800")
    dialog.accept_current()
    assert dialog.chosen() == "#ff8800"


def test_typed_name_is_accepted_as_hex(qapp: object) -> None:
    dialog = ColorPickerDialog()
    dialog.set_query("white")
    dialog.accept_current()
    assert dialog.chosen() == "#ffffff"


def test_invalid_text_yields_no_choice(qapp: object) -> None:
    dialog = ColorPickerDialog()
    dialog.set_query("notacolor")
    dialog.accept_current()
    assert dialog.chosen() is None


def test_recents_appear_first(qapp: object) -> None:
    dialog = ColorPickerDialog(recent=["#123456", "#abcdef"])
    assert dialog.visible_hex(0) == "#123456"
    assert dialog.visible_hex(1) == "#abcdef"


def test_preview_follows_typed_value(qapp: object) -> None:
    dialog = ColorPickerDialog()
    dialog.set_query("#00ff00")
    assert dialog.preview_hex() == "#00ff00"


def test_name_filter_narrows_list(qapp: object) -> None:
    dialog = ColorPickerDialog()
    dialog.set_query("black")
    hexes = [dialog.visible_hex(i) for i in range(dialog.visible_count())]
    assert "#000000" in hexes


def test_selecting_list_row_accepts_its_hex(qapp: object) -> None:
    dialog = ColorPickerDialog(recent=["#abcdef"])
    dialog.set_query("")  # show all, recents first
    dialog.accept_current()
    assert dialog.chosen() == "#abcdef"


def test_no_transparent_option_by_default(qapp: object) -> None:
    dialog = ColorPickerDialog()
    values = [dialog.visible_hex(i) for i in range(dialog.visible_count())]
    assert ColorPickerDialog.TRANSPARENT not in values


def test_transparent_option_listed_first_when_allowed(qapp: object) -> None:
    dialog = ColorPickerDialog(allow_transparent=True)
    assert dialog.visible_hex(0) == ColorPickerDialog.TRANSPARENT


def test_typed_transparent_word_accepted(qapp: object) -> None:
    dialog = ColorPickerDialog(allow_transparent=True)
    dialog.set_query("transparent")
    dialog.accept_current()
    assert dialog.chosen() == ColorPickerDialog.TRANSPARENT


def test_transparent_sentinel_not_returned_when_not_allowed(qapp: object) -> None:
    # Qt parses the word "transparent" as a valid color, so it normalises to a
    # hex; the important guarantee is that the TRANSPARENT sentinel is not used.
    dialog = ColorPickerDialog()
    dialog.set_query("transparent")
    dialog.accept_current()
    assert dialog.chosen() != ColorPickerDialog.TRANSPARENT
