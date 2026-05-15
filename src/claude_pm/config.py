"""Configuration: env var resolution, path resolution, PAK loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ConfigError

DEFAULT_VAULT = Path.home() / ".claude-memory"
DEFAULT_PAK_FILE = Path.home() / ".claude" / "secrets" / "linear-pak.env"
FALLBACK_CACHE_ROOT = Path.home() / ".config" / "claude-pm-skill"


@dataclass
class Config:
    pak_file: Path
    pak: str | None
    vault_path: Path | None
    repo_name: str
    cache_path: Path
    team_id_override: str | None
    project_id_override: str | None
    provider_name: str = "linear"

    @classmethod
    def load(cls, repo_name_override: str | None = None) -> Config:
        # Local import keeps the layering clean (config doesn't depend on infra).
        from .infrastructure.repo_detect import detect_repo_name

        pak_file = Path(os.environ.get("LINEAR_PAK_FILE", str(DEFAULT_PAK_FILE))).expanduser()
        pak = _read_pak(pak_file)

        vault_env = os.environ.get("CLAUDE_MEMORY_PATH")
        vault_path: Path | None = Path(vault_env).expanduser() if vault_env else DEFAULT_VAULT
        if vault_path is not None and not vault_path.is_dir():
            vault_path = None

        repo_name = repo_name_override or detect_repo_name()

        if vault_path is not None:
            cache_path = vault_path / "proyectos" / repo_name / ".linear-cache.json"
        else:
            cache_path = FALLBACK_CACHE_ROOT / repo_name / ".linear-cache.json"

        return cls(
            pak_file=pak_file,
            pak=pak,
            vault_path=vault_path,
            repo_name=repo_name,
            cache_path=cache_path,
            team_id_override=os.environ.get("LINEAR_TEAM_ID"),
            project_id_override=os.environ.get("LINEAR_PROJECT_ID"),
        )

    def require_pak(self) -> str:
        if not self.pak:
            raise ConfigError(
                f"Linear API key not found at {self.pak_file}.\n"
                f"  See README.md for setup. Quick version:\n"
                f"    1. Create a Personal API Key at https://linear.app/settings/api\n"
                f"    2. Save it as: LINEAR_API_KEY=lin_api_xxx in {self.pak_file}\n"
                f"    3. chmod 600 {self.pak_file}"
            )
        return self.pak


def _read_pak(path: Path) -> str | None:
    """Parse a `KEY=VALUE` env file and return LINEAR_API_KEY (or None)."""
    if not path.is_file():
        return None
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if line.startswith("LINEAR_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
    except OSError:
        return None
    return None
