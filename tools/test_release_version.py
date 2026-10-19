"""Isolated check of the build -> publish version handoff (no real build/upload).

Copies the real build_release.bat / publish_release.bat / release_create.bat into a
temp project and replaces python, uv, makensis, build_exe and the uploader with
fakes. Run from the project root:  python tools/test_release_version.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REAL_BATS = ("build_release.bat", "publish_release.bat", "release_create.bat")

# build_release.bat runs `python -m pytest` without `call`, so python must be a real
# exe: a --without-pip venv on PATH, with these fake modules first on PYTHONPATH.
FAKE_MODULES = {
    "pytest.py": "",
    "app/__init__.py": "",
    "app/release/__init__.py": "",
    "app/release/release_info.py": "import os\nprint(os.environ['FAKE_LABEL'])\n",
}
FAKES = {
    # presign step: `uv run ... presign_exe.py`
    "uv.bat": "@echo off\r\nexit /b 0\r\n",
    "makensis.bat": (
        '@echo off\r\nif "%FAKE_NSIS_FAIL%"=="1" exit /b 1\r\n'
        '> "%~dp1..\\releases\\windows\\installer.exe" echo installer %FAKE_LABEL%\r\nexit /b 0\r\n'
    ),
    "fake_upload.bat": (
        '@echo off\r\n>> "%FAKE_LOG%" echo ARGS %*\r\n'
        'type %1 >> "%FAKE_LOG%"\r\nexit /b %FAKE_UPLOAD_EXIT%\r\n'
    ),
}
FAKE_BUILD_EXE = (
    '@echo off\r\nmkdir "%~dp0..\\dist\\FastFileViewer" 2>nul\r\n'
    '> "%~dp0..\\dist\\FastFileViewer\\FastFileViewer.exe" echo exe\r\nexit /b 0\r\n'
)


class Workspace:
    def __init__(self, base: Path) -> None:
        self.root = base / "proj"
        self.tools = self.root / "tools"
        self.bin = base / "bin"
        self.modules = base / "modules"
        self.py_scripts = base / "py" / "Scripts"
        self.log = base / "upload.log"
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(base / "py")], check=True
        )
        for rel, body in FAKE_MODULES.items():
            (self.modules / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.modules / rel).write_text(body, encoding="ascii")
        for d in (self.tools, self.bin, self.root / ".venv" / "Scripts", self.root / "installer"):
            d.mkdir(parents=True)
        for name in REAL_BATS:
            shutil.copy(TOOLS / name, self.tools / name)
        for name, body in FAKES.items():
            (self.bin / name).write_text(body, encoding="ascii")
        (self.tools / "build_exe.bat").write_text(FAKE_BUILD_EXE, encoding="ascii")
        (self.root / ".venv" / "Scripts" / "activate.bat").write_text(
            "@echo off\r\n", encoding="ascii"
        )
        (self.root / "installer" / "installer.nsi").write_text("", encoding="ascii")
        (self.tools / "publish_settings.ini").write_text("[FTP]\n", encoding="ascii")
        self.record = self.root / "releases" / "windows" / "release_version.txt"

    def run(self, bat: str, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        full_env = {
            **os.environ,
            "PATH": f"{self.bin};{self.py_scripts};{os.environ['PATH']}",
            "PYTHONPATH": str(self.modules),
            "FAKE_LOG": str(self.log),
            "FAKE_UPLOAD_EXIT": "0",
            "FAKE_NSIS_FAIL": "0",
            "RELEASE_TOOL_CMD": str(self.bin / "fake_upload.bat"),
            **env,
        }
        full_env.pop("TICKETS_WATCHER_COMMAND_RUN", None)
        return subprocess.run(
            ["cmd", "/c", str(self.tools / bat), *args],
            # cwd outside the repo: `python -m app...` must resolve to the fakes.
            cwd=self.modules.parent,
            env=full_env,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )

    def uploads(self) -> str:
        return self.log.read_text() if self.log.exists() else ""

    def recorded(self) -> str | None:
        return self.record.read_text().strip() if self.record.exists() else None


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(Path(tmp))

        # Build completes and records its label.
        assert ws.run("build_release.bat", FAKE_LABEL="0.2.0_5").returncode == 0
        assert ws.recorded() == "0.2.0_5"

        # Source counter moves on; publish still ships the completed build.
        (ws.tools / "previous_version.txt").write_text("0.2.0_4\n")
        r = ws.run("publish_release.bat", FAKE_LABEL="0.2.0_6")
        assert r.returncode == 0, r.stdout + r.stderr
        log = ws.uploads()
        assert "installer 0.2.0_5" in log and '--previous-version "0.2.0_4"' in log, log

        # Failed build of a NEW label keeps the old record (its artifact survives).
        assert ws.run("build_release.bat", FAKE_LABEL="0.2.0_6", FAKE_NSIS_FAIL="1").returncode != 0
        assert ws.recorded() == "0.2.0_5"

        # Explicit %2 ships an older build; %1 overrides previous_version.txt.
        ws.log.unlink()
        assert ws.run("build_release.bat", FAKE_LABEL="0.2.0_6").returncode == 0
        r = ws.run("publish_release.bat", "0.2.0_3", "0.2.0_5")
        assert r.returncode == 0 and "installer 0.2.0_5" in ws.uploads(), r.stdout
        assert '--previous-version "0.2.0_3"' in ws.uploads()

        # Uploader failure propagates through publish.
        assert ws.run("publish_release.bat", FAKE_UPLOAD_EXIT="3").returncode == 3

        # Failed rebuild of the recorded label invalidates it; publish stops pre-upload.
        assert ws.run("build_release.bat", FAKE_LABEL="0.2.0_6", FAKE_NSIS_FAIL="1").returncode != 0
        assert ws.recorded() is None
        ws.log.unlink()
        assert ws.run("publish_release.bat").returncode != 0
        assert ws.uploads() == ""

        # Explicit label whose installer is missing stops pre-upload.
        assert ws.run("publish_release.bat", "0.2.0_4", "9.9.9_9").returncode != 0
        assert ws.uploads() == ""

        # Launcher preflight: missing publish config fails before release-tool runs.
        (ws.tools / "publish_settings.ini").unlink()
        r = ws.run("release_create.bat", "--dry-run")
        assert (
            r.returncode == 1 and "publish_settings.ini" in r.stdout and "is missing" in r.stdout
        ), r.stdout

    print("release version handoff: OK")


if __name__ == "__main__":
    sys.exit(main())
