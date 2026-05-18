"""`create-issue` — create a single issue with optional assignee + labels."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..application.issue_creation import CreateIssueService
from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK, NeedsChoice, PMError
from ._helpers import build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()

    # Resolve which project to use
    projects = cache.projects
    project_id_override = getattr(args, "project_id", None)
    if len(projects) > 1 and not project_id_override:
        raise NeedsChoice(
            "Multiple projects configured. Re-run with --project-id <ID>.",
            {"action": "choose-project", "projects": projects},
        )
    if project_id_override:
        cache.data["linearProjectId"] = project_id_override
        matched = next((p for p in projects if p["id"] == project_id_override), None)
        cache.data["linearProjectName"] = matched["name"] if matched else project_id_override

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
