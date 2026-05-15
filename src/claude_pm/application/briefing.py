"""BriefingService — open issues grouped by state, plus optional vault context."""

from __future__ import annotations

from ..domain.models import Briefing, Issue
from ..domain.ports import ContextProvider, IssueProvider


class BriefingService:
    def __init__(self, provider: IssueProvider, context: ContextProvider) -> None:
        self.provider = provider
        self.context = context

    def generate(self, *, project_id: str, project_name: str, repo_name: str) -> Briefing:
        issues = self.provider.list_open_issues(project_id)
        grouped: dict[str, list[Issue]] = {}
        for issue in issues:
            grouped.setdefault(issue.state.name, []).append(issue)

        excerpt = (
            self.context.get_status_excerpt(repo_name) if self.context.is_available() else None
        )

        return Briefing(
            repo=repo_name,
            project_name=project_name,
            issues_by_state=grouped,
            total_open=len(issues),
            vault_excerpt=excerpt,
            vault_available=self.context.is_available(),
        )
