# elan-ng

A cross-platform reimplementation of [ELAN](https://archive.mpi.nl/tla/elan), the annotation tool for time-aligning transcriptions and annotations to audio and video. "elan-ng" is a working name. The project is not affiliated with the Max Planck Institute for Psycholinguistics.

The design and specification are in [REIMPLEMENTATION.md](REIMPLEMENTATION.md).

**Status: M0 (skeleton).** The app opens an empty main window with ELAN's full menu layout. Menu items that later milestones will implement are shown disabled, with the planned milestone in the tooltip.

## Requirements

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/) 0.5 or later (it installs the pinned dependencies from `uv.lock`)
- Windows 10/11 x64, macOS 12+ (Intel or Apple Silicon) or 64-bit Linux

## Run from source

All commands are run from this `elan/` folder.

### macOS and Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
uv sync
```

```bash
uv run elan-ng
```

On Linux, Qt needs a few system libraries that most desktops already have. On a minimal Debian/Ubuntu install:

```bash
sudo apt-get install libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libdbus-1-3 libfontconfig1
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync
uv run elan-ng
```

## Development

```bash
uv run pytest
```

```bash
uv run ruff check . && uv run ruff format --check .
```

```bash
uv run mypy
```

```bash
uv run lint-imports
```

`lint-imports` checks the layering rules from REIMPLEMENTATION.md §4.4: `elan_ng.core` must not import Qt, PyAV or any other elan-ng layer.

`uv run elan-ng --self-test` starts the app without a visible window, checks the main window, and exits. CI runs it on the packaged app.

## Packaging

```bash
uv run python packaging/build.py
```

This builds a standalone app with PyInstaller into `dist/` (`dist/elan-ng/` on Windows and Linux, `dist/elan-ng.app` on macOS) and runs its self-test. The installers (signed `.msi`, notarized `.dmg`, AppImage) come in a later milestone.

## Continuous integration

`.github/workflows/elan.yml` (at the repository root) runs lint, type checks, the import contract and the tests on Ubuntu, Windows, macOS on Apple Silicon and macOS on Intel. It then builds the packaged app on each OS and runs its self-test. It only runs when files under `elan/` change.
