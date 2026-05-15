"""`create-issue` — create a single issue with optional assignee + labels."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..application.issue_creation import CreateIssueService
from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK, PMError
from ._helpers import build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()

    description_path = Path(args.description_file).expanduser()
    if not description_path.is_file():
        raise PMError(f"Description file not found: {description_path}")
    description = description_path.read_text(encoding="utf-8")

    issue = CreateIssueService(provider, cache).create(
        title=args.title,
        description=description,
        state_name=args.state,
        priority=args.priority,
        assignee_email=args.assignee,
        label_names=args.label or [],
    )
    print_json(
        {
            "ok": True,
            "id": issue.identifier,  # human-readable ID for compat
            "identifier": issue.identifier,
            "title": issue.title,
            "url": issue.url,
        }
    )
    return EXIT_OK
