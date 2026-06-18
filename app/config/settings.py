"""Centralized environment-driven settings for pdf-toolkit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ENV_BACKUP_DIR = "PDF_TOOLKIT_BACKUP_DIR"
ENV_LOG_LEVEL = "PDF_TOOLKIT_LOG_LEVEL"
ENV_DATABASE_URL = "PDF_TOOLKIT_DATABASE_URL"

DEFAULT_BACKUP_DIR = "backup"
DEFAULT_LOG_LEVEL = "INFO"


def _default_database_url() -> str:
    """Local SQLite file under the user's ``~/.pdf-toolkit`` directory."""
    return f"sqlite:///{Path.home() / '.pdf-toolkit' / 'pdf-toolkit.db'}"


@dataclass(frozen=True)
class Settings:
    backup_dir: Path
    log_level: str
    database_url: str = field(default_factory=_default_database_url)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            backup_dir=Path(os.getenv(ENV_BACKUP_DIR, DEFAULT_BACKUP_DIR)),
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            database_url=os.getenv(ENV_DATABASE_URL) or _default_database_url(),
        )
