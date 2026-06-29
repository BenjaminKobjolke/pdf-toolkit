"""The shared application logger is a single instance every module imports."""

from __future__ import annotations

from app.logging_setup import LOGGER_NAME, log


def test_shared_logger_is_named_pdf_toolkit() -> None:
    assert log.name == LOGGER_NAME == "pdf_toolkit"


def test_modules_reuse_the_same_logger_instance() -> None:
    import app.pdf.merger as merger
    import app.storage.sqlite_backend as sqlite_backend

    assert getattr(merger, "log") is log
    assert getattr(sqlite_backend, "log") is log
