"""`update-issue` — update title, state, priority, or assignee of an existing issue."""

from __future__ import annotations

import argparse

from ..application.setup_flow import SetupService
from ..config import Config
from ..domain.models import IssueUpdate
from ..exceptions import EXIT_OK, PMError
from ._helpers import build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)

    state_id: str | None = None
    if args.state:
        cache = SetupService(provider, load_cache(config), config).ensure()
        state_id = cache.state_ids.get(args.state)
        if not state_id:
            available = ", ".join(cache.state_ids.keys())
            raise PMError(f"State '{args.state}' not found. Available: {available}")

    assignee_id: str | None = None
    if args.assignee:
        user = provider.resolve_user_by_email(args.assignee)
        if not user:
            raise PMError(f"No member with email '{args.assignee}'.")
        assignee_id = user.id

    update = IssueUpdate(
        issue_id=args.id,
        title=args.title,
        description=args.description,
        state_id=state_id,
        priority=args.priority,
        assignee_id=assignee_id,
    )
    issue = provider.update_issue(update)
    print_json({
        "ok": True,
        "identifier": issue.identifier,
        "title": issue.title,
        "state": issue.state.name,
        "url": issue.url,
    })
    return EXIT_OK
