"""Shared helpers for command handlers — wiring + JSON serialization."""

from __future__ import annotations

import json
from typing import Any

from ..config import Config
from ..domain.models import Briefing, Issue
from ..domain.ports import ContextProvider, IssueProvider
from ..infrastructure.cache import Cache
from ..infrastructure.context.null import NullContext
from ..infrastructure.context.obsidian import ObsidianVaultContext
from ..infrastructure.providers._registry import get_provider


def build_provider(config: Config) -> IssueProvider:
    pak = config.require_pak()
    return get_provider(config.provider_name, api_key=pak)


def build_context(config: Config) -> ContextProvider:
    if config.vault_path is None:
        return NullContext()
    return ObsidianVaultContext(config.vault_path)


def load_cache(config: Config) -> Cache:
    return Cache.load(config.cache_path)


def issue_to_dict(issue: Issue) -> dict[str, Any]:
    return {
        "identifier": issue.identifier,
        "title": issue.title,
        "priority": issue.priority,
        "url": issue.url,
        "state": {"id": issue.state.id, "name": issue.state.name},
        "project": (
            {"id": issue.project.id, "name": issue.project.name} if issue.project else None
        ),
    }


def briefing_to_dict(briefing: Briefing) -> dict[str, Any]:
    return {
        "repo": briefing.repo,
        "project": briefing.project_name,
        "vault_available": briefing.vault_available,
        "vault_excerpt": briefing.vault_excerpt,
        "issues_by_state": {
            state: [issue_to_dict(i) for i in issues]
            for state, issues in briefing.issues_by_state.items()
        },
        "total_open": briefing.total_open,
    }


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
