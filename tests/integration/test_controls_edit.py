"""Integration tests for the EditBar signals (offscreen Qt)."""

from __future__ import annotations

from app.gui.edit_bar import EditBar
from app.gui.text_style import TextStyle


def test_toggle_emits_edit_mode(qapp: object) -> None:
    bar = EditBar()
    seen: list[bool] = []
    bar.edit_mode_toggled.connect(seen.append)

    bar._toggle.setChecked(True)
    bar._toggle.setChecked(False)

    assert seen == [True, False]


def test_add_and_export_emit(qapp: object) -> None:
    bar = EditBar()
    added: list[int] = []
    exported: list[int] = []
    bar.add_field_requested.connect(lambda: added.append(1))
    bar.export_text_requested.connect(lambda: exported.append(1))

    bar._add.click()
    bar._export.click()

    assert added == [1]
    assert exported == [1]


def test_size_change_emits_style(qapp: object) -> None:
    bar = EditBar()
    styles: list[object] = []
    bar.style_changed.connect(styles.append)

    bar._size.setValue(42.0)

    assert styles
    assert isinstance(styles[-1], TextStyle)
    assert styles[-1].font_size == 42.0


def test_default_style_is_transparent(qapp: object) -> None:
    bar = EditBar()
    assert bar.current_style().bg_color is None
