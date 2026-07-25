"""Effective keyboard map: built-in defaults overlaid by chord-keyed overrides.

The merge/mutation logic (:class:`KeyMap`, :class:`KeyOverride`, ``merge_keymap``,
``assign``, ``remove_command``, ``remove_chord``) now lives in the extracted
``command_palette`` library — re-exported here so every existing import path
(``from app.config.key_bindings import ...``) keeps working unchanged. Only the
sqlite-backed store stays app-specific, since it persists through this app's
:class:`~app.storage.backend.StorageBackend` rather than the library's own
``Store`` protocol.
"""

from __future__ import annotations

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


def effective_keymap(store: KeyBindingStore, defaults: list[DefaultPair]) -> KeyMap:
    """Load the stored overrides and merge them onto ``defaults`` (the live keymap)."""
    return merge_keymap(defaults, store.load())


class KeyBindingStore(RecordStore):
    """Reads and writes the chord-keyed override list via the storage backend."""

    LABEL = "Keyboard shortcuts"

    def __init__(self, backend: StorageBackend) -> None:
        super().__init__(backend, KEY_BINDINGS_KEY)

    def load(self) -> tuple[KeyOverride, ...]:
        """Return the stored overrides; ``()`` if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, KEY_BINDINGS_VERSION)
        if raw is None:
            return ()
        items = raw.get("overrides", [])
        if not isinstance(items, list):
            return ()
        return tuple(parsed for item in items if (parsed := _parse_override(item)) is not None)

    def save(self, overrides: tuple[KeyOverride, ...]) -> None:
        payload = {
            "overrides": [
                {"chord": override.chord, "command_id": override.command_id}
                for override in overrides
            ]
        }
        self._backend.set_versioned(self._key, KEY_BINDINGS_VERSION, payload)


def _parse_override(item: object) -> KeyOverride | None:
    """Deserialize one persisted override row, or ``None`` if malformed."""
    if not isinstance(item, dict):
        return None
    chord = item.get("chord")
    command_id = item.get("command_id")
    if not isinstance(chord, str):
        return None
    if command_id is not None and not isinstance(command_id, str):
        return None
    return KeyOverride(chord, command_id)
