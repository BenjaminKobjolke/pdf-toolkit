"""Contract tests for :class:`SqliteBackend` (the default storage backend).

These exercise the :class:`~app.storage.backend.StorageBackend` surface every
config store depends on, so a future backend (MySQL, …) can be run against the
same expectations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.storage.factory import make_backend
from app.storage.sqlite_backend import SqliteBackend


@pytest.fixture
def backend(tmp_path: Path) -> SqliteBackend:
    return SqliteBackend(tmp_path / "pdf-toolkit.db")


# --- settings (one versioned JSON object per key) ---------------------------


def test_set_then_get_roundtrips_payload(backend: SqliteBackend) -> None:
    backend.set_versioned("zoom", 1, {"fit": False, "percent": 150})
    assert backend.get_versioned("zoom", 1) == {
        "version": 1,
        "fit": False,
        "percent": 150,
    }


def test_get_missing_key_returns_none(backend: SqliteBackend) -> None:
    assert backend.get_versioned("absent", 1) is None


def test_set_upserts_existing_key(backend: SqliteBackend) -> None:
    backend.set_versioned("zoom", 1, {"percent": 100})
    backend.set_versioned("zoom", 1, {"percent": 200})
    assert backend.get_versioned("zoom", 1) == {"version": 1, "percent": 200}


def test_get_with_wrong_version_returns_none(backend: SqliteBackend) -> None:
    backend.set_versioned("zoom", 1, {"percent": 100})
    assert backend.get_versioned("zoom", 2) is None


def test_delete_setting_removes_key(backend: SqliteBackend) -> None:
    backend.set_versioned("zoom", 1, {"percent": 100})
    backend.delete_setting("zoom")
    assert backend.get_versioned("zoom", 1) is None


def test_delete_missing_setting_is_noop(backend: SqliteBackend) -> None:
    backend.delete_setting("absent")  # must not raise


def test_get_corrupt_value_returns_none(backend: SqliteBackend) -> None:
    # A row whose value is not valid JSON degrades to None (logged, not raised),
    # so every store falls back to its defaults instead of crashing.
    backend._conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("zoom", "{ not json"))
    backend._conn.commit()
    assert backend.get_versioned("zoom", 1) is None


# --- per-document rows (the scaling table) ----------------------------------


def test_put_then_get_document_roundtrips_scalar(backend: SqliteBackend) -> None:
    backend.put_document("page", "C:/a.pdf", 3)
    assert backend.document_value("page", "C:/a.pdf") == 3


def test_put_then_get_document_roundtrips_object(backend: SqliteBackend) -> None:
    backend.put_document("zoom", "C:/a.pdf", {"fit": True, "percent": 100})
    assert backend.document_value("zoom", "C:/a.pdf") == {"fit": True, "percent": 100}


def test_document_value_missing_returns_none(backend: SqliteBackend) -> None:
    assert backend.document_value("zoom", "C:/missing.pdf") is None


def test_put_document_upserts(backend: SqliteBackend) -> None:
    backend.put_document("page", "C:/a.pdf", 1)
    backend.put_document("page", "C:/a.pdf", 9)
    assert backend.document_value("page", "C:/a.pdf") == 9


def test_namespaces_are_independent(backend: SqliteBackend) -> None:
    backend.put_document("zoom", "C:/a.pdf", {"percent": 150})
    backend.put_document("page", "C:/a.pdf", 4)
    assert backend.document_value("zoom", "C:/a.pdf") == {"percent": 150}
    assert backend.document_value("page", "C:/a.pdf") == 4


def test_delete_document_removes_one_row(backend: SqliteBackend) -> None:
    backend.put_document("page", "C:/a.pdf", 1)
    backend.put_document("page", "C:/b.pdf", 2)
    backend.delete_document("page", "C:/a.pdf")
    assert backend.document_value("page", "C:/a.pdf") is None
    assert backend.document_value("page", "C:/b.pdf") == 2


def test_clear_namespace_drops_only_that_namespace(backend: SqliteBackend) -> None:
    backend.put_document("page", "C:/a.pdf", 1)
    backend.put_document("page", "C:/b.pdf", 2)
    backend.put_document("zoom", "C:/a.pdf", {"percent": 150})
    backend.clear_namespace("page")
    assert backend.document_value("page", "C:/a.pdf") is None
    assert backend.document_value("page", "C:/b.pdf") is None
    assert backend.document_value("zoom", "C:/a.pdf") == {"percent": 150}


# --- durability / lifecycle -------------------------------------------------


def test_data_persists_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "pdf-toolkit.db"
    first = SqliteBackend(path)
    first.set_versioned("zoom", 1, {"percent": 150})
    first.put_document("page", "C:/a.pdf", 7)
    first.close()

    second = SqliteBackend(path)
    assert second.get_versioned("zoom", 1) == {"version": 1, "percent": 150}
    assert second.document_value("page", "C:/a.pdf") == 7
    second.close()


def test_fresh_db_creates_parent_dirs(tmp_path: Path) -> None:
    backend = SqliteBackend(tmp_path / "nested" / "deep" / "pdf-toolkit.db")
    assert backend.get_versioned("anything", 1) is None  # schema ready, empty


def test_make_backend_returns_sqlite_for_sqlite_url(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'pdf-toolkit.db'}"
    backend = make_backend(url)
    assert isinstance(backend, SqliteBackend)
    backend.set_versioned("zoom", 1, {"percent": 100})
    assert backend.get_versioned("zoom", 1) == {"version": 1, "percent": 100}


def test_make_backend_rejects_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        make_backend("mysql://user:pass@host/db")
