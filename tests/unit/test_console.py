"""Unit tests for the CLI console output seam."""

from __future__ import annotations

import io

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


def test_ask_reads_input_without_watcher_marker(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(" Alice\n"))

    assert Console().ask("Name: ", watcher_run=False) == " Alice"
    assert capsys.readouterr().out == "Name: "


def test_ask_prints_watcher_marker_before_reading(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("Alice\n"))

    assert Console().ask("Name: ", watcher_run=True) == "Alice"
    assert capsys.readouterr().out == "Name: \n::tw-input-line::\n"
