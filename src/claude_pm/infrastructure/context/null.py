"""Null context provider — used when no vault is configured."""

from __future__ import annotations


class NullContext:
    """Implements ContextProvider as a no-op (no enrichment)."""

    def is_available(self) -> bool:
        return False

    def get_status_excerpt(self, repo_name: str, max_chars: int = 1500) -> str | None:
        return None
