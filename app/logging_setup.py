"""Centralized logging configuration."""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

LOGGER_NAME = "pdf_toolkit"

# The one logger every module imports — single off/level switch via configure_logging.
log = logging.getLogger(LOGGER_NAME)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)
