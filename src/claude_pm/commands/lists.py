"""Lookup helpers: list-teams, list-states, list-labels, resolve-user."""

from __future__ import annotations

import argparse

from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK, PMError
from ._helpers import build_provider, load_cache, print_json


def run_list_teams(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    teams = provider.list_teams()
    print_json({"teams": [{"id": t.id, "name": t.name, "key": t.key} for t in teams]})
    return EXIT_OK


def run_list_states(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()
    print_json({"states": cache.state_ids})
    return EXIT_OK


def run_list_labels(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()
    team_id = cache.team_id
    if not team_id:
        raise PMError("Cache missing team_id. Run `pm setup` first.")
    labels = provider.list_labels(team_id)
    print_json({"labels": [{"id": lbl.id, "name": lbl.name} for lbl in labels]})
    return EXIT_OK


def run_resolve_user(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    user = provider.resolve_user_by_email(args.email)
    if not user:
        raise PMError(f"No member with email '{args.email}' in this workspace.")
    print_json({"user": {"id": user.id, "email": user.email, "name": user.name}})
    return EXIT_OK
