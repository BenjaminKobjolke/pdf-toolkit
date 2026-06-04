"""Centralized environment-driven settings for pdf-toolkit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ENV_BACKUP_DIR = "PDF_TOOLKIT_BACKUP_DIR"
ENV_LOG_LEVEL = "PDF_TOOLKIT_LOG_LEVEL"
ENV_RECENT_FILE = "PDF_TOOLKIT_RECENT_FILE"

DEFAULT_BACKUP_DIR = "backup"
DEFAULT_LOG_LEVEL = "INFO"


def _default_recent_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "recent.json"


@dataclass(frozen=True)
class Settings:
    backup_dir: Path
    log_level: str
    recent_file: Path = field(default_factory=_default_recent_file)

    @classmethod
    def from_env(cls) -> Settings:
        recent = os.getenv(ENV_RECENT_FILE)
        return cls(
            backup_dir=Path(os.getenv(ENV_BACKUP_DIR, DEFAULT_BACKUP_DIR)),
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            recent_file=Path(recent) if recent else _default_recent_file(),
        )
