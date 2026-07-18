"""Sign an executable in place via release-tool's network-share PreSigner.

Reuses release_tool.pre_signer (copy to signing share, poll for signed copy,
verify signer CN, replace file in place). Must run in release-tool's env:

    uv run --project D:\\GIT\\BenjaminKobjolke\\release-tool python presign_exe.py \\
        <exe> <publish_settings.ini>
"""

import logging
import sys
from pathlib import Path

from release_tool.config import ReleaseConfig
from release_tool.exceptions import ReleaseToolError
from release_tool.pre_signer import PreSigner


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if len(sys.argv) != 3:
        print("Usage: presign_exe.py <exe-path> <publish_settings.ini>")
        return 2

    exe = Path(sys.argv[1])
    if not exe.is_file():
        print(f"File not found: {exe}")
        return 2

    config = ReleaseConfig.from_ini_file(Path(sys.argv[2]))
    if config.pre_sign is None:
        print("[PreSigning] is not enabled in the settings file.")
        return 1

    try:
        PreSigner(config.pre_sign).process(exe)
    except ReleaseToolError as e:
        print(f"Signing failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
