"""stdout/stderr setup helpers."""

from __future__ import annotations

import contextlib
import sys


def force_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8.

    Windows defaults to cp1252 which mangles em-dashes, accents, and emoji that
    appear in briefings and JSON output. Safe no-op on POSIX.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(Exception):
                reconfigure(encoding="utf-8", errors="replace")
