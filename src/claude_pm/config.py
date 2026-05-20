"""Configuration: env var resolution, path resolution, PAK loading."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

from .enums import ProviderType
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

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECTS_FILE = _SKILL_ROOT / "projects.pm"
_SKILL_ENV_FILE = _SKILL_ROOT / ".env"


@dataclass(frozen=True)
class _ProviderConf:
    api_key: str
    pak_env: str
    default_pak: Path
    cache_suffix: str
    team_env: str
    project_env: str
    setup_hint: str


_PROVIDER_CONF: dict[ProviderType, _ProviderConf] = {
    ProviderType.LINEAR: _ProviderConf(
        api_key="LINEAR_API_KEY",
        pak_env="LINEAR_PAK_FILE",
        default_pak=DEFAULT_LINEAR_PAK_FILE,
        cache_suffix=".linear-cache.json",
        team_env="LINEAR_TEAM_ID",
        project_env="LINEAR_PROJECT_ID",
        setup_hint=(
            "  See README.md. Create a Personal API Key at https://linear.app/settings/api\n"
            "  and save it as: LINEAR_API_KEY=lin_api_xxx in the file above."
        ),
    ),
    ProviderType.CLICKUP: _ProviderConf(
        api_key="CLICKUP_API_KEY",
        pak_env="CLICKUP_PAK_FILE",
        default_pak=DEFAULT_CLICKUP_PAK_FILE,
        cache_suffix=".clickup-cache.json",
        team_env="CLICKUP_SPACE_ID",
        project_env="CLICKUP_LIST_ID",
        setup_hint=(
            "  Get your token at ClickUp → Settings → Apps → API Token\n"
            "  and save it as: CLICKUP_API_KEY=pk_xxx in the file above.\n"
            "  Set PM_PROVIDER=clickup in your environment."
        ),
    ),
}


@dataclass
class Config:
    pak_file: Path
    pak: str | None
    vault_path: Path | None
    repo_name: str
    cache_path: Path
    team_id_override: str | None
    project_id_override: str | None
    provider_name: ProviderType = ProviderType.LINEAR
    pm_file: PmFileConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.pm_file is None:
            self.pm_file = PmFileConfig()

    @classmethod
    def load(cls, repo_name_override: str | None = None) -> Config:
        from .infrastructure.repo_detect import detect_repo_name

        repo_name = repo_name_override or detect_repo_name()
        pm_file = _read_projects_file(repo_name)

        provider_name = _parse_provider(os.environ.get("PM_PROVIDER") or pm_file.provider)

        conf = _PROVIDER_CONF[provider_name]
        pak_file = Path.cwd() / ".env"
        pak = _read_env_key(pak_file, conf.api_key)
        if not pak:
            pak_file = _SKILL_ENV_FILE
            pak = _read_env_key(pak_file, conf.api_key)
        if not pak:
            pak_file = Path(os.environ.get(conf.pak_env, str(conf.default_pak))).expanduser()
            pak = _read_env_key(pak_file, conf.api_key)

        vault_env = os.environ.get("CLAUDE_MEMORY_PATH")
        vault_path: Path | None = Path(vault_env).expanduser() if vault_env else DEFAULT_VAULT
        if vault_path is not None and not vault_path.is_dir():
            vault_path = None

        cache_suffix = conf.cache_suffix
        cache_path = (vault_path / "proyectos" / repo_name / cache_suffix) if vault_path else (FALLBACK_CACHE_ROOT / repo_name / cache_suffix)

        return cls(
            pak_file=pak_file,
            pak=pak,
            vault_path=vault_path,
            repo_name=repo_name,
            cache_path=cache_path,
            team_id_override=os.environ.get(conf.team_env),
            project_id_override=os.environ.get(conf.project_env),
            provider_name=provider_name,
            pm_file=pm_file,
        )

    def require_pak(self) -> str:
        if not self.pak:
            hint = _PROVIDER_CONF[self.provider_name].setup_hint
            raise ConfigError(
                f"{self.provider_name.capitalize()} API key not found at {self.pak_file}.\n{hint}"
            )
        return self.pak


def _read_env_key(path: Path, key_name: str) -> str | None:
    if not path.is_file():
        return None
    prefix = f"{key_name}="
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if line.startswith(prefix):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


def _read_projects_file(repo_name: str) -> PmFileConfig:
    if not _PROJECTS_FILE.is_file():
        return PmFileConfig()
    parser = configparser.ConfigParser()
    try:
        parser.read(_PROJECTS_FILE, encoding="utf-8")
    except OSError:
        return PmFileConfig()
    section = next((s for s in parser.sections() if s.lower() == repo_name.lower()), None)
    if not section:
        return PmFileConfig()
    sec = parser[section]
    projects = [p.strip() for p in sec.get("project", "").split(",") if p.strip()]
    return PmFileConfig(
        provider=sec.get("provider") or None,
        space=sec.get("space") or None,
        projects=projects,
        label=sec.get("label") or None,
    )

def _parse_provider(value: str | None) -> ProviderType:
    try:
        return ProviderType(value or "linear")
    except ValueError:
        supported = ", ".join(p.value for p in ProviderType)
        raise ConfigError(f"Unknown provider '{value}'. Supported: {supported}") from None
