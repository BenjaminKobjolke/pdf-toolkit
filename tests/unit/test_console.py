"""Unit tests for the CLI console output seam."""

from __future__ import annotations

import pytest

from app.cli.console import Console


def test_line_writes_message_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    Console().line("hello")

    assert capsys.readouterr().out == "hello\n"


def test_line_without_argument_writes_blank_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    Console().line()

    assert capsys.readouterr().out == "\n"
