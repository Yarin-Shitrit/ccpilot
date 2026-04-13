"""Config loader. Stdlib-only. TOML via tomllib (3.11+) or fallback parser."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

DEFAULTS: dict[str, Any] = {
    "router": {
        "enabled": True,
        "min_complexity_for_swarm": 0.55,
        "log_path": "~/.claude/ccpilot/log.jsonl",
        "visible_routing_block": True,
    },
    "classifier": {
        "llm_escalation": False,
        "protocol": "anthropic",  # "anthropic" | "openai"
        "base_url": "",
        "model": "",
        "api_key_env": "CLAUDE_API_KEY",
        "confidence_threshold": 0.6,
        "timeout_s": 8,
    },
    "swarm": {
        "max_agents": 5,
        "byzantine": False,
        "quorum_timeout_s": 60,
        "mode": "direct",  # "direct" | "teams" (sqlite mailbox)
    },
    "search": {
        "enabled": True,  # semantic rerank of skills (sub-ms at <500 skills)
    },
    "guidance": {
        "enabled": True,  # parse CLAUDE.md ## Rules section
    },
    "learning": {
        "enabled": False,  # PostToolUse verdict tracking
    },
}


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    candidates = [
        Path(path) if path else None,
        Path(os.environ.get("CCPILOT_CONFIG", "")) if os.environ.get("CCPILOT_CONFIG") else None,
        Path.home() / ".claude" / "ccpilot" / "config.toml",
        Path(__file__).with_name("config.toml"),
    ]
    for c in candidates:
        if c and c.is_file():
            with c.open("rb") as f:
                return _deep_merge(DEFAULTS, tomllib.load(f))
    return DEFAULTS
