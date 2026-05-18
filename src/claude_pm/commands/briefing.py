"""`briefing` — open issues grouped by state, plus optional vault context."""

from __future__ import annotations

import argparse

from ..application.briefing import BriefingService
from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK, PMError
from ._helpers import briefing_to_dict, build_context, build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache = SetupService(provider, load_cache(config), config).ensure()

    projects = cache.projects
    if not projects:
        raise PMError("Cache is missing project info. Run `pm setup` first.")

    context = build_context(config)
    service = BriefingService(provider, context)

    if len(projects) > 1:
        result = service.generate_multi(projects=projects, repo_name=config.repo_name)
        print_json(result)
    else:
        briefing = service.generate(
            project_id=projects[0]["id"],
            project_name=projects[0]["name"],
            repo_name=config.repo_name,
        )
        print_json(briefing_to_dict(briefing))
    return EXIT_OK
