"""Local JSON cache for the team/project/state IDs discovered during setup."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CACHE_TTL_DAYS = 30


@dataclass
class Cache:
    path: Path
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Cache:
        if path.is_file():
            try:
                return cls(path=path, data=json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                return cls(path=path, data={})
        return cls(path=path, data={})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def is_fresh(self) -> bool:
        ts = self.data.get("lastRefresh")
        if not ts:
            return False
        try:
            last = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            return False
        age = datetime.now(timezone.utc) - last
        return age.days < CACHE_TTL_DAYS

    @property
    def team_id(self) -> str | None:
        value = self.data.get("linearTeamId")
        return str(value) if value else None

    @property
    def project_id(self) -> str | None:
        value = self.data.get("linearProjectId")
        return str(value) if value else None

    @property
    def project_name(self) -> str | None:
        value = self.data.get("linearProjectName")
        return str(value) if value else None

    @property
    def projects(self) -> list[dict[str, str]]:
        raw = self.data.get("projects", [])
        if raw:
            return [{"id": str(p["id"]), "name": str(p["name"])} for p in raw]
        # backward compat: wrap single project
        if self.project_id and self.project_name:
            return [{"id": self.project_id, "name": self.project_name}]
        return []

    @property
    def state_ids(self) -> dict[str, str]:
        raw = self.data.get("stateIds", {})
        if not isinstance(raw, dict):
            return {}
        return {str(k): str(v) for k, v in raw.items()}

    def write(
        self,
        *,
        team_id: str,
        project_id: str,
        project_name: str,
        state_ids: dict[str, str],
    ) -> None:
        self.data = {
            "linearTeamId": team_id,
            "linearProjectId": project_id,
            "linearProjectName": project_name,
            "stateIds": state_ids,
            "lastRefresh": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def write_multi(
        self,
        *,
        team_id: str,
        projects: list[dict[str, str]],
        state_ids: dict[str, str],
    ) -> None:
        first = projects[0] if projects else {}
        self.data = {
            "linearTeamId": team_id,
            "linearProjectId": first.get("id"),
            "linearProjectName": first.get("name"),
            "projects": projects,
            "stateIds": state_ids,
            "lastRefresh": datetime.now(timezone.utc).isoformat(),
        }
        self.save()
