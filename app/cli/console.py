"""Centralized user-facing console output for the CLI layer.

A single seam over ``print`` so wizard and installer output funnels through one
place. It writes to stdout today; swap the implementation here (rich, capture,
file) later without touching any call site. This is deliberately separate from
the diagnostic ``logging`` logger: ``logging`` is for operational/debug records,
``Console`` is for interactive UI the user types against.
"""

from __future__ import annotations


class Console:
    """Writes user-facing lines to stdout."""

    def line(self, message: str = "") -> None:
        """Write a single line of UI output to the user."""
        print(message)


console = Console()
