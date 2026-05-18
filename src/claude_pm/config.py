"""Configuration: env var resolution, path resolution, PAK loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import ConfigError


@dataclass
class PmFileConfig:
    """Contents of the `.pm` file at the repo root."""

    provider: str | None = None
    space: str | None = None
    projects: list[str] = field(default_factory=list)
    label: str | None = None


DEFAULT_VAULT = Path.home() / ".claude-memory"
DEFAULT_LINEAR_PAK_FILE = Path.home() / ".claude" / "secrets" / "linear-pak.env"
DEFAULT_CLICKUP_PAK_FILE = Path.home() / ".claude" / "secrets" / "clickup-pak.env"
FALLBACK_CACHE_ROOT = Path.home() / ".config" / "claude-pm-skill"

# Keep old name as alias so external code importing it doesn't break.
DEFAULT_PAK_FILE = DEFAULT_LINEAR_PAK_FILE

# Resolve symlinks so paths work whether the skill is run directly or via symlink.
_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent

# .env in the repo root
_REPO_ENV_FILE = _SKILL_ROOT / ".env"

# Central projects config (one section per repo, gitignored)
_PROJECTS_FILE = _SKILL_ROOT / "projects.pm"


def _read_projects_file(repo_name: str) -> PmFileConfig:
    """Parse projects.pm and return the section matching repo_name, or empty config."""
    if not _PROJECTS_FILE.is_file():
        return PmFileConfig()
    current: str | None = None
    fields: dict[str, str] = {}
    try:
        for raw in _PROJECTS_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                if current and current.lower() == repo_name.lower():
                    break
                current = line[1:-1].strip()
                fields = {}
                continue
            if current and current.lower() == repo_name.lower() and ":" in line:
                key, _, val = line.partition(":")
                fields[key.strip().lower()] = val.strip()
    except OSError:
        return PmFileConfig()

    if not fields:
        return PmFileConfig()

    projects = [p.strip() for p in fields.get("project", "").split(",") if p.strip()]
    return PmFileConfig(
        provider=fields.get("provider") or None,
        space=fields.get("space") or None,
        projects=projects,
        label=fields.get("label") or None,
    )


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
    pm_file: PmFileConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.pm_file is None:
            self.pm_file = PmFileConfig()

    @classmethod
    def load(cls, repo_name_override: str | None = None) -> Config:
        from .infrastructure.repo_detect import detect_repo_name

        repo_name = repo_name_override or detect_repo_name()
        pm_file = _read_projects_file(repo_name)

        # Priority: env var > projects.pm > default "linear"
        provider_name = os.environ.get("PM_PROVIDER") or pm_file.provider or "linear"

        if provider_name == "clickup":
            # Repo .env first, then legacy secrets file, then env var override.
            pak = _read_env_key(_REPO_ENV_FILE, "CLICKUP_API_KEY")
            pak_file = _REPO_ENV_FILE
            if not pak:
                pak_file = Path(
                    os.environ.get("CLICKUP_PAK_FILE", str(DEFAULT_CLICKUP_PAK_FILE))
                ).expanduser()
                pak = _read_env_key(pak_file, "CLICKUP_API_KEY")
            cache_suffix = ".clickup-cache.json"
            team_id_override = os.environ.get("CLICKUP_SPACE_ID")
            project_id_override = os.environ.get("CLICKUP_LIST_ID")
        else:
            pak = _read_env_key(_REPO_ENV_FILE, "LINEAR_API_KEY")
            pak_file = _REPO_ENV_FILE
            if not pak:
                pak_file = Path(
                    os.environ.get("LINEAR_PAK_FILE", str(DEFAULT_LINEAR_PAK_FILE))
                ).expanduser()
                pak = _read_env_key(pak_file, "LINEAR_API_KEY")
            cache_suffix = ".linear-cache.json"
            team_id_override = os.environ.get("LINEAR_TEAM_ID")
            project_id_override = os.environ.get("LINEAR_PROJECT_ID")

        vault_env = os.environ.get("CLAUDE_MEMORY_PATH")
        vault_path: Path | None = Path(vault_env).expanduser() if vault_env else DEFAULT_VAULT
        if vault_path is not None and not vault_path.is_dir():
            vault_path = None

        if vault_path is not None:
            cache_path = vault_path / "proyectos" / repo_name / cache_suffix
        else:
            cache_path = FALLBACK_CACHE_ROOT / repo_name / cache_suffix

        return cls(
            pak_file=pak_file,
            pak=pak,
            vault_path=vault_path,
            repo_name=repo_name,
            cache_path=cache_path,
            team_id_override=team_id_override,
            project_id_override=project_id_override,
            provider_name=provider_name,
            pm_file=pm_file,
        )

    def require_pak(self) -> str:
        if not self.pak:
            if self.provider_name == "clickup":
                raise ConfigError(
                    f"ClickUp API key not found at {self.pak_file}.\n"
                    f"  1. Get your Personal Token at ClickUp → Settings → Apps → API Token\n"
                    f"  2. Save it as: CLICKUP_API_KEY=pk_xxx in {self.pak_file}\n"
                    f"  3. Set PM_PROVIDER=clickup in your environment"
                )
            raise ConfigError(
                f"Linear API key not found at {self.pak_file}.\n"
                f"  See README.md for setup. Quick version:\n"
                f"    1. Create a Personal API Key at https://linear.app/settings/api\n"
                f"    2. Save it as: LINEAR_API_KEY=lin_api_xxx in {self.pak_file}\n"
                f"    3. chmod 600 {self.pak_file}"
            )
        return self.pak


def _read_env_key(path: Path, key_name: str) -> str | None:
    """Parse a `KEY=VALUE` env file and return the value for key_name (or None)."""
    if not path.is_file():
        return None
    prefix = f"{key_name}="
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if line.startswith(prefix):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
    except OSError:
        return None
    return None


def _read_pak(path: Path) -> str | None:
    """Backward-compat wrapper — reads LINEAR_API_KEY."""
    return _read_env_key(path, "LINEAR_API_KEY")
