# Contributing to claude-pm-skill

Thanks for considering a contribution. This skill is built around a small, deliberate architecture so that anyone can plug in a new issue tracker (GitHub Issues, Jira, Notion Tasks, …) without touching the rest of the code.

## Project layout

```
src/claude_pm/
├── domain/          # Entities (Issue, Team, ...) and ports (Protocols)
├── infrastructure/  # Adapters: HTTP, cache, providers, context sources
├── application/     # Services (BriefingService, SetupService, ...)
└── commands/        # CLI handlers — wiring between argparse and services
```

The boundary lines are real:

- **`domain/`** has zero dependencies. It defines the entities (`Issue`, `Team`, …) and the **ports** (`IssueProvider`, `ContextProvider`) as `typing.Protocol`s.
- **`infrastructure/`** depends on `domain/`. Adapters live here (Linear today; GitHub/Jira/Notion tomorrow).
- **`application/`** depends only on `domain/` ports. Services orchestrate workflows but don't know about HTTP or argparse.
- **`commands/`** is the only layer that wires everything together. It lives next to the CLI parser.

When adding code, ask: *which layer does this belong to?* — and keep imports flowing only downward (commands → application → domain ← infrastructure).

## Adding a new issue tracker provider

The skill works against any issue tracker that can satisfy the [`IssueProvider`](src/claude_pm/domain/ports.py) Protocol. Today we ship Linear; here's how to add another (e.g. GitHub Issues).

1. **Create the adapter file**
   ```
   src/claude_pm/infrastructure/providers/github.py
   ```

2. **Implement `IssueProvider`** as a class. You don't need to inherit anything — `Protocol` uses structural typing, so as long as your class has the methods with the right signatures, mypy will accept it.

   ```python
   from ...domain.models import Issue, IssueDraft, Label, Project, State, Team, User

   class GitHubProvider:
       def __init__(self, token: str, repo: str) -> None: ...
       def viewer_email(self) -> str: ...
       def list_teams(self) -> list[Team]: ...
       def find_projects(self, name_query: str) -> list[Project]: ...
       def create_project(self, name: str, team_id: str) -> Project: ...
       def list_states(self, team_id: str) -> list[State]: ...
       def list_labels(self, team_id: str) -> list[Label]: ...
       def resolve_user_by_email(self, email: str) -> User | None: ...
       def list_open_issues(self, project_id: str) -> list[Issue]: ...
       def search_issues(self, query: str, *, project_id: str | None = None) -> list[Issue]: ...
       def create_issue(self, draft: IssueDraft) -> Issue: ...
   ```

   Reuse `infrastructure/providers/_http.py` (`HttpClient`) for the HTTP plumbing if it fits.

3. **Register the provider** in [`_registry.py`](src/claude_pm/infrastructure/providers/_registry.py):

   ```python
   from .github import GitHubProvider
   PROVIDERS["github"] = GitHubProvider
   ```

4. **Make it selectable.** Today the provider name is hard-coded to `"linear"` in `Config`. If you're adding a tracker for general use, expose it via an env var (e.g. `PM_PROVIDER=github`) and document it in the README. For internal experimentation, you can flip `Config.provider_name` directly.

5. **Document setup** in the README: which env vars the user must set, how to obtain credentials, and any provider-specific quirks.

## Conventions

- **stdlib only at runtime.** No `pip install` should be required to use the skill — only to develop on it (`ruff`, `mypy`).
- **Python ≥ 3.10.** Use `X | None` (not `Optional[X]`); use `match` if it helps; use modern dataclass features.
- **`from __future__ import annotations` at the top of every file.** It keeps annotations as strings, avoids forward-reference issues, and matches the rest of the codebase.
- **Models are frozen dataclasses.** No methods, no validation logic — just data.
- **Services receive ports via the constructor.** No `import` of concrete adapters inside `application/`.
- **Commands are wiring only.** A command handler should be ~30 lines: build provider, build service, call it, print JSON.

## Local development

```bash
git clone https://github.com/FacuTaborra/claude-pm-skill.git
cd claude-pm-skill
pip install -e ".[dev]"

# Verify
ruff check .
ruff format --check .
mypy

# Smoke test against Linear (needs a PAK)
python pm.py doctor
python pm.py briefing --repo-name <some-repo>
```

## Style and tooling

- **Lint:** `ruff check .`
- **Format:** `ruff format .`
- **Types:** `mypy` (strict mode is on)
- All three must pass before opening a PR. CI enforces them.

There are no automated tests in this repo yet — verification is manual smoke tests + lint + type checks. Tests are planned for a future iteration; if you'd like to lead that, open an issue first to align on the approach.

## Pull requests

- One feature/fix per PR.
- Keep commits focused; squash noisy ones before merging.
- Include a one-line summary of the change in the PR description and reference the issue if there is one.
- If you add a new provider, link to the official API docs you used.

## Issues

- Bug reports: include the command you ran, the output, and `python pm.py doctor` output.
- Feature requests: explain the use case and what wouldn't work today.
- Don't paste real PAKs or secrets in issues. The maintainer will not ask for them.
