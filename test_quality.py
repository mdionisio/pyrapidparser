"""Static quality checks: strict type checking (mypy) and code formatting (ruff).

Both tools read their configuration from pyproject.toml.
To fix a formatting failure run ``hatch run format``.
"""

import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_tool(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [sys.executable, "-m", *args], cwd=PROJECT_DIR, capture_output=True, text=True
    )


def test_mypy_strict() -> None:
    result = run_tool("mypy")
    assert result.returncode == 0, result.stdout + result.stderr


def test_ruff_format() -> None:
    result = run_tool("ruff", "format", "--check", "--diff")
    assert result.returncode == 0, result.stdout + result.stderr
