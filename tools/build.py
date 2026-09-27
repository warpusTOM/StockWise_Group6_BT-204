"""Release build for StockWise.

Usage (from the repo root, inside the build venv):

    python tools/build.py

Produces dist/StockWise.exe (single file, windowed, icon + version info).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CMD = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm", "--clean",
    "--onefile", "--windowed",
    "--name", "StockWise",
    "--icon", str(ROOT / "assets" / "icon.ico"),
    "--version-file", str(ROOT / "tools" / "version_info.txt"),
    # customtkinter ships data files (themes/assets) that must be bundled
    "--collect-all", "customtkinter",
    str(ROOT / "main.py"),
]


def main() -> None:
    print(" ".join(CMD))
    subprocess.run(CMD, cwd=ROOT, check=True)
    print("\nBuild complete -> dist/StockWise.exe")


if __name__ == "__main__":
    main()
