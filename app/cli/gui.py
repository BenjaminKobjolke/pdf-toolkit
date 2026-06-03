"""CLI entry point that launches the GUI viewer.

Kept uniform with the other ``app.cli.<module>`` entry points so the bat
wrappers, ``[project.scripts]``, and the wizard all invoke the GUI the same way.
"""

from __future__ import annotations

import sys


def main() -> int:
    from app.gui.main import main as gui_main

    return gui_main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
