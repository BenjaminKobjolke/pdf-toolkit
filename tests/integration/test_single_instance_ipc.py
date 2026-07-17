"""Cross-process integration tests for single-instance forwarding.

A real subprocess plays the second launch: it connects to this process's
``InstanceServer`` and forwards a path, exactly as ``FastFileViewer.bat``
would. The parent pumps its event loop while waiting — a Qt local-socket
server only accepts connections on event-loop ticks.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.gui.single_instance import InstanceServer

REPO_ROOT = Path(__file__).resolve().parents[2]

_SEND_SCRIPT = """
import sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication
app = QCoreApplication([])
from app.gui.single_instance import try_send_to_running
name, arg = sys.argv[1], sys.argv[2]
ok = try_send_to_running(Path(arg) if arg else None, name=name)
sys.exit(0 if ok else 1)
"""


def _send_from_subprocess(qapp: object, name: str, path: Path | None) -> bool:
    """Run try_send_to_running in a child process while pumping our event loop."""
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    proc = subprocess.Popen(
        [sys.executable, "-c", _SEND_SCRIPT, name, str(path) if path is not None else ""],
        env=env,
        cwd=REPO_ROOT,
    )
    deadline = time.monotonic() + 30
    while proc.poll() is None and time.monotonic() < deadline:
        qapp.processEvents()  # type: ignore[attr-defined]
    if proc.poll() is None:
        proc.kill()
        raise TimeoutError("subprocess sender did not finish")
    return proc.returncode == 0


def _pump_until_true(qapp: object, predicate: object, timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while not predicate() and time.monotonic() < deadline:  # type: ignore[operator]
        qapp.processEvents()  # type: ignore[attr-defined]
    return bool(predicate())  # type: ignore[operator]


@pytest.fixture
def server_name() -> str:
    return f"pdft-test-{uuid.uuid4().hex}"


@pytest.fixture
def received(qapp: object) -> list[Path | None]:
    return []


@pytest.fixture
def server(server_name: str, received: list[Path | None]) -> Iterator[InstanceServer]:
    server = InstanceServer(received.append, name=server_name)
    assert server.start() is True
    yield server
    server.stop()


def test_forwarded_path_reaches_callback(
    qapp: object, server_name: str, server: InstanceServer, received: list[Path | None]
) -> None:
    path = Path(r"C:\docs\some file.pdf")

    assert _send_from_subprocess(qapp, server_name, path) is True
    assert _pump_until_true(qapp, lambda: bool(received))
    assert received == [path]


def test_empty_send_means_activate_only(
    qapp: object, server_name: str, server: InstanceServer, received: list[Path | None]
) -> None:
    assert _send_from_subprocess(qapp, server_name, None) is True
    assert _pump_until_true(qapp, lambda: bool(received))
    assert received == [None]


def test_raising_callback_does_not_kill_server(qapp: object, server_name: str) -> None:
    received: list[Path | None] = []

    def flaky(path: Path | None) -> None:
        received.append(path)
        if len(received) == 1:
            raise RuntimeError("boom")

    server = InstanceServer(flaky, name=server_name)
    assert server.start() is True
    try:
        assert _send_from_subprocess(qapp, server_name, Path("a.pdf")) is True
        assert _pump_until_true(qapp, lambda: len(received) == 1)
        assert _send_from_subprocess(qapp, server_name, Path("b.pdf")) is True
        assert _pump_until_true(qapp, lambda: len(received) == 2)
        assert received[1] == Path("b.pdf")
    finally:
        server.stop()
