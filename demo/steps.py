"""App-specific demo steps for FastFileViewer.

Generic steps (TypeText, Pause, PressKey, Screenshot) come from the
automated-screenshot-connector; this module adds the one step the connector
cannot know: opening a bundled sample document.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from automated_screenshot_connector import DemoScript, TypeText

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@dataclass(frozen=True)
class OpenFile:
    """Open a bundled sample document from ``demo/assets/`` in the viewer.

    ``name`` may contain a ``{placeholder}`` filled from --automation-demo-texts
    (e.g. ``{sample_pdf}`` -> ``sample_de.pdf`` for the German run).
    """

    name: str

    def path(self) -> Path:
        return ASSETS_DIR / self.name


def localize_viewer_script(script: DemoScript, texts: Mapping[str, str]) -> DemoScript:
    """Fill ``{placeholder}``s in TypeText and OpenFile steps from ``texts``."""
    if not texts:
        return script
    steps = []
    for step in script.steps:
        try:
            if isinstance(step, TypeText):
                step = TypeText(step.text.format(**texts), step.char_delay_ms)
            elif isinstance(step, OpenFile):
                step = OpenFile(step.name.format(**texts))
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Demo '{script.name}': no text for placeholder {e} "
                f"(available: {', '.join(sorted(texts))})"
            ) from e
        steps.append(step)
    return DemoScript(id=script.id, name=script.name, steps=tuple(steps))
