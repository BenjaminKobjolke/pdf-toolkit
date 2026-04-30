"""Interactive CLI wizard: pick an operation, then run it.

Adding a new feature? Append a ``WizardOption`` to ``WIZARD_OPTIONS`` so the
wizard exposes it. CLAUDE.md mandates this update for every new feature.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from app.cli._common import EXIT_OK, run_with_backup
from app.config.settings import Settings
from app.logging_setup import configure_logging
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.swapper import swap_two_pages

log = logging.getLogger("pdf_toolkit")


@dataclass(frozen=True)
class WizardOption:
    """Single menu entry in the wizard.

    ``handler`` collects op-specific inputs from the user and runs the operation
    via ``run_with_backup``, returning a process exit code.
    """

    label: str
    handler: Callable[[Settings], int]


def _ask_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print(f"not a valid integer: {raw!r}")


class PdfCompleter(Completer):
    """Tab-completes ``*.pdf`` filenames from the current working directory.

    Case-insensitive prefix match against the text already typed.
    """

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        word = document.text_before_cursor
        prefix = word.lower()
        for pdf in sorted(Path.cwd().glob("*.pdf")):
            if pdf.name.lower().startswith(prefix):
                yield Completion(pdf.name, start_position=-len(word))


def _ask_pdf_path(prompt_text: str = "PDF (Tab to complete): ") -> Path:
    """Prompt for a PDF path with Tab-completion against ``*.pdf`` files in CWD."""
    while True:
        raw = pt_prompt(prompt_text, completer=PdfCompleter()).strip().strip('"')
        if not raw:
            print("path is required")
            continue
        return Path(raw)


def _ask_choice(option_count: int) -> int | None:
    while True:
        raw = input(f"Choose [1-{option_count}, q to quit]: ").strip().lower()
        if raw == "q":
            return None
        try:
            value = int(raw)
        except ValueError:
            print(f"not a valid choice: {raw!r}")
            continue
        if 1 <= value <= option_count:
            return value
        print(f"out of range: {value}")


def _handle_swap(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    return run_with_backup(pdf, swap_two_pages, settings)


def _handle_delete_single(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    page = _ask_int("Page number (1-based): ")
    return run_with_backup(pdf, lambda p: delete_page(p, page), settings)


def _handle_delete_range(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    start = _ask_int("Start page (1-based, inclusive): ")
    end = _ask_int("End page (1-based, inclusive): ")
    return run_with_backup(pdf, lambda p: delete_page_range(p, start, end), settings)


WIZARD_OPTIONS: tuple[WizardOption, ...] = (
    WizardOption("Swap pages (2-page PDF)", _handle_swap),
    WizardOption("Delete single page", _handle_delete_single),
    WizardOption("Delete page range", _handle_delete_range),
)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    print("pdf-toolkit wizard")
    print("==================")
    for index, option in enumerate(WIZARD_OPTIONS, start=1):
        print(f"{index}) {option.label}")

    choice = _ask_choice(len(WIZARD_OPTIONS))
    if choice is None:
        return EXIT_OK

    return WIZARD_OPTIONS[choice - 1].handler(settings)


if __name__ == "__main__":
    sys.exit(main())
