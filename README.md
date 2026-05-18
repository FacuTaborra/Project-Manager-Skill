# claude-pm-skill

[![CI](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml)

A Claude Code skill that turns Claude into your project's **Project Manager**, backed by Linear (with an extensible provider architecture for GitHub Issues, Jira, etc.).

Two modes:

- **`/pm`** — Briefing of what's open, in progress, and blocked.
- **`/pm "task description"`** — Proposes a board of issues for the task, then creates them in Linear after your confirmation.

Designed to work in **any repo**, with or without an Obsidian vault for project context. Output (briefings, proposed boards, issue descriptions in Linear) is always written in the language you're using to talk to Claude.

---

## Requirements

- **Python 3.10+** (uses stdlib only at runtime — no `pip install` needed to use it)
- **Linear** account with permission to create issues
- **Claude Code** CLI installed ([install guide](https://docs.anthropic.com/claude/docs/claude-code))

---

## Install

### Linux / macOS / Git Bash on Windows

```bash
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
./install.sh
```

### Windows (native PowerShell)

```powershell
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
.\install.ps1
```

The installer copies `SKILL.md` and `pm.py` to `~/.claude/skills/pm/` and creates a `~/.claude/secrets/linear-pak.env` from the example if it doesn't exist.

### Optional: add the `pm` shell alias

To run `pm doctor` instead of the full `python3 ~/.claude/skills/pm/pm.py doctor`:

**Git Bash / Linux / macOS** — add to `~/.bashrc` or `~/.zshrc`:
```bash
alias pm='python3 ~/.claude/skills/pm/pm.py'
```

**PowerShell** — add to your `$PROFILE`:
```powershell
function pm { python3 "$HOME/.claude/skills/pm/pm.py" @args }
```

---

## Configure: get a Linear API key

1. Go to <https://linear.app/settings/api>
2. Click **Create new API key**
3. Name it (e.g. `claude-pm-skill`), grant **Read + Write** scopes
4. Copy the key (starts with `lin_api_...`)
5. Open `~/.claude/secrets/linear-pak.env` and replace `REPLACE_ME`:
   ```
   LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxx
   ```
6. Lock down the file (Linux/macOS):
   ```bash
   chmod 600 ~/.claude/secrets/linear-pak.env
   ```

Verify everything works:

```bash
pm doctor
# or without the alias:
python3 ~/.claude/skills/pm/pm.py doctor
```

You should see `Linear ping: ok — authenticated as <your email>`.

---

## Usage

Open Claude Code in any project, then:

```
/pm
```

→ briefing of open issues for the current repo.

```
/pm let's add a multi-tenant billing feature
```

→ Claude proposes a board of issues, asks for your confirmation, and creates them in Linear.

The skill auto-detects the **project name** from the current directory (or `.claude-session-name` if present) and looks up the matching Linear project. On first use it caches the team/project IDs so subsequent calls are fast.

---

## Environment variables

All optional — the defaults work for most setups.

| Variable | Default | What it does |
|---|---|---|
| `CLAUDE_MEMORY_PATH` | `~/.claude-memory` | Path to an Obsidian vault. If it exists, the skill reads `proyectos/<repo>/STATUS.md` to enrich briefings. If not, the skill runs in Linear-only mode. |
| `LINEAR_PAK_FILE` | `~/.claude/secrets/linear-pak.env` | Where the Linear PAK lives. |
| `LINEAR_TEAM_ID` | (none) | Override auto-detected team. |
| `LINEAR_PROJECT_ID` | (none) | Override auto-detected project. Useful if the Linear project name differs from the repo name. |

---

## Team setup

A Linear **team** is a shared board — multiple developers can use this skill against the same Linear project. Issues you create show up for the whole team in real time. Each developer uses their own Personal API Key.

### First developer (creates the project)

```bash
git clone <repo>
cd <repo>
./install.sh    # or .\install.ps1 on Windows
```

Edit `~/.claude/secrets/linear-pak.env` with your PAK, then in Claude:

```
/pm
```

If no Linear project matches the repo name, the skill tells you. Either:

- Re-run setup to create one:
  ```bash
  pm setup --create-project
  ```
- Or point the skill at an existing project:
  ```bash
  pm setup --project-id <linear-project-id>
  ```

### Other developers on the team

Same install, but the skill finds the existing project automatically:

```bash
git clone <repo>
cd <repo>
./install.sh
# edit ~/.claude/secrets/linear-pak.env with YOUR own PAK
```

Then `/pm` from Claude — no manual setup needed.

### Project name doesn't match the repo

Set `LINEAR_PROJECT_ID` in your shell profile:

```bash
export LINEAR_PROJECT_ID=<uuid-of-the-linear-project>
```

Or override per-call:

```bash
pm setup --project-id <uuid>
```

### Assigning issues to teammates

Tell Claude: *"propose this task and assign it to juan@team.com"*. The skill resolves the email to a Linear user ID via `pm.py resolve-user` and passes `--assignee` to `create-issue`. The teammate must already exist in your Linear workspace.

### Using your team's labels

If your team uses Linear labels (`feature`, `bug`, `tech-debt`, etc.), tell Claude: *"…with the `feature` and `backend` labels"*. Labels must **already exist** in the team — the skill won't auto-create them (avoids typos becoming new labels). Run `pm list-labels` to see what's available.

### Security

- **PAKs are personal — never commit `linear-pak.env`.** Each developer generates their own.
- Each developer's `~/.claude/secrets/` is local. No shared secrets.

---

## Optional: Obsidian vault integration

If you keep project notes in an Obsidian vault following this layout:

```
<vault>/
└── proyectos/
    └── <repo-name>/
        ├── STATUS.md       # what's in flight, last sessions, blockers
        └── .linear-cache.json
```

…then the skill reads `STATUS.md` and includes a 1–2 line summary in the briefing. Set `CLAUDE_MEMORY_PATH` to your vault root.

The skill works fine without a vault — briefings just rely on Linear data only.

---

## Troubleshooting

### `Linear API key not found`

The PAK file is missing or has a malformed line. Run `pm.py doctor` to see where it's looking, then check that the file exists and contains `LINEAR_API_KEY=lin_api_...`.

### `Multiple teams found. Pick one and re-run with --team-id`

Your Linear workspace has more than one team. Run `pm.py list-teams` to see them, then:

```bash
pm setup --team-id <id>
```

Or set `LINEAR_TEAM_ID` in your shell profile.

### `No project matches '<repo>' in this team`

The Linear project doesn't exist. Either create it (`setup --create-project`) or use an existing one with a different name (`setup --project-id <id>`).

### `Label 'X' not found in this team`

Run `pm.py list-labels` to see what exists. Either pick one of those, or create the label in Linear's UI first (the skill won't auto-create labels — that prevents typos from polluting your label set).

### `No member with email 'X' in this workspace`

Check that the email matches the one Linear has for that user. Use `pm.py resolve-user <email>` to verify.

### Cache seems stale

```bash
pm setup --force
```

This re-discovers team, project, and state IDs from Linear.

---

## How it's wired

The skill follows a **hexagonal (ports & adapters)** architecture so that any issue tracker — Linear today, GitHub Issues / Jira / Notion tomorrow — can be plugged in without touching the rest of the code.

```
src/claude_pm/
├── domain/           # Issue, Team, Project, ... (frozen dataclasses)
│                     # IssueProvider, ContextProvider (typing.Protocol)
├── infrastructure/   # LinearProvider, ObsidianVaultContext, HttpClient, Cache
├── application/      # BriefingService, SetupService, SearchService, CreateIssueService
└── commands/         # CLI handlers — wire argparse to services
```

- **`SKILL.md`** — what Claude reads. Tells Claude how to detect mode, present briefings, propose boards, and call the CLI.
- **`pm.py`** (root) — a thin wrapper that delegates to the `claude_pm` package; preserves the exact invocation Claude uses (`python3 ~/.claude/skills/pm/pm.py <cmd>`).
- **`src/claude_pm/`** — the actual package. Subcommands: `doctor`, `setup`, `briefing`, `search`, `create-issue`, `list-teams`, `list-states`, `list-labels`, `resolve-user`.
- **Cache** — `<vault>/proyectos/<repo>/.linear-cache.json` if a vault is configured, else `~/.config/claude-pm-skill/<repo>/.linear-cache.json`.

The CLI does the API plumbing (HTTP, JSON, retries, error parsing); Claude handles the conversation.

To add a new tracker (GitHub, Jira, …), implement the `IssueProvider` Protocol — see [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the project layout, how to add a new provider, and local dev setup (`ruff`, `mypy`, smoke tests).

---

## License

MIT — see [LICENSE](./LICENSE).
