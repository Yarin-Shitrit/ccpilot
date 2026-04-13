# ccpilot

Zero-config auto-pilot for the Claude CLI. Installs a `UserPromptSubmit` hook that classifies each prompt, discovers available skills/MCP servers on the host, and injects a routing block so Claude automatically dispatches the right skills and subagents — no DSL, no learning curve.

## Install

Requires Python 3.9+. Works on Linux, macOS, Windows.

```sh
git clone https://github.com/Yarin-Shitrit/ccpilot.git
cd ccpilot
python install.py --with-smart              # one-shot: hooks + skills + smart deps
```

`--with-smart` pip-installs `anthropic` (Haiku classifier escalation) and
`model2vec` (dense skill embeddings). Skip it for a pure-stdlib install —
ccpilot falls back to hashed TF-IDF and regex heuristics.

Other flags:

```sh
python install.py --dry-run                 # preview every file touched
python install.py --with-learning           # also install PostToolUse verdict hook
python install.py --with-openai             # add openai SDK (MiniMax, LiteLLM, etc)
python install.py --no-skills --no-agents   # hooks only, bring your own skills
```

Uninstall: remove the `ccpilot` entry from `~/.claude/settings.json`'s `UserPromptSubmit` hooks and delete `~/.claude/ccpilot/`.

## What it does

- Heuristic classifier scores each prompt (intent + complexity + confidence) with pure stdlib. No network required.
- Optional Tier-2 escalation to a private Claude endpoint for low-confidence prompts. Fully configurable; off by default.
- Dynamic registry scans `~/.claude/skills/*/SKILL.md`, `.mcp.json`, and plugins — works with whatever the host already has.
- Swarm orchestrator spawns role-specialized subagents for complex prompts and reconciles via Raft-lite quorum consensus (opt-in Byzantine mode for high-stakes runs).
- Bundled 30-skill pack installed non-destructively (`.ccpilot` suffix on name conflicts).

## Configuration

`~/.claude/ccpilot/config.toml` — see `ccpilot/config.sample.toml` for the full schema. All fields optional.

### Disabling the hook (cost management)

Three levels, from most to least ephemeral:

```sh
CCPILOT_DISABLED=1 claude              # one-shot: skip routing for this session
```

```toml
# ~/.claude/ccpilot/config.toml — persistent off switch
[router]
enabled = false
```

```toml
# Keep routing on but disable Tier-2 LLM escalation (the only outbound cost)
[classifier]
llm_escalation = false
```

Or remove the `ccpilot` entry from `~/.claude/settings.json`'s `UserPromptSubmit` hooks to fully uninstall.

## Architecture

- `ccpilot/route.py` — hook entrypoint.
- `ccpilot/classifier.py` — heuristic + optional LLM classification.
- `ccpilot/registry.py` — skills/MCP discovery.
- `ccpilot/swarm/` — coordinator, consensus (Raft-lite), judge, roles.
- `ccpilot/llm/client.py` — stdlib HTTP client for a private Claude endpoint.
- `hooks/ccpilot.{sh,cmd}` — thin POSIX/Windows launchers.

## Verify

```sh
echo '{"prompt": "audit this repo for security issues"}' | python -m ccpilot route
python -m ccpilot registry
pytest                           # smoke tests
```

Logs: `~/.claude/ccpilot/log.jsonl` (routing) and `~/.claude/ccpilot/swarm.jsonl` (consensus rounds).
