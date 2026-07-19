"""Single-instance IPC: forward a file path to an already-running viewer.

A running viewer listens on a local socket (a named pipe on Windows). A second
launch connects, writes the path to open (empty payload = "just activate the
window"), and exits. Every failure path returns ``False`` so the caller falls
back to starting a normal standalone instance — this module must never be the
reason a file fails to open.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket

from app.app_logger import log

SERVER_NAME = "pdf-toolkit-viewer"
CONNECT_TIMEOUT_MS = 300
ASFW_ANY = -1  # AllowSetForegroundWindow: grant to any process


def _allow_foreground_transfer() -> None:
    """Let the running viewer take focus when it receives our message.

    Windows only allows the *foreground* process to call SetForegroundWindow;
    the receiving viewer is background, so its raise/activate would only flash
    the taskbar. This launching process *is* foreground-eligible (the user just
    started it), so it hands that right over before forwarding.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
    except (AttributeError, OSError):  # pragma: no cover - defensive, never fatal
        log.debug("single-instance: AllowSetForegroundWindow failed", exc_info=True)


def try_send_to_running(
    path: Path | None,
    *,
    name: str = SERVER_NAME,
    timeout_ms: int = CONNECT_TIMEOUT_MS,
) -> bool:
    """Forward ``path`` (or an activate-only ping when ``None``) to a running viewer.

    ``True`` only when a server accepted the message; any failure means the
    caller should continue starting up as a normal standalone instance.
    """
    _allow_foreground_transfer()
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(timeout_ms):
        log.debug("single-instance: no running viewer (%s)", socket.errorString())
        return False
    payload = str(path).encode("utf-8") if path is not None else b""
    socket.write(payload)
    socket.flush()
    # flush() may drain synchronously; waitForBytesWritten returns False when
    # there is nothing left to write, so only wait while bytes are pending.
    ok = socket.bytesToWrite() == 0 or bool(socket.waitForBytesWritten(timeout_ms))
    socket.disconnectFromServer()
    if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
        socket.waitForDisconnected(timeout_ms)
    if ok:
        log.info("single-instance: forwarded %s to running viewer", path or "<activate>")
    return ok


class InstanceServer:
    """Listens for forwarded paths; ``on_open(None)`` means activate only.

    EOF (client disconnect) delimits a message, so no framing protocol is
    needed. The callback runs on the GUI thread and is exception-guarded so a
    bad path can never kill the event loop.
    """

    def __init__(self, on_open: Callable[[Path | None], None], *, name: str = SERVER_NAME) -> None:
        self._on_open = on_open
        self._name = name
        self._server = QLocalServer()
        self._server.newConnection.connect(self._accept)

    def start(self) -> bool:
        """Begin listening. Retries once past a stale pipe left by a crash."""
        if self._server.listen(self._name):
            return True
        QLocalServer.removeServer(self._name)
        if self._server.listen(self._name):
            return True
        log.debug("single-instance: listen failed: %s", self._server.errorString())
        return False

    def stop(self) -> None:
        self._server.close()

    def _accept(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        buffer = bytearray()
        socket.readyRead.connect(lambda: buffer.extend(socket.readAll().data()))
        socket.disconnected.connect(lambda: self._dispatch(socket, buffer))

    def _dispatch(self, socket: QLocalSocket, buffer: bytearray) -> None:
        buffer.extend(socket.readAll().data())  # drain anything readyRead missed
        socket.deleteLater()
        text = buffer.decode("utf-8", errors="replace").strip()
        try:
            self._on_open(Path(text) if text else None)
        except Exception:
            log.exception("single-instance: open callback failed for %r", text)
