"""Base classes for the small remembered-preference stores.

Every remembered setting persists one versioned JSON object under a fixed string
``key`` in the shared :class:`~app.storage.backend.StorageBackend`. This base
gives them a uniform :meth:`reset` (delete the row, restoring defaults on next
load) and a human-readable :attr:`label`, so the "Remembered settings" command
can list and reset them without a hardcoded table.
"""

from __future__ import annotations

from dataclasses import asdict, fields, replace
from enum import Enum
from typing import Any, Generic, TypeVar

from app.storage.backend import StorageBackend

S = TypeVar("S")  # a frozen dataclass of JSON-friendly values


class RecordStore:
    """A config store persisted as one row in the shared storage backend."""

    LABEL = "setting"

    def __init__(self, backend: StorageBackend, key: str) -> None:
        self._backend = backend
        self._key = key

    @property
    def label(self) -> str:
        """Human-readable name shown in the Remembered-settings command."""
        return self.LABEL

    def reset(self) -> None:
        """Forget the remembered value by deleting its row (no-op if absent)."""
        self._backend.delete_setting(self._key)


class SettingsRecordStore(RecordStore, Generic[S]):
    """Shared versioned load/save for stores persisting one frozen dataclass.

    Subclasses set :attr:`LABEL` and :attr:`VERSION` and pass their default
    instance. :meth:`load` coerces each stored value to the type of the matching
    default field, so a hand-edited or stale row degrades to the defaults instead
    of crashing; :meth:`save` persists the plain ``asdict`` shape.
    """

    VERSION = 1

    def __init__(self, backend: StorageBackend, key: str, default: S) -> None:
        super().__init__(backend, key)
        self._default = default

    def load(self) -> S:
        """Return the stored settings, or defaults if absent/corrupt."""
        raw = self._backend.get_versioned(self._key, self.VERSION)
        if raw is None:
            return self._default
        default: Any = self._default
        changes = {
            field.name: _coerce(getattr(default, field.name), raw[field.name])
            for field in fields(default)
            if field.name in raw
        }
        result: S = replace(default, **changes)
        return result

    def save(self, settings: S) -> None:
        value: Any = settings
        self._backend.set_versioned(self._key, self.VERSION, asdict(value))


def _coerce(default_value: Any, raw: Any) -> Any:
    """Coerce ``raw`` to ``default_value``'s type (unknown enum -> the default)."""
    # Order matters: StrEnum members are str instances, bool is an int subclass.
    if isinstance(default_value, Enum):
        try:
            return type(default_value)(raw)
        except ValueError:
            return default_value
    if isinstance(default_value, bool):
        return bool(raw)
    if isinstance(default_value, int):
        return int(raw)
    if isinstance(default_value, float):
        return float(raw)
    if isinstance(default_value, str):
        return str(raw)
    if isinstance(default_value, tuple):
        return tuple(raw)
    return raw
