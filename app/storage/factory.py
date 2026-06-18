"""Build a :class:`~app.storage.backend.StorageBackend` from a connection URL.

The URL scheme selects the engine, so switching backends is a configuration
change (``PDF_TOOLKIT_DATABASE_URL``) rather than a code change. This module is
the single place that names a concrete backend; adding MySQL means adding one
branch here plus its implementation module.
"""

from __future__ import annotations

from pathlib import Path

from app.storage.backend import StorageBackend
from app.storage.sqlite_backend import SqliteBackend

_SQLITE_PREFIX = "sqlite:///"


def make_backend(database_url: str) -> StorageBackend:
    """Return the backend named by ``database_url``.

    Supported today: ``sqlite:///<path>`` (a local SQLite file). An unsupported
    scheme raises :class:`ValueError`.
    """
    if database_url.startswith(_SQLITE_PREFIX):
        return SqliteBackend(Path(database_url[len(_SQLITE_PREFIX) :]))
    scheme = database_url.split("://", 1)[0]
    raise ValueError(f"unsupported database url scheme: {scheme!r}")
