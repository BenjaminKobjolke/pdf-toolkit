"""Unit tests for per-document stores (via the zoom and page subclasses)."""

from __future__ import annotations

from pathlib import Path

from app.config.document_page import DocumentPageStore
from app.config.document_zoom import DocumentZoomStore
from app.config.zoom_settings import ZoomSettings
from app.storage.sqlite_backend import SqliteBackend


def _zoom(tmp_path: Path) -> DocumentZoomStore:
    return DocumentZoomStore(SqliteBackend(tmp_path / "db.sqlite"))


def _page(tmp_path: Path) -> DocumentPageStore:
    return DocumentPageStore(SqliteBackend(tmp_path / "db.sqlite"))


# --- value round-trip -------------------------------------------------------


def test_zoom_remember_then_value_for(tmp_path: Path) -> None:
    store = _zoom(tmp_path)
    store.remember(Path("a.pdf"), ZoomSettings(fit=False, percent=150))
    assert store.value_for(Path("a.pdf")) == ZoomSettings(fit=False, percent=150)


def test_page_remember_then_value_for(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.remember(Path("a.pdf"), 4)
    assert store.value_for(Path("a.pdf")) == 4


def test_value_for_missing_returns_none(tmp_path: Path) -> None:
    assert _zoom(tmp_path).value_for(Path("missing.pdf")) is None


def test_remember_upserts(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.remember(Path("a.pdf"), 1)
    store.remember(Path("a.pdf"), 9)
    assert store.value_for(Path("a.pdf")) == 9


def test_doc_key_is_normalized(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.remember(Path("a.pdf"), 3)
    # A different spelling that resolves to the same absolute path matches.
    assert store.value_for(Path("a.pdf").resolve()) == 3


# --- auto-all flag ----------------------------------------------------------


def test_auto_all_defaults_false(tmp_path: Path) -> None:
    assert _zoom(tmp_path).auto_all() is False


def test_set_auto_all_round_trips(tmp_path: Path) -> None:
    store = _zoom(tmp_path)
    store.set_auto_all(True)
    assert store.auto_all() is True
    store.set_auto_all(False)
    assert store.auto_all() is False


# --- forget / forget_all / reset --------------------------------------------


def test_forget_one_keeps_others_and_auto(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.set_auto_all(True)
    store.remember(Path("a.pdf"), 1)
    store.remember(Path("b.pdf"), 2)
    store.forget(Path("a.pdf"))
    assert store.value_for(Path("a.pdf")) is None
    assert store.value_for(Path("b.pdf")) == 2
    assert store.auto_all() is True


def test_forget_all_keeps_auto(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.set_auto_all(True)
    store.remember(Path("a.pdf"), 1)
    store.remember(Path("b.pdf"), 2)
    store.forget_all()
    assert store.value_for(Path("a.pdf")) is None
    assert store.value_for(Path("b.pdf")) is None
    assert store.auto_all() is True


def test_reset_clears_values_and_auto(tmp_path: Path) -> None:
    store = _page(tmp_path)
    store.set_auto_all(True)
    store.remember(Path("a.pdf"), 1)
    store.reset()
    assert store.value_for(Path("a.pdf")) is None
    assert store.auto_all() is False


def test_zoom_and_page_namespaces_independent(tmp_path: Path) -> None:
    backend = SqliteBackend(tmp_path / "db.sqlite")
    zoom = DocumentZoomStore(backend)
    page = DocumentPageStore(backend)
    zoom.remember(Path("a.pdf"), ZoomSettings(fit=False, percent=150))
    page.remember(Path("a.pdf"), 4)
    zoom.forget_all()
    assert zoom.value_for(Path("a.pdf")) is None
    assert page.value_for(Path("a.pdf")) == 4


def test_labels(tmp_path: Path) -> None:
    assert _zoom(tmp_path).label == "Remembered document zoom"
    assert _page(tmp_path).label == "Remembered document page"
