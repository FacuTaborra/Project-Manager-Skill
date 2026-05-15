"""Detect the current repo name from the cwd."""

from __future__ import annotations

from pathlib import Path

SESSION_FILE_NAME = ".claude-session-name"


def detect_repo_name() -> str:
    """Return the repo name from `.claude-session-name` if present, else the cwd basename."""
    cwd = Path.cwd()
    session_file = cwd / SESSION_FILE_NAME
    if session_file.is_file():
        try:
            name = session_file.read_text(encoding="utf-8").strip()
            if name:
                return name
        except OSError:
            pass
    return cwd.name
