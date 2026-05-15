"""`search` — duplicate detection."""

from __future__ import annotations

import argparse

from ..application.search import SearchService
from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK
from ._helpers import build_provider, issue_to_dict, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()

    scope = None if args.global_search else cache.project_id
    matches = SearchService(provider).find_duplicates(args.query, scoped_to_project=scope)

    print_json(
        {
            "query": args.query,
            "matches": [issue_to_dict(i) for i in matches],
        }
    )
    return EXIT_OK
