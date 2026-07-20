"""Regenerate the bundled sample PDFs (run once, output is committed).

Usage: uv run python demo/assets/make_samples.py
Landscape pages so a page fills the wide 16:9 demo window without letterboxing;
page 2 carries the localized search term the "features" demo searches for.
"""

from __future__ import annotations

from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
# 16:10-ish landscape, close to the demo windows' aspect ratio.
PAGE_W, PAGE_H = 640, 400

CONTENT = {
    "sample_en.pdf": [
        (
            "Household Documents",
            [
                "A small folder of everyday paperwork.",
                "Page 2 holds the March invoice,",
                "page 3 the meter readings.",
            ],
        ),
        (
            "Invoice No. 2024-031",
            [
                "Garden service, March",
                "Labour: 3 h x 45 EUR = 135 EUR",
                "Materials: 28 EUR",
                "Total: 163 EUR - invoice due within 14 days.",
            ],
        ),
        (
            "Meter Readings",
            [
                "Electricity: 48,210 kWh",
                "Water: 1,872 m3",
                "Read on the first of the month.",
            ],
        ),
    ],
    "sample_de.pdf": [
        (
            "Haushaltsunterlagen",
            [
                "Ein kleiner Ordner mit Alltagspapieren.",
                "Seite 2 enthaelt die Maerz-Rechnung,",
                "Seite 3 die Zaehlerstaende.",
            ],
        ),
        (
            "Rechnung Nr. 2024-031",
            [
                "Gartenservice, Maerz",
                "Arbeitszeit: 3 h x 45 EUR = 135 EUR",
                "Material: 28 EUR",
                "Summe: 163 EUR - Rechnung zahlbar in 14 Tagen.",
            ],
        ),
        (
            "Zaehlerstaende",
            [
                "Strom: 48.210 kWh",
                "Wasser: 1.872 m3",
                "Abgelesen am Monatsersten.",
            ],
        ),
    ],
}


def main() -> None:
    for filename, pages in CONTENT.items():
        doc = fitz.open()
        for index, (title, lines) in enumerate(pages, start=1):
            page = doc.new_page(width=PAGE_W, height=PAGE_H)
            page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H), color=None, fill=(1, 1, 1))
            page.insert_text((40, 70), title, fontsize=26, fontname="hebo")
            y = 120
            for line in lines:
                page.insert_text((40, y), line, fontsize=15, fontname="helv")
                y += 28
            page.insert_text(
                (PAGE_W - 90, PAGE_H - 30), f"{index} / {len(pages)}", fontsize=10, fontname="helv"
            )
        doc.save(HERE / filename)
        print(f"wrote {filename} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
