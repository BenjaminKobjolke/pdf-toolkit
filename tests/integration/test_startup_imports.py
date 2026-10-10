"""Guard the GUI startup path from loading action-only dependencies."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTUP_ONLY_MODULES = (
    "pypdf",
    "img2pdf",
    "pikepdf",
    "markdown",
    "send2trash",
    "asyncio",
)


def _loaded_modules(import_statement: str) -> set[str]:
    watched = repr((*STARTUP_ONLY_MODULES, "app.gui.main_window"))
    code = (
        f"{import_statement}\n"
        "import json\n"
        "import sys\n"
        f"print(json.dumps([name for name in {watched} if name in sys.modules]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return set(json.loads(result.stdout))


def test_gui_entrypoint_does_not_import_main_window() -> None:
    loaded = _loaded_modules("import app.gui.main")

    assert "app.gui.main_window" not in loaded


def test_main_window_import_does_not_load_action_only_libraries() -> None:
    loaded = _loaded_modules("import app.gui.main_window")

    assert loaded - {"app.gui.main_window"} == set()
