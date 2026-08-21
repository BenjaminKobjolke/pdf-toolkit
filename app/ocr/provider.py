"""The OCR provider seam and its first implementation (Windows built-in OCR).

``OcrProvider`` is the abstraction future engines (Tesseract, cloud, …) plug
into; ``default_provider`` is the single place callers get the active engine
from, so swapping or configuring engines later touches one function.

The Windows implementation talks to ``Windows.Media.Ocr`` directly through the
winrt projection packages (PIL RGBA bytes → SoftwareBitmap → ``recognize_async``)
so it can use both engine modes: a specific installed language pack, or the
automatic pick from the user's Windows profile languages.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from app.app_logger import log


class OcrError(RuntimeError):
    """Single error surface for OCR failures (unreadable image, engine error)."""


@dataclass(frozen=True)
class OcrLanguage:
    """One installed recognition language of an engine."""

    tag: str
    display_name: str


class OcrProvider(ABC):
    """Extracts text from an image file on disk."""

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this engine can run on the current system."""

    @abstractmethod
    def recognize(self, image_path: Path, language: str | None = None) -> str:
        """Recognize ``image_path`` in ``language`` (``None``/empty = automatic).

        Raises :class:`OcrError` on unreadable images or engine failures.
        """

    @abstractmethod
    def available_languages(self) -> list[OcrLanguage]:
        """The languages this engine can recognize (empty when unavailable)."""


class WindowsOcrProvider(OcrProvider):
    """Windows built-in OCR (``Windows.Media.Ocr`` via the winrt projections)."""

    def is_available(self) -> bool:
        return (
            sys.platform == "win32"
            and importlib.util.find_spec("winrt.windows.media.ocr") is not None
        )

    def available_languages(self) -> list[OcrLanguage]:
        if not self.is_available():
            return []
        from winrt.windows.media.ocr import OcrEngine

        return [
            OcrLanguage(tag=lang.language_tag, display_name=lang.display_name)
            for lang in OcrEngine.available_recognizer_languages
        ]

    def recognize(self, image_path: Path, language: str | None = None) -> str:
        try:
            with Image.open(image_path) as img:
                rgba = img.convert("RGBA")
                data, width, height = rgba.tobytes(), rgba.width, rgba.height
        except Exception as err:
            log.warning("OCR could not read %s: %s", image_path, err)
            raise OcrError(str(err)) from err
        engine = self._engine(language)
        try:
            return asyncio.run(_recognize_bytes(engine, data, width, height))
        except Exception as err:
            log.warning("OCR failed for %s: %s", image_path, err)
            raise OcrError(str(err)) from err

    def _engine(self, language: str | None) -> Any:
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine

        try:
            if language:
                engine = OcrEngine.try_create_from_language(Language(language))
            else:
                engine = OcrEngine.try_create_from_user_profile_languages()
        except Exception as err:
            raise OcrError(str(err)) from err
        if engine is None:
            raise OcrError(f"no OCR engine for language '{language or 'auto'}'")
        return engine


async def _recognize_bytes(engine: Any, data: bytes, width: int, height: int) -> str:
    from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
    from winrt.windows.storage.streams import DataWriter

    writer = DataWriter()
    writer.write_bytes(data)
    bitmap = SoftwareBitmap.create_copy_from_buffer(
        writer.detach_buffer(), BitmapPixelFormat.RGBA8, width, height
    )
    result = await engine.recognize_async(bitmap)
    return str(result.text)


def default_provider() -> OcrProvider:
    """The engine the app uses; the one place to change when more engines exist."""
    return WindowsOcrProvider()
