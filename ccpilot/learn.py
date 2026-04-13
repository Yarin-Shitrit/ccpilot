"""PostToolUse learning hook entrypoint.

Claude Code invokes this after each tool call with a JSON payload containing
the tool name and a success indicator. We record a verdict keyed to the last
routed intent (stashed by route.py into a small sidecar file) so that
memory.nudge() can bias future classifications.

Fails open: any error exits 0 silently.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import memory

SIDECAR = Path.home() / ".claude" / "ccpilot" / "last_intent.txt"


def _last_intent() -> str | None:
    try:
        return SIDECAR.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return 0
    intent = _last_intent()
    if not intent:
        return 0
    # Convention: Claude's PostToolUse payload carries tool_response.is_error
    # (bool). Absence = success.
    resp = payload.get("tool_response") or {}
    success = not bool(resp.get("is_error", False))
    try:
        memory.record(intent, success)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
