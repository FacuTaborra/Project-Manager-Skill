#!/usr/bin/env python3
"""Backward-compat wrapper. Delegates to the `claude_pm` package in src/.

SKILL.md hard-codes `python3 ~/.claude/skills/pm/pm.py <cmd>`, so this file
must stay at the repo root and be installed alongside the package.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "src"))

from claude_pm.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
