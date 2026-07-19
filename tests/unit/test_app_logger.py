"""AppLogger is the single logging seam; every module imports its shared instance."""

from __future__ import annotations

import logging

import pytest

from app.app_logger import LOGGER_NAME, AppLogger, log


def test_shared_logger_is_the_app_logger() -> None:
    assert isinstance(log, AppLogger)
    assert LOGGER_NAME == "pdf_toolkit"


def test_modules_reuse_the_same_logger_instance() -> None:
    import app.pdf.merger as merger
    import app.storage.sqlite_backend as sqlite_backend

    assert merger.log is log
    assert sqlite_backend.log is log


def test_log_emits_through_the_stdlib_logger(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        log.info("hello %s", "world")
    assert "hello world" in caplog.text
