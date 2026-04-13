"""Lightweight CLAUDE.md → rules compiler.

Ruflo uses a WASM kernel to enforce CLAUDE.md policies across long-horizon
runs. At ccpilot's scale a regex-level matcher is plenty: we parse a
`## Rules` section and derive predicates that veto/adjust the routing block
before it is emitted.

Supported rule grammar (one rule per bullet):
    - never spawn more than N agents
    - never use skill <name>
    - require skill <name> for <intent>
    - max complexity <float>

Unknown rules are preserved in .notes for human review but don't gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Rules:
    max_agents: int | None = None
    max_complexity: float | None = None
    banned_skills: set[str] = field(default_factory=set)
    required_skills: dict[str, str] = field(default_factory=dict)  # intent -> skill
    notes: list[str] = field(default_factory=list)


_SECTION = re.compile(r"(?mi)^##+\s*rules\s*$")
_BULLET = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")

_MAX_AGENTS = re.compile(r"(?i)never\s+spawn\s+more\s+than\s+(\d+)\s+agents?")
_MAX_COMPLEX = re.compile(r"(?i)max(?:imum)?\s+complexity\s+([0-9.]+)")
_BAN = re.compile(r"(?i)never\s+use\s+skill\s+([\w.-]+)")
_REQUIRE = re.compile(r"(?i)require\s+skill\s+([\w.-]+)\s+for\s+([\w-]+)")


def parse(md_text: str) -> Rules:
    rules = Rules()
    m = _SECTION.search(md_text)
    if not m:
        return rules
    tail = md_text[m.end():]
    # stop at next h2+
    stop = re.search(r"(?m)^##+\s", tail)
    body = tail[: stop.start()] if stop else tail
    for line in body.splitlines():
        bm = _BULLET.match(line)
        if not bm:
            continue
        rule = bm.group(1)
        if mm := _MAX_AGENTS.search(rule):
            rules.max_agents = int(mm.group(1))
        elif mm := _MAX_COMPLEX.search(rule):
            rules.max_complexity = float(mm.group(1))
        elif mm := _BAN.search(rule):
            rules.banned_skills.add(mm.group(1))
        elif mm := _REQUIRE.search(rule):
            rules.required_skills[mm.group(2)] = mm.group(1)
        else:
            rules.notes.append(rule)
    return rules


def load(cwd: Path | None = None) -> Rules:
    """Load rules from CLAUDE.md in cwd, then ~/.claude/CLAUDE.md (merged)."""
    paths: list[Path] = []
    if cwd:
        p = Path(cwd) / "CLAUDE.md"
        if p.is_file():
            paths.append(p)
    home = Path.home() / ".claude" / "CLAUDE.md"
    if home.is_file():
        paths.append(home)
    merged = Rules()
    for p in paths:
        try:
            r = parse(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        if r.max_agents is not None:
            merged.max_agents = min(r.max_agents, merged.max_agents or r.max_agents)
        if r.max_complexity is not None:
            merged.max_complexity = min(
                r.max_complexity, merged.max_complexity or r.max_complexity
            )
        merged.banned_skills |= r.banned_skills
        for k, v in r.required_skills.items():
            merged.required_skills.setdefault(k, v)
        merged.notes.extend(r.notes)
    return merged


def apply(
    rules: Rules,
    intent: str,
    complexity: float,
    skills: list[str],
    agents: int,
) -> tuple[list[str], int]:
    """Return (skills, agents) adjusted per rules."""
    if rules.banned_skills:
        skills = [s for s in skills if s not in rules.banned_skills]
    req = rules.required_skills.get(intent)
    if req and req not in skills:
        skills = [req, *skills]
    if rules.max_agents is not None:
        agents = min(agents, rules.max_agents)
    if rules.max_complexity is not None and complexity > rules.max_complexity:
        agents = 0
    return skills, agents
