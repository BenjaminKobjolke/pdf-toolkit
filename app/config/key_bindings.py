"""Effective keyboard map: built-in defaults overlaid by chord-keyed overrides.

Defaults are passed in (from :func:`app.gui.window_input.default_shortcut_pairs`)
so this config module never imports the GUI. A user override is keyed by *chord*:
a value reassigns/adds that chord to a command; ``None`` is a tombstone that
deletes the chord. This makes built-in defaults behave like ordinary, mutable
bindings while still letting brand-new defaults appear unless the user explicitly
removed them. Merge and mutations are pure and Qt-free (cf. ``order_ids`` in
:mod:`app.config.command_history`).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config.record_store import RecordStore
from app.storage.backend import StorageBackend

KEY_BINDINGS_VERSION = 1
KEY_BINDINGS_KEY = "key_bindings"

# A (chord, command_id) default binding pair, as produced by the GUI defaults.
DefaultPair = tuple[str, str]


@dataclass(frozen=True)
class KeyOverride:
    """One chord-keyed override. ``command_id=None`` is a tombstone (removed)."""

    chord: str
    command_id: str | None


@dataclass(frozen=True)
class KeyMap:
    """Effective chord->command_id bindings (chords unique), ordered for display."""

    bindings: tuple[tuple[str, str], ...]

    def command_for(self, chord: str) -> str | None:
        """Return the command bound to ``chord``, or ``None`` if unbound."""
        for bound_chord, command_id in self.bindings:
            if bound_chord == chord:
                return command_id
        return None

    def chords_for(self, command_id: str) -> tuple[str, ...]:
        """Return every chord bound to ``command_id``, in binding order."""
        return tuple(chord for chord, bound_id in self.bindings if bound_id == command_id)


def merge_keymap(defaults: list[DefaultPair], overrides: tuple[KeyOverride, ...]) -> KeyMap:
    """Overlay ``overrides`` onto ``defaults`` by chord (value sets, ``None`` deletes)."""
    effective: dict[str, str] = {}
    for chord, command_id in defaults:
        effective[chord] = command_id
    for override in overrides:
        if override.command_id is None:
            effective.pop(override.chord, None)
        else:
            effective[override.chord] = override.command_id
    return KeyMap(tuple(effective.items()))


def effective_keymap(store: KeyBindingStore, defaults: list[DefaultPair]) -> KeyMap:
    """Load the stored overrides and merge them onto ``defaults`` (the live keymap)."""
    return merge_keymap(defaults, store.load())


def assign(
    overrides: tuple[KeyOverride, ...], chord: str, command_id: str
) -> tuple[KeyOverride, ...]:
    """Upsert ``chord -> command_id`` (chords stay unique in the override layer)."""
    return _upsert(overrides, chord, command_id)


def remove_command(
    overrides: tuple[KeyOverride, ...], defaults: list[DefaultPair], command_id: str
) -> tuple[KeyOverride, ...]:
    """Tombstone every chord that currently maps to ``command_id``."""
    keymap = merge_keymap(defaults, overrides)
    result = overrides
    for chord in keymap.chords_for(command_id):
        result = _upsert(result, chord, None)
    return result


def remove_chord(overrides: tuple[KeyOverride, ...], chord: str) -> tuple[KeyOverride, ...]:
    """Tombstone a single chord (leaves the command's other chords intact)."""
    return _upsert(overrides, chord, None)


def _upsert(
    overrides: tuple[KeyOverride, ...], chord: str, command_id: str | None
) -> tuple[KeyOverride, ...]:
    kept = tuple(override for override in overrides if override.chord != chord)
    return (*kept, KeyOverride(chord, command_id))


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
