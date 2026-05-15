"""SearchService — duplicate detection before plan mode proposes new issues."""

from __future__ import annotations

from ..domain.models import Issue
from ..domain.ports import IssueProvider


class SearchService:
    def __init__(self, provider: IssueProvider) -> None:
        self.provider = provider

    def find_duplicates(self, query: str, *, scoped_to_project: str | None = None) -> list[Issue]:
        return self.provider.search_issues(query, project_id=scoped_to_project)
