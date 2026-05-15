"""`doctor` — diagnose configuration."""

from __future__ import annotations

import argparse
import sys

from ..config import DEFAULT_VAULT, Config
from ..exceptions import EXIT_ERROR, EXIT_OK, ProviderError
from ..infrastructure.providers._registry import get_provider


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    print("claude-pm-skill — doctor")
    print(f"  Python:        {sys.version.split()[0]}")
    print(f"  Repo name:     {config.repo_name}")
    print(f"  Provider:      {config.provider_name}")
    print(f"  PAK file:      {config.pak_file}")
    print(f"  PAK loaded:    {'yes' if config.pak else 'NO — see README setup'}")
    if config.vault_path:
        print(f"  Vault:         {config.vault_path}")
    else:
        print(
            f"  Vault:         not found (CLAUDE_MEMORY_PATH unset and {DEFAULT_VAULT} missing). "
            f"Skill will run in tracker-only mode."
        )
    print(
        f"  Cache:         {config.cache_path}"
        f" {'(exists)' if config.cache_path.is_file() else '(not yet created)'}"
    )
    if config.team_id_override:
        print(f"  Team override: LINEAR_TEAM_ID={config.team_id_override}")
    if config.project_id_override:
        print(f"  Project override: LINEAR_PROJECT_ID={config.project_id_override}")

    if not config.pak:
        return EXIT_OK
    print("  Provider ping: testing...")
    try:
        provider = get_provider(config.provider_name, api_key=config.pak)
        email = provider.viewer_email()
        print(f"  Provider ping: ok — authenticated as {email}")
    except ProviderError as e:
        print(f"  Provider ping: FAILED — {e}")
        return EXIT_ERROR
    return EXIT_OK
