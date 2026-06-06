"""Centralized environment-driven settings for pdf-toolkit."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ENV_BACKUP_DIR = "PDF_TOOLKIT_BACKUP_DIR"
ENV_LOG_LEVEL = "PDF_TOOLKIT_LOG_LEVEL"
ENV_RECENT_FILE = "PDF_TOOLKIT_RECENT_FILE"
ENV_UI_STATE_FILE = "PDF_TOOLKIT_UI_STATE_FILE"
ENV_PALETTE_FILE = "PDF_TOOLKIT_PALETTE_FILE"

DEFAULT_BACKUP_DIR = "backup"
DEFAULT_LOG_LEVEL = "INFO"


def _default_recent_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "recent.json"


def _default_ui_state_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "ui_state.json"


def _default_palette_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "palette.json"


def _path_from_env(env_var: str, default_fn: Callable[[], Path]) -> Path:
    """Return the env-var path if set, otherwise the computed default."""
    value = os.getenv(env_var)
    return Path(value) if value else default_fn()


@dataclass(frozen=True)
class Settings:
    backup_dir: Path
    log_level: str
    recent_file: Path = field(default_factory=_default_recent_file)
    ui_state_file: Path = field(default_factory=_default_ui_state_file)
    palette_file: Path = field(default_factory=_default_palette_file)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            backup_dir=Path(os.getenv(ENV_BACKUP_DIR, DEFAULT_BACKUP_DIR)),
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            recent_file=_path_from_env(ENV_RECENT_FILE, _default_recent_file),
            ui_state_file=_path_from_env(ENV_UI_STATE_FILE, _default_ui_state_file),
            palette_file=_path_from_env(ENV_PALETTE_FILE, _default_palette_file),
        )
