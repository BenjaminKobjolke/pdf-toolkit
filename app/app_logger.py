"""Centralized logging — ``AppLogger`` is the single output seam and off switch."""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

LOGGER_NAME = "pdf_toolkit"


class AppLogger:
    """Wraps the one stdlib logger; feature code never touches ``logging`` directly."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(LOGGER_NAME)

    def configure(self, level: str) -> None:
        logging.basicConfig(level=level.upper(), format=LOG_FORMAT, force=True)

    def debug(self, message: str, *args: object, exc_info: bool = False) -> None:
        self._logger.debug(message, *args, exc_info=exc_info)

    def info(self, message: str, *args: object) -> None:
        self._logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        self._logger.error(message, *args)

    def exception(self, message: str, *args: object) -> None:
        self._logger.exception(message, *args)


# The one instance every module imports — single off/level switch via configure.
log = AppLogger()


def configure_logging(level: str) -> None:
    """Module-level entry point the CLI/GUI mains call at startup."""
    log.configure(level)
