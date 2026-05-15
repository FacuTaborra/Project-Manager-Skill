"""`setup` — discover team/project/states and write the cache."""

from __future__ import annotations

import argparse

from ..application.setup_flow import SetupOptions, SetupService
from ..config import Config
from ..exceptions import EXIT_OK
from ._helpers import build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = load_cache(config)

    options = SetupOptions(
        force=args.force,
        team_id_override=args.team_id,
        project_id_override=args.project_id,
        create_project_if_missing=args.create_project,
    )
    cache = SetupService(provider, cache, config).ensure(options)

    print_json({"ok": True, "cache": cache.data, "cache_path": str(cache.path)})
    return EXIT_OK
