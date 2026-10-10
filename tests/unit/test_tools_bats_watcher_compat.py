"""Static checks for tool batch files run by Tickets Watcher."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
INCLUDE_FILES = {"analyze_code_config.bat", "analyze_code_config.example.bat"}
BATCH_FILES = sorted(
    path
    for pattern in ("**/*.bat", "**/*.cmd")
    for path in TOOLS_DIR.glob(pattern)
    if not path.name.startswith(".tw-run-") and path.name not in INCLUDE_FILES
)


@pytest.mark.parametrize(
    "path", BATCH_FILES, ids=lambda path: path.relative_to(TOOLS_DIR).as_posix()
)
def test_tool_batch_files_return_and_do_not_block(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    non_blank_lines = [line for line in lines if line.strip()]

    assert non_blank_lines and "exit /b" in non_blank_lines[-1].lower(), (
        f"{path.relative_to(TOOLS_DIR)} must end with an explicit exit /b"
    )
    assert not any(re.match(r"^\s*@?\s*pause(?:\s|$)", line, re.IGNORECASE) for line in lines), (
        f"{path.relative_to(TOOLS_DIR)} contains a blocking pause"
    )
    relative_path = path.relative_to(TOOLS_DIR)
    has_watcher_guard = (
        relative_path == Path("build_and_create_installer_for_testing.bat")
        and re.search(
            r'^\s*if\s+"%TICKETS_WATCHER_COMMAND_RUN%"=="1"\s*\(\s*\n'
            r'(?:[^\n]*\n)*?\s*exit\s+/b\s+0\s*\n\s*\)',
            "\n".join(lines),
            re.IGNORECASE | re.MULTILINE,
        ) is not None
    )
    for line in lines:
        if re.match(r"^\s*@?\s*start(?:\s|$)", line, re.IGNORECASE):
            assert re.search(r"(?:^|\s)/wait(?:\s|$)", line, re.IGNORECASE) or has_watcher_guard, (
                f"{path.relative_to(TOOLS_DIR)} starts a process without /wait"
            )
