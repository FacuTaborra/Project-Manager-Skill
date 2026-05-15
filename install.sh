#!/usr/bin/env bash
# claude-pm-skill installer (Linux / macOS / Git Bash on Windows).
# Copies SKILL.md, pm.py and the src/claude_pm package to ~/.claude/skills/pm/
# and seeds the secret file.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_DIR/skills/pm"
SECRETS_DIR="$CLAUDE_DIR/secrets"
SECRET_FILE="$SECRETS_DIR/linear-pak.env"
EXAMPLE_FILE="$REPO_ROOT/examples/linear-pak.env.example"

echo "claude-pm-skill installer"
echo "  repo:       $REPO_ROOT"
echo "  target:     $SKILL_DIR"

if [ ! -d "$CLAUDE_DIR" ]; then
  echo
  echo "WARN: $CLAUDE_DIR does not exist."
  echo "      Install Claude Code first: https://docs.anthropic.com/claude/docs/claude-code"
  echo "      Continuing anyway — directories will be created."
fi

mkdir -p "$SKILL_DIR"
cp "$REPO_ROOT/SKILL.md" "$SKILL_DIR/SKILL.md"
cp "$REPO_ROOT/pm.py"    "$SKILL_DIR/pm.py"
chmod +x "$SKILL_DIR/pm.py" 2>/dev/null || true
echo "  + $SKILL_DIR/SKILL.md"
echo "  + $SKILL_DIR/pm.py"

# Sync the src/claude_pm package (mirror — remove stale files first)
mkdir -p "$SKILL_DIR/src"
rm -rf "$SKILL_DIR/src/claude_pm"
cp -r "$REPO_ROOT/src/claude_pm" "$SKILL_DIR/src/claude_pm"
echo "  + $SKILL_DIR/src/claude_pm/ (package)"

mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR" 2>/dev/null || true

if [ -f "$SECRET_FILE" ]; then
  echo "  = $SECRET_FILE (kept existing)"
else
  cp "$EXAMPLE_FILE" "$SECRET_FILE"
  chmod 600 "$SECRET_FILE" 2>/dev/null || true
  echo "  + $SECRET_FILE (template — edit it to add your real key)"
fi

echo
echo "Installed."
echo
echo "Next steps:"
echo "  1. Edit $SECRET_FILE and replace REPLACE_ME with your Linear PAK."
echo "     Get one at https://linear.app/settings/api (scope: read + write)."
echo "  2. Verify with: python3 $SKILL_DIR/pm.py doctor"
echo "  3. Open Claude Code in any project and run: /pm"
