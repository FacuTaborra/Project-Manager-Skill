"""Argparse dispatch + main entry point."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from ._stdio import force_utf8_stdio
from .commands import briefing, create_issue, doctor, lists, search, setup, update_issue
from .exceptions import EXIT_OK, NeedsChoice, PMError


def _add_repo_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-name", default=None, help="Override auto-detected repo name.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pm",
        description="Linear-backed Product Manager CLI for Claude Code.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_doctor = sub.add_parser("doctor", help="Diagnose configuration.")
    _add_repo_arg(p_doctor)
    p_doctor.set_defaults(func=doctor.run)

    p_setup = sub.add_parser("setup", help="Discover team/project and write cache.")
    _add_repo_arg(p_setup)
    p_setup.add_argument("--team-id", default=None)
    p_setup.add_argument("--project-id", default=None)
    p_setup.add_argument(
        "--create-project",
        action="store_true",
        help="Create a project named after the repo if none matches.",
    )
    p_setup.add_argument("--force", action="store_true", help="Re-discover even if cache is fresh.")
    p_setup.set_defaults(func=setup.run)

    p_teams = sub.add_parser("list-teams", help="List teams in the workspace.")
    _add_repo_arg(p_teams)
    p_teams.set_defaults(func=lists.run_list_teams)

    p_projects = sub.add_parser("list-projects", help="List projects in the workspace.")
    _add_repo_arg(p_projects)
    p_projects.add_argument("--team-id", default=None, help="Filter by team ID.")
    p_projects.set_defaults(func=lists.run_list_projects)

    p_create_project = sub.add_parser("create-project", help="Create a new project/list inside a team/space.")
    _add_repo_arg(p_create_project)
    p_create_project.add_argument("name", help="Name of the new project.")
    p_create_project.add_argument("--team-id", required=True, help="Team or Space ID where the project will be created.")
    p_create_project.set_defaults(func=lists.run_create_project)

    p_create_team = sub.add_parser("create-team", help="Create a new team in the workspace.")
    _add_repo_arg(p_create_team)
    p_create_team.add_argument("name", help="Name of the new team.")
    p_create_team.set_defaults(func=lists.run_create_team)

    p_states = sub.add_parser("list-states", help="List workflow states for the current team.")
    _add_repo_arg(p_states)
    p_states.set_defaults(func=lists.run_list_states)

    p_labels = sub.add_parser("list-labels", help="List labels for the current team.")
    _add_repo_arg(p_labels)
    p_labels.set_defaults(func=lists.run_list_labels)

    p_user = sub.add_parser("resolve-user", help="Resolve a user id by email.")
    _add_repo_arg(p_user)
    p_user.add_argument("email")
    p_user.set_defaults(func=lists.run_resolve_user)

    p_brief = sub.add_parser("briefing", help="Open issues grouped by state, plus vault context.")
    _add_repo_arg(p_brief)
    p_brief.set_defaults(func=briefing.run)

    p_search = sub.add_parser("search", help="Search issues for duplicate detection.")
    _add_repo_arg(p_search)
    p_search.add_argument("query")
    p_search.add_argument(
        "--global-search",
        action="store_true",
        help="Search across all projects instead of just the current one.",
    )
    p_search.set_defaults(func=search.run)

    p_update = sub.add_parser("update-issue", help="Update an existing issue.")
    _add_repo_arg(p_update)
    p_update.add_argument("--id", required=True, help="Issue identifier (e.g. FAC-12 or ClickUp task ID).")
    p_update.add_argument("--title", default=None)
    p_update.add_argument("--description", default=None)
    p_update.add_argument("--state", default=None, help="State name (e.g. 'In Progress').")
    p_update.add_argument("--priority", type=int, default=None, help="0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low.")
    p_update.add_argument("--assignee", default=None, help="Email of the member to assign.")
    p_update.set_defaults(func=update_issue.run)

    p_create = sub.add_parser("create-issue", help="Create an issue.")
    _add_repo_arg(p_create)
    p_create.add_argument("--title", required=True)
    p_create.add_argument(
        "--description-file",
        required=True,
        help="Path to a UTF-8 file with the issue description (Markdown).",
    )
    p_create.add_argument(
        "--state",
        default=None,
        help="State name (Backlog, Todo, In Progress, ...). Default: team default.",
    )
    p_create.add_argument(
        "--priority",
        type=int,
        default=None,
        help="0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low.",
    )
    p_create.add_argument(
        "--assignee",
        default=None,
        help="Email of the workspace member to assign.",
    )
    p_create.add_argument(
        "--label",
        action="append",
        default=None,
        help="Label name (repeatable). Labels must exist in the team.",
    )
    p_create.set_defaults(func=create_issue.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    force_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
        return int(result) if result is not None else EXIT_OK
    except NeedsChoice as e:
        print(json.dumps(e.payload, indent=2, ensure_ascii=False))
        print(str(e), file=sys.stderr)
        return e.exit_code
    except PMError as e:
        print(str(e), file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
