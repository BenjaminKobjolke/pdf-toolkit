"""Unit tests for the OCR provider seam (no real WinRT engine)."""

from __future__ import annotations

import importlib.machinery
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from app.ocr.provider import (
    OcrError,
    OcrLanguage,
    OcrProvider,
    WindowsOcrProvider,
    default_provider,
)

if TYPE_CHECKING:
    from tests.conftest import MakeImage


class _FakeEngine:
    def __init__(self, text: str) -> None:
        self._text = text

    async def recognize_async(self, _bitmap: object) -> SimpleNamespace:
        return SimpleNamespace(text=self._text)


class _FakeWinrt:
    """Installs fake winrt.windows.* modules and records engine selection."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, text: str = "fake text") -> None:
        self.created_from: list[str | None] = []
        self.engine: _FakeEngine | None = _FakeEngine(text)
        fake = self

        class _OcrEngine:
            available_recognizer_languages = [
                SimpleNamespace(language_tag="de-DE", display_name="German (Germany)"),
                SimpleNamespace(language_tag="en-US", display_name="English (United States)"),
            ]

            @staticmethod
            def try_create_from_user_profile_languages() -> _FakeEngine | None:
                fake.created_from.append(None)
                return fake.engine

            @staticmethod
            def try_create_from_language(language: object) -> _FakeEngine | None:
                fake.created_from.append(getattr(language, "tag", None))
                return fake.engine

        modules: dict[str, dict[str, object]] = {
            "winrt.windows.media.ocr": {"OcrEngine": _OcrEngine},
            "winrt.windows.globalization": {"Language": lambda tag: SimpleNamespace(tag=tag)},
            "winrt.windows.graphics.imaging": {
                "SoftwareBitmap": SimpleNamespace(
                    create_copy_from_buffer=lambda *_a, **_k: object()
                ),
                "BitmapPixelFormat": SimpleNamespace(RGBA8=87),
            },
            "winrt.windows.storage.streams": {
                "DataWriter": lambda: SimpleNamespace(
                    write_bytes=lambda _b: None, detach_buffer=lambda: object()
                )
            },
        }
        for name, attrs in modules.items():
            module = ModuleType(name)
            # find_spec on an already-imported module reads __spec__; a bare
            # ModuleType has none and would raise ValueError.
            module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
            for attr, value in attrs.items():
                setattr(module, attr, value)
            monkeypatch.setitem(sys.modules, name, module)


def test_default_provider_is_windows_provider() -> None:
    provider = default_provider()
    assert isinstance(provider, WindowsOcrProvider)
    assert isinstance(provider, OcrProvider)


def test_unavailable_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    assert WindowsOcrProvider().is_available() is False


def test_unavailable_without_winrt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ocr.provider.importlib.util.find_spec", lambda _name: None)
    assert WindowsOcrProvider().is_available() is False


def test_recognize_auto_uses_profile_engine(
    monkeypatch: pytest.MonkeyPatch, make_image: MakeImage
) -> None:
    fake = _FakeWinrt(monkeypatch, "hello world")
    assert WindowsOcrProvider().recognize(make_image("png")) == "hello world"
    assert fake.created_from == [None]


def test_recognize_with_language_uses_language_engine(
    monkeypatch: pytest.MonkeyPatch, make_image: MakeImage
) -> None:
    fake = _FakeWinrt(monkeypatch, "hallo welt")
    assert WindowsOcrProvider().recognize(make_image("png"), "de-DE") == "hallo welt"
    assert fake.created_from == ["de-DE"]


def test_missing_language_pack_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch, make_image: MakeImage
) -> None:
    fake = _FakeWinrt(monkeypatch)
    fake.engine = None
    with pytest.raises(OcrError):
        WindowsOcrProvider().recognize(make_image("png"), "xx-XX")


def test_recognize_unreadable_file_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _FakeWinrt(monkeypatch)
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not an image")
    with pytest.raises(OcrError):
        WindowsOcrProvider().recognize(broken)


def test_available_languages_maps_tag_and_display_name(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeWinrt(monkeypatch)
    assert WindowsOcrProvider().available_languages() == [
        OcrLanguage(tag="de-DE", display_name="German (Germany)"),
        OcrLanguage(tag="en-US", display_name="English (United States)"),
    ]
