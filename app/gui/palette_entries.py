"""Build the command-palette rows from the registry and the usage history.

Keeps :class:`MainWindow` thin: it loads the most-recently-used command ids and
hands them here with the registry. The recently-used commands float to the top
(most-recent first) and the single top-most enabled row is bolded as the "last
command" cue. Pure aside from reading each command's ``is_enabled``.
"""

from __future__ import annotations

from app.config.command_history import order_ids
from app.gui.commands import Command
from app.gui.filter_list_dialog import ListEntry


def build_palette_entries(registry: list[Command], mru: list[str]) -> list[ListEntry]:
    """Return palette rows ordered by recency, with the top enabled row bolded."""
    by_id = {cmd.command_id: cmd for cmd in registry}
    ordered_ids = order_ids([cmd.command_id for cmd in registry], mru)
    ordered = [by_id[cid] for cid in ordered_ids]

    first_enabled = next((cmd.command_id for cmd in ordered if cmd.is_enabled()), None)
    return [
        ListEntry(
            title=cmd.title,
            enabled=cmd.is_enabled(),
            payload=cmd,
            bold=cmd.command_id == first_enabled,
        )
        for cmd in ordered
    ]
