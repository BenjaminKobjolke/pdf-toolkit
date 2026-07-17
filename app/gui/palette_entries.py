"""Build the command-palette rows from the registry and the usage history.

Keeps :class:`MainWindow` thin: it loads the most-recently-used command ids and
hands them here with the registry. The recently-used commands float to the top
(most-recent first) and the single top-most enabled row is bolded as the "last
command" cue. Pure aside from reading each command's ``is_enabled``.
"""

from __future__ import annotations

from collections.abc import Callable

from app.config.command_history import order_ids
from app.config.key_bindings import KeyMap
from app.gui.commands import Command
from app.gui.filter_list_dialog import ListEntry


def build_palette_entries(
    registry: list[Command],
    mru: list[str],
    keymap: KeyMap,
    is_available: Callable[[Command], bool] = lambda cmd: cmd.is_enabled(),
) -> list[ListEntry]:
    """Return palette rows ordered by recency, bolding the top available row.

    ``is_available`` decides whether each row is enabled/runnable — the command
    palette passes a format-aware check (``cmd.available(current_format)``) so
    commands the open document can't use are greyed; the shortcut-config picker
    keeps the default (``is_enabled`` only), since bindings apply to any command.

    Each row carries every chord bound to the command (``keymap.chords_for``,
    comma-joined) so the dialog can render them right-aligned.
    """
    by_id = {cmd.command_id: cmd for cmd in registry}
    ordered_ids = order_ids([cmd.command_id for cmd in registry], mru)
    ordered = [by_id[cid] for cid in ordered_ids]

    first_enabled = next((cmd.command_id for cmd in ordered if is_available(cmd)), None)
    return [
        ListEntry(
            title=cmd.display_title(),
            enabled=is_available(cmd),
            payload=cmd,
            bold=cmd.command_id == first_enabled,
            shortcut=", ".join(keymap.chords_for(cmd.command_id)),
        )
        for cmd in ordered
    ]
