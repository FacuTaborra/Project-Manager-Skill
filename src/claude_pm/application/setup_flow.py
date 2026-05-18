"""SetupService — discover team/project/states and persist them in cache."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config
from ..domain.models import Project, Team
from ..domain.ports import IssueProvider
from ..exceptions import NeedsChoice, PMError
from ..infrastructure.cache import Cache


@dataclass
class SetupOptions:
    force: bool = False
    team_id_override: str | None = None
    project_id_override: str | None = None
    create_project_if_missing: bool = False


class SetupService:
    """Resolve `(team, project, stateIds)` and write them to the cache.

    Behavior:
      - If the cache is fresh (≤ 30 days) and complete, we no-op.
      - If a team/project override is provided, we use it (and revalidate state IDs).
      - If multiple teams exist and no override, we raise NeedsChoice for the CLI.
      - If no project matches the repo name, we either create one (when
        `create_project_if_missing=True`) or raise NeedsChoice asking the user.
    """

    def __init__(self, provider: IssueProvider, cache: Cache, config: Config) -> None:
        self.provider = provider
        self.cache = cache
        self.config = config

    def ensure(self, options: SetupOptions | None = None) -> Cache:
        opts = options or SetupOptions()

        cache_complete = (
            self.cache.team_id
            and self.cache.projects
            and self.cache.state_ids
            and self.cache.is_fresh()
        )
        if not opts.force and cache_complete:
            return self.cache

        if self.config.pm_file.projects:
            return self._setup_from_pm_file(opts)

        team_id = self._resolve_team(opts)
        project = self._resolve_project(team_id, opts)
        state_ids = {s.name: s.id for s in self.provider.list_states(team_id)}
        self.cache.write(
            team_id=team_id,
            project_id=project.id,
            project_name=project.name,
            state_ids=state_ids,
        )
        return self.cache

    def _setup_from_pm_file(self, opts: SetupOptions) -> Cache:
        pm = self.config.pm_file
        teams = self.provider.list_teams()
        if not teams:
            raise PMError("No teams/spaces found in this workspace.")

        if pm.space:
            matched = [t for t in teams if t.name.lower() == pm.space.lower()]
            if not matched:
                available = ", ".join(t.name for t in teams)
                raise PMError(f"Space '{pm.space}' not found. Available: {available}")
            team_id = matched[0].id
        elif len(teams) == 1:
            team_id = teams[0].id
        else:
            raise NeedsChoice(
                "Multiple teams found and no 'space' set in projects.pm. Pick one and re-run with --team-id <ID>.",
                {"action": "choose-team", "teams": [_team_dict(t) for t in teams]},
            )

        available_projects = self.provider.list_projects(team_id)
        name_to_proj = {p.name.lower(): p for p in available_projects}
        resolved: list[dict[str, str]] = []
        for name in pm.projects:
            proj = name_to_proj.get(name.lower())
            if not proj:
                avail = ", ".join(p.name for p in available_projects)
                raise PMError(f"Project '{name}' not found in space. Available: {avail}")
            resolved.append({"id": proj.id, "name": proj.name})

        state_ids = {s.name: s.id for s in self.provider.list_states(team_id)}
        self.cache.write_multi(team_id=team_id, projects=resolved, state_ids=state_ids)
        return self.cache

    # -- internals -----------------------------------------------------------

    def _resolve_team(self, opts: SetupOptions) -> str:
        override = opts.team_id_override or self.config.team_id_override or self.cache.team_id
        teams = self.provider.list_teams()
        if not teams:
            raise PMError("Workspace has no teams. Create one in your tracker first.")

        if override:
            if not any(t.id == override for t in teams):
                raise PMError(f"Team id {override} not found in this workspace.")
            return override
        if len(teams) == 1:
            return teams[0].id
        raise NeedsChoice(
            "Multiple teams found. Pick one and re-run with --team-id <ID>.",
            {"action": "choose-team", "teams": [_team_dict(t) for t in teams]},
        )

    def _resolve_project(self, team_id: str, opts: SetupOptions) -> Project:
        override = (
            opts.project_id_override or self.config.project_id_override or self.cache.project_id
        )
        if override:
            # We trust the override but use the cached name (or repo_name as fallback).
            return Project(id=override, name=self.cache.project_name or self.config.repo_name)

        candidates = self.provider.find_projects(self.config.repo_name)
        exact = [p for p in candidates if p.name.lower() == self.config.repo_name.lower()]
        if exact:
            return exact[0]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise NeedsChoice(
                f"Multiple projects match '{self.config.repo_name}'. "
                f"Pick one and re-run with --project-id <ID>.",
                {
                    "action": "choose-project",
                    "projects": [{"id": p.id, "name": p.name} for p in candidates],
                },
            )

        # No project exists.
        if opts.create_project_if_missing:
            return self.provider.create_project(self.config.repo_name, team_id)
        raise NeedsChoice(
            f"No project matches '{self.config.repo_name}' in this team. "
            f"Re-run with --create-project to create one named '{self.config.repo_name}', "
            f"or with --project-id <ID> to use an existing one with a different name.",
            {"action": "create-or-pick-project", "repo_name": self.config.repo_name},
        )


def _team_dict(team: Team) -> dict[str, str]:
    return {"id": team.id, "name": team.name, "key": team.key}
