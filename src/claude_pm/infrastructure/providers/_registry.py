"""Provider registry — maps provider name → factory.

To add a new provider (GitHub, Jira, Notion, ...):
    1. Implement the IssueProvider Protocol in pm/infrastructure/providers/<name>.py
    2. Register it here: PROVIDERS["<name>"] = <ClassName>
    3. Document setup in README

See CONTRIBUTING.md for details.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...domain.ports import IssueProvider
from ...exceptions import ConfigError
from .linear import LinearProvider

PROVIDERS: dict[str, Callable[..., IssueProvider]] = {
    "linear": LinearProvider,
}


def get_provider(name: str, **kwargs: Any) -> IssueProvider:
    """Instantiate a provider by name. kwargs are forwarded to its constructor."""
    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS)) or "(none)"
        raise ConfigError(
            f"Unknown provider '{name}'. Available: {available}. "
            f"See CONTRIBUTING.md to add a new provider."
        )
    return PROVIDERS[name](**kwargs)
