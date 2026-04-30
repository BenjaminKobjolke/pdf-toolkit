"""Unit tests for the pdft wizard helpers and registry."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from app.cli.pdft import (
    WIZARD_OPTIONS,
    PdfCompleter,
    WizardOption,
    _ask_choice,
    _ask_int,
    _ask_pdf_path,
)
from tests.conftest import MakePdf


def _input_queue(values: list[str]) -> Iterator[str]:
    yield from values


def test_wizard_options_are_registered() -> None:
    labels = [opt.label for opt in WIZARD_OPTIONS]

    assert "Swap pages (2-page PDF)" in labels
    assert "Delete single page" in labels
    assert "Delete page range" in labels


def test_wizard_options_have_callable_handlers() -> None:
    for opt in WIZARD_OPTIONS:
        assert isinstance(opt, WizardOption)
        assert callable(opt.handler)


def test_ask_int_returns_parsed_int(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = _input_queue(["7"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert _ask_int("Page: ") == 7


def test_ask_int_retries_on_invalid(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = _input_queue(["abc", "  ", "42"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert _ask_int("Page: ") == 42
    out = capsys.readouterr().out
    assert "not a valid integer" in out


def test_ask_pdf_path_returns_typed_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.cli.pdft.pt_prompt",
        lambda *_a, **_kw: '  "C:\\some path\\file.pdf"  ',
    )

    result = _ask_pdf_path()

    assert str(result) == "C:\\some path\\file.pdf"


def test_ask_pdf_path_retries_on_empty_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = _input_queue(["", "  ", "C:\\file.pdf"])
    monkeypatch.setattr("app.cli.pdft.pt_prompt", lambda *_a, **_kw: next(answers))

    result = _ask_pdf_path()

    assert str(result) == "C:\\file.pdf"
    assert "path is required" in capsys.readouterr().out


def test_pdf_completer_lists_only_pdfs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, make_pdf: MakePdf
) -> None:
    make_pdf([(10, 10), (20, 20)], name="alpha.pdf")
    make_pdf([(10, 10), (20, 20)], name="beta.pdf")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    completer = PdfCompleter()
    document = Document(text="", cursor_position=0)
    completions = list(completer.get_completions(document, CompleteEvent()))

    names = sorted(c.text for c in completions)
    assert names == ["alpha.pdf", "beta.pdf"]


def test_pdf_completer_filters_by_prefix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, make_pdf: MakePdf
) -> None:
    make_pdf([(10, 10), (20, 20)], name="alpha.pdf")
    make_pdf([(10, 10), (20, 20)], name="beta.pdf")
    monkeypatch.chdir(tmp_path)

    completer = PdfCompleter()
    document = Document(text="al", cursor_position=2)
    completions = list(completer.get_completions(document, CompleteEvent()))

    names = [c.text for c in completions]
    assert names == ["alpha.pdf"]


def test_pdf_completer_is_case_insensitive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, make_pdf: MakePdf
) -> None:
    make_pdf([(10, 10), (20, 20)], name="Alpha.pdf")
    monkeypatch.chdir(tmp_path)

    completer = PdfCompleter()
    document = Document(text="al", cursor_position=2)
    completions = list(completer.get_completions(document, CompleteEvent()))

    names = [c.text for c in completions]
    assert names == ["Alpha.pdf"]


def test_pdf_completer_replaces_typed_word(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, make_pdf: MakePdf
) -> None:
    make_pdf([(10, 10), (20, 20)], name="alpha.pdf")
    monkeypatch.chdir(tmp_path)

    completer = PdfCompleter()
    document = Document(text="al", cursor_position=2)
    completion = next(iter(completer.get_completions(document, CompleteEvent())))

    assert completion.start_position == -2


def test_ask_choice_quit_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "q")

    assert _ask_choice(3) is None


def test_ask_choice_returns_valid_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")

    assert _ask_choice(3) == 2


def test_ask_choice_retries_on_out_of_range(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = _input_queue(["0", "9", "x", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert _ask_choice(3) == 1
    out = capsys.readouterr().out
    assert "out of range" in out
    assert "not a valid choice" in out
