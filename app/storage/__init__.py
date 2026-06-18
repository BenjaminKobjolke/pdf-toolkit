"""Pluggable persistence backends for remembered settings.

All config stores talk to a :class:`~app.storage.backend.StorageBackend` rather
than to files or a concrete database, so the storage engine can be swapped (today
SQLite; a MySQL/Postgres backend later) without touching any store.
"""
