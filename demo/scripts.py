"""The registered demo scripts, keyed by their ``--automation-demo`` id.

ids 1/2 are the wide (16:9) demos; ids 3/4 are square (1:1) variants with extra
beats to fill the taller window. Recording window size + settings per id live in
tools/create_media/fastfileviewer.json; localized file names and the search term
come from tools/create_media/texts/{lang}.json via ``{placeholder}``s.

The overview demos browse the photo set (Alt+Right = next file in folder) —
wide uses landscape photos, square uses portrait ones. The features demos show
the md dark-mode toggle and pdf full-text search. Photos are language-neutral,
so only the md/pdf names and the search term are localized.

Palette filter texts must uniquely match one command (e.g. "dark" only matches
"Text/Markdown: toggle dark mode") so Return runs the intended one.
"""

from __future__ import annotations

from automated_screenshot_connector import DemoScript, Pause, PressKey, Screenshot, TypeText

from demo.steps import OpenFile

DEMOS: dict[int, DemoScript] = {
    1: DemoScript(
        id=1,
        name="viewer-overview",
        steps=(
            Pause(0.5),
            OpenFile("photos/landscape/dummy_1.jpg"),
            Pause(1.5),
            PressKey("Alt+Right"),
            Pause(1.4),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("next file"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.5),
            Screenshot("viewer-overview"),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("rotate right"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("zoom 100"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            Pause(1.0),
        ),
    ),
    2: DemoScript(
        id=2,
        name="features",
        steps=(
            Pause(0.5),
            OpenFile("{sample_md}"),
            Pause(1.6),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("dark"),
            Pause(1.0),
            PressKey("Return"),
            Pause(1.5),
            Screenshot("overview-dark"),
            OpenFile("{sample_pdf}"),
            Pause(1.5),
            PressKey("Ctrl+F"),
            Pause(0.8),
            TypeText("{search_term}"),
            Pause(1.2),
            PressKey("Return"),
            Pause(1.5),
            Screenshot("features"),
            PressKey("Ctrl+R"),
            Pause(1.5),
            Pause(1.0),
        ),
    ),
    3: DemoScript(
        id=3,
        name="viewer-overview-square",
        steps=(
            Pause(0.5),
            OpenFile("photos/portrait/dummy_1.jpg"),
            Pause(1.6),
            PressKey("Alt+Right"),
            Pause(1.5),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("next file"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            Screenshot("viewer-overview"),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("rotate right"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("flip hor"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            PressKey("Ctrl+Shift+P"),
            Pause(0.6),
            TypeText("zoom 100"),
            Pause(0.9),
            PressKey("Return"),
            Pause(1.6),
            Pause(1.0),
        ),
    ),
    4: DemoScript(
        id=4,
        name="features-square",
        steps=(
            Pause(0.5),
            OpenFile("{sample_md}"),
            Pause(1.8),
            PressKey("Ctrl+Shift+P"),
            Pause(0.8),
            TypeText("dark"),
            Pause(1.2),
            PressKey("Return"),
            Pause(1.8),
            Screenshot("overview-dark"),
            OpenFile("{sample_pdf}"),
            Pause(1.8),
            PressKey("Ctrl+F"),
            Pause(0.8),
            TypeText("{search_term}"),
            Pause(1.4),
            PressKey("Return"),
            Pause(1.8),
            Screenshot("features"),
            PressKey("Ctrl+R"),
            Pause(1.5),
            PressKey("Ctrl+R"),
            Pause(1.5),
            Pause(1.0),
        ),
    ),
}
