"""Keyboard-shortcut persistence, backed by this app's storage engine.

The merge/mutation logic (:class:`KeyMap`, :class:`KeyOverride`, ``merge_keymap``,
``assign``, ``remove_command``, ``remove_chord``) and the full editor UI now live
in the extracted ``command_palette`` library (:class:`~command_palette.state.KeymapState`,
``open_shortcut_editor``) — re-exported here so every existing import path
(``from app.config.key_bindings import ...``) keeps working unchanged.

:class:`KeyBindingStore` is now purely an *adapter*: it satisfies the library's
``Store`` protocol (``read``/``write``) by delegating to this app's
:class:`~app.storage.backend.StorageBackend`, so a ``KeymapState`` built over it
persists through this app's storage engine instead of the library's own
``JsonStore``. It stays a :class:`~app.config.record_store.RecordStore` too, so
"Remembered settings" can still reset it by label.
"""

from __future__ import annotations

from typing import Any

from command_palette.keymap import DefaultPair as DefaultPair
from command_palette.keymap import KeyMap as KeyMap
from command_palette.keymap import KeyOverride as KeyOverride
from command_palette.keymap import assign as assign
from command_palette.keymap import merge_keymap as merge_keymap
from command_palette.keymap import remove_chord as remove_chord
from command_palette.keymap import remove_command as remove_command

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

KEY_BINDINGS_VERSION = 1
KEY_BINDINGS_KEY = "key_bindings"


class KeyBindingStore(RecordStore):
    """Adapts this app's ``StorageBackend`` to the library's ``Store`` protocol."""

    LABEL = "Keyboard shortcuts"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, KEY_BINDINGS_KEY)

    def read(self, key: str) -> dict[str, Any] | None:
        """``Store`` protocol: the stored JSON object for ``key``, or ``None``."""
        return self._backend.get_versioned(key, KEY_BINDINGS_VERSION)

    def write(self, key: str, value: dict[str, Any]) -> None:
        """``Store`` protocol: upsert ``value`` for ``key``."""
        self._backend.set_versioned(key, KEY_BINDINGS_VERSION, value)
