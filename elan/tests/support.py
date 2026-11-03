"""Paths to test files."""

from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
DATA = TESTS / "data"
EXTERNAL = TESTS / "corpus" / "external"


def external(name: str) -> Path:
    path = EXTERNAL / name
    if not path.exists():
        pytest.skip(f"{name} not downloaded; run: uv run python tests/corpus/fetch.py")
    return path
