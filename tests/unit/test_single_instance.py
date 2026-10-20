"""Unit tests for the single-instance sender's failure paths.

Successful delivery is inherently cross-process (a Qt local-socket server only
accepts on its own event loop) and is covered by
``tests/integration/test_single_instance_ipc.py`` with a real subprocess sender.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtNetwork import QLocalSocket

from app.gui import single_instance
from app.gui.single_instance import InstanceServer, try_send_to_running


def _unique_name() -> str:
    return f"pdft-test-{uuid.uuid4().hex}"


def test_send_without_server_returns_false(qapp: object) -> None:
    assert try_send_to_running(Path("x.pdf"), name=_unique_name()) is False


def test_send_after_stop_returns_false(qapp: object) -> None:
    name = _unique_name()
    server = InstanceServer(lambda _p: None, name=name)
    assert server.start() is True
    server.stop()
    assert try_send_to_running(Path("x.pdf"), name=name) is False


def test_start_twice_on_same_name_still_works(qapp: object) -> None:
    """A second start() on the same pipe name (stale-pipe path) succeeds."""
    name = _unique_name()
    first = InstanceServer(lambda _p: None, name=name)
    assert first.start() is True
    first.stop()
    second = InstanceServer(lambda _p: None, name=name)
    assert second.start() is True
    second.stop()


def test_dispatch_preserves_whitespace_in_forwarded_path() -> None:
    received: list[Path | None] = []
    server = InstanceServer(received.append)

    server._dispatch(bytearray(b" leading and trailing.pdf "))

    assert received == [Path(" leading and trailing.pdf ")]


def test_send_succeeds_when_wait_drains_pending_bytes(
    monkeypatch: object,
) -> None:
    socket = MagicMock(spec=QLocalSocket)
    socket.waitForConnected.return_value = True
    socket.write.return_value = len(str(Path("x.pdf")).encode("utf-8"))
    socket.bytesToWrite.side_effect = [4, 0]
    socket.waitForBytesWritten.return_value = False
    socket.state.return_value = QLocalSocket.LocalSocketState.UnconnectedState
    socket_factory = MagicMock(spec=QLocalSocket)
    socket_factory.return_value = socket
    socket_factory.LocalSocketState = QLocalSocket.LocalSocketState
    monkeypatch.setattr(single_instance, "QLocalSocket", socket_factory)  # type: ignore[attr-defined]

    assert try_send_to_running(Path("x.pdf"), name="existing-viewer") is True
