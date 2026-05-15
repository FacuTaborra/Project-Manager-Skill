"""CreateIssueService — resolve assignee/labels then create the issue."""

from __future__ import annotations

from ..domain.models import Issue, IssueDraft
from ..domain.ports import IssueProvider
from ..exceptions import PMError
from ..infrastructure.cache import Cache


class CreateIssueService:
    def __init__(self, provider: IssueProvider, cache: Cache) -> None:
        self.provider = provider
        self.cache = cache

    def create(
        self,
        *,
        title: str,
        description: str,
        state_name: str | None = None,
        priority: int | None = None,
        assignee_email: str | None = None,
        label_names: list[str] | None = None,
    ) -> Issue:
        team_id = self.cache.team_id
        project_id = self.cache.project_id
        if not team_id or not project_id:
            raise PMError("Cache is missing team_id/project_id. Run `pm setup` first.")

        state_id = self._resolve_state(state_name)
        assignee_id = self._resolve_assignee(assignee_email)
        label_ids = self._resolve_labels(team_id, label_names or [])

        draft = IssueDraft(
            title=title,
            description=description,
            project_id=project_id,
            team_id=team_id,
            state_id=state_id,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=tuple(label_ids),
        )
        return self.provider.create_issue(draft)

    # -- resolvers -----------------------------------------------------------

    def _resolve_state(self, state_name: str | None) -> str | None:
        if not state_name:
            return None
        state_id = self.cache.state_ids.get(state_name)
        if not state_id:
            available = ", ".join(self.cache.state_ids.keys())
            raise PMError(f"State '{state_name}' not found. Available: {available}")
        return state_id

    def _resolve_assignee(self, email: str | None) -> str | None:
        if not email:
            return None
        user = self.provider.resolve_user_by_email(email)
        if not user:
            raise PMError(f"No member with email '{email}' in this workspace.")
        return user.id

    def _resolve_labels(self, team_id: str, names: list[str]) -> list[str]:
        if not names:
            return []
        team_labels = self.provider.list_labels(team_id)
        by_name = {lbl.name.lower(): lbl.id for lbl in team_labels}
        resolved: list[str] = []
        for name in names:
            lid = by_name.get(name.lower())
            if not lid:
                available = ", ".join(sorted(lbl.name for lbl in team_labels)) or "(none)"
                raise PMError(
                    f"Label '{name}' not found in this team. "
                    f"Available: {available}. Create it in your tracker UI first."
                )
            resolved.append(lid)
        return resolved
