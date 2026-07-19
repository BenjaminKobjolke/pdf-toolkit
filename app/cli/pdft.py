"""Interactive CLI wizard: pick an operation, then run it.

Adding a new feature? Append a ``WizardOption`` to ``WIZARD_OPTIONS`` so the
wizard exposes it. CLAUDE.md mandates this update for every new feature.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from app.app_logger import configure_logging
from app.cli._common import EXIT_OK, run_folder_merge, run_to_new_file, run_with_backup
from app.cli.console import console
from app.config.settings import Settings
from app.pdf._inputs import PDF_EXTENSION, SUPPORTED_EXTENSIONS
from app.pdf.deleter import delete_page, delete_page_range
from app.pdf.extractor import default_extract_dest, extract_page
from app.pdf.inserter import insert_after
from app.pdf.merger import merge_folder
from app.pdf.mover import move_page
from app.pdf.rotator import rotate_page
from app.pdf.swapper import swap_two_pages


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
            console.line(f"not a valid integer: {raw!r}")


class FileCompleter(Completer):
    """Tab-completes CWD entries matching ``predicate`` (case-insensitive prefix)."""

    def __init__(self, predicate: Callable[[Path], bool]) -> None:
        self._predicate = predicate

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        word = document.text_before_cursor
        prefix = word.lower()
        for entry in sorted(Path.cwd().iterdir()):
            if self._predicate(entry) and entry.name.lower().startswith(prefix):
                yield Completion(entry.name, start_position=-len(word))


def _is_pdf(entry: Path) -> bool:
    return entry.is_file() and entry.suffix.lower() == PDF_EXTENSION


def _is_insertable(entry: Path) -> bool:
    return entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS


class PdfCompleter(FileCompleter):
    """Tab-completes ``*.pdf`` filenames from the current working directory."""

    def __init__(self) -> None:
        super().__init__(_is_pdf)


def _ask_path(prompt_text: str, completer: Completer) -> Path:
    """Prompt for a non-empty path with Tab-completion via ``completer``."""
    while True:
        raw = pt_prompt(prompt_text, completer=completer).strip().strip('"')
        if not raw:
            console.line("path is required")
            continue
        return Path(raw)


def _ask_pdf_path(prompt_text: str = "PDF (Tab to complete): ") -> Path:
    """Prompt for a PDF path with Tab-completion against ``*.pdf`` files in CWD."""
    return _ask_path(prompt_text, PdfCompleter())


def _ask_insert_path(prompt_text: str = "PDF or image to insert (Tab to complete): ") -> Path:
    """Prompt for a PDF/image path with Tab-completion against supported files in CWD."""
    return _ask_path(prompt_text, FileCompleter(_is_insertable))


def _ask_folder_path(prompt_text: str = "Folder (Tab to complete): ") -> Path:
    """Prompt for a folder path with Tab-completion against subdirectories in CWD."""
    return _ask_path(prompt_text, FileCompleter(lambda entry: entry.is_dir()))


def _ask_choice(option_count: int) -> int | None:
    while True:
        raw = input(f"Choose [1-{option_count}, q to quit]: ").strip().lower()
        if raw == "q":
            return None
        try:
            value = int(raw)
        except ValueError:
            console.line(f"not a valid choice: {raw!r}")
            continue
        if 1 <= value <= option_count:
            return value
        console.line(f"out of range: {value}")


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


def _handle_rotate(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    page = _ask_int("Page number (1-based): ")
    degrees = _ask_int("Rotate clockwise degrees (90=right, 180=flip, 270=left): ")
    return run_with_backup(pdf, lambda p: rotate_page(p, page, degrees), settings)


def _handle_move(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    from_page = _ask_int("Move page (1-based): ")
    to_page = _ask_int("To position (1-based): ")
    return run_with_backup(pdf, lambda p: move_page(p, from_page, to_page), settings)


def _handle_insert(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    insert = _ask_insert_path()
    after_page = _ask_int("Insert after page (1-based, 0 = front): ")
    return run_with_backup(pdf, lambda p: insert_after(p, insert, after_page), settings)


def _handle_extract(settings: Settings) -> int:
    pdf = _ask_pdf_path()
    page = _ask_int("Page to extract (1-based): ")
    dest = default_extract_dest(pdf, page)
    return run_to_new_file(pdf, lambda p: extract_page(p, page, dest), settings)


def _handle_merge_folder(settings: Settings) -> int:
    folder = _ask_folder_path()
    return run_folder_merge(folder, merge_folder, settings)


def _handle_launch_gui(settings: Settings) -> int:
    # Local import keeps PySide6 out of pure-CLI startup.
    from app.gui.main import main as gui_main

    return gui_main([])


def _handle_release_notes(settings: Settings) -> int:
    from app.release.notes_loader import load_release_notes

    notes = load_release_notes()
    if not notes:
        console.line("No release notes yet.")
        return EXIT_OK
    for note in notes:
        console.line(f"{note.title}  —  {note.label}  ({note.date})")
        for line in note.notes:
            console.line(f"  • {line}")
        console.line("")
    return EXIT_OK


# The "Edit text" feature (place/style/export text fields) is interactive-only
# and lives inside the GUI viewer; it is reached via "Open GUI viewer" below, so
# it needs no separate WizardOption of its own.
WIZARD_OPTIONS: tuple[WizardOption, ...] = (
    WizardOption("Swap pages (2-page PDF)", _handle_swap),
    WizardOption("Delete single page", _handle_delete_single),
    WizardOption("Delete page range", _handle_delete_range),
    WizardOption("Rotate page", _handle_rotate),
    WizardOption("Move page", _handle_move),
    WizardOption("Insert pages (PDF or image)", _handle_insert),
    WizardOption("Extract page to new file", _handle_extract),
    WizardOption("Merge folder (PDFs + images) -> merged.pdf", _handle_merge_folder),
    WizardOption("Open GUI viewer", _handle_launch_gui),
    WizardOption("Show release notes", _handle_release_notes),
)


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    console.line("pdf-toolkit wizard")
    console.line("==================")
    for index, option in enumerate(WIZARD_OPTIONS, start=1):
        console.line(f"{index}) {option.label}")

    choice = _ask_choice(len(WIZARD_OPTIONS))
    if choice is None:
        return EXIT_OK

    return WIZARD_OPTIONS[choice - 1].handler(settings)


if __name__ == "__main__":
    sys.exit(main())
