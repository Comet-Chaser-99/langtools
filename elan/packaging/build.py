"""Build a standalone elan-ng app with PyInstaller and run its self-test.

Usage (from the elan/ folder): uv run python packaging/build.py [--skip-self-test]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NAME = "elan-ng"


def built_executable() -> Path:
    if sys.platform == "darwin":
        return DIST / f"{NAME}.app" / "Contents" / "MacOS" / NAME
    suffix = ".exe" if sys.platform == "win32" else ""
    return DIST / NAME / f"{NAME}{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-self-test", action="store_true")
    args = parser.parse_args()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name",
            NAME,
            "--distpath",
            str(DIST),
            "--workpath",
            str(ROOT / "build"),
            "--specpath",
            str(ROOT / "build"),
            "--paths",
            str(ROOT / "src"),
            # Not used; leaving it out keeps the bundle smaller.
            "--exclude-module",
            "tkinter",
            str(ROOT / "packaging" / "entry.py"),
        ],
        check=True,
    )
    exe = built_executable()
    print(f"built {exe}")
    if args.skip_self_test:
        return 0
    result = subprocess.run([str(exe), "--self-test"], capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
