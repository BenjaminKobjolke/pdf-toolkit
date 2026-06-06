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
ENV_COMMAND_HISTORY_FILE = "PDF_TOOLKIT_COMMAND_HISTORY_FILE"
ENV_PLACEMENT_FILE = "PDF_TOOLKIT_PLACEMENT_FILE"
ENV_WINDOW_FILE = "PDF_TOOLKIT_WINDOW_FILE"
ENV_IMAGE_CHOICE_FILE = "PDF_TOOLKIT_IMAGE_CHOICE_FILE"
ENV_OUTLINE_FILE = "PDF_TOOLKIT_OUTLINE_FILE"
ENV_ZOOM_FILE = "PDF_TOOLKIT_ZOOM_FILE"

DEFAULT_BACKUP_DIR = "backup"
DEFAULT_LOG_LEVEL = "INFO"


def _default_recent_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "recent.json"


def _default_ui_state_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "ui_state.json"


def _default_palette_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "palette.json"


def _default_command_history_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "command_history.json"


def _default_placement_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "placement.json"


def _default_window_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "window.json"


def _default_image_choice_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "image_choice.json"


def _default_outline_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "outline.json"


def _default_zoom_file() -> Path:
    return Path.home() / ".pdf-toolkit" / "zoom.json"


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
    command_history_file: Path = field(default_factory=_default_command_history_file)
    placement_file: Path = field(default_factory=_default_placement_file)
    window_file: Path = field(default_factory=_default_window_file)
    image_choice_file: Path = field(default_factory=_default_image_choice_file)
    outline_file: Path = field(default_factory=_default_outline_file)
    zoom_file: Path = field(default_factory=_default_zoom_file)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            backup_dir=Path(os.getenv(ENV_BACKUP_DIR, DEFAULT_BACKUP_DIR)),
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            recent_file=_path_from_env(ENV_RECENT_FILE, _default_recent_file),
            ui_state_file=_path_from_env(ENV_UI_STATE_FILE, _default_ui_state_file),
            palette_file=_path_from_env(ENV_PALETTE_FILE, _default_palette_file),
            command_history_file=_path_from_env(
                ENV_COMMAND_HISTORY_FILE, _default_command_history_file
            ),
            placement_file=_path_from_env(ENV_PLACEMENT_FILE, _default_placement_file),
            window_file=_path_from_env(ENV_WINDOW_FILE, _default_window_file),
            image_choice_file=_path_from_env(ENV_IMAGE_CHOICE_FILE, _default_image_choice_file),
            outline_file=_path_from_env(ENV_OUTLINE_FILE, _default_outline_file),
            zoom_file=_path_from_env(ENV_ZOOM_FILE, _default_zoom_file),
        )
