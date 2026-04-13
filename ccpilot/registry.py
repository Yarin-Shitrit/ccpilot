"""Dynamic registry of skills, MCP servers, and plugins on the local machine."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
CACHE = CLAUDE_DIR / "ccpilot" / "registry.json"

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


@dataclass
class Skill:
    name: str
    path: str
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Registry:
    skills: list[Skill] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "skills": [s.__dict__ for s in self.skills],
            "mcp_servers": self.mcp_servers,
        }


def _parse_skill(md: Path) -> Skill | None:
    try:
        text = md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    name = md.parent.name
    desc = ""
    tags: list[str] = []
    m = _FRONTMATTER.search(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                if k == "name" and v:
                    name = v
                elif k == "description":
                    desc = v
                elif k in ("tags", "keywords"):
                    tags = [t.strip() for t in v.strip("[]").split(",") if t.strip()]
    else:
        # fallback: first non-empty line
        for line in text.splitlines():
            if line.strip():
                desc = line.strip().lstrip("# ").strip()
                break
    return Skill(name=name, path=str(md), description=desc, tags=tags)


def build(claude_dir: Path = CLAUDE_DIR) -> Registry:
    reg = Registry()
    skills_dir = claude_dir / "skills"
    if skills_dir.is_dir():
        # Many skills ship alongside a `.ccpilot` twin with identical content
        # (legacy packaging artifact). Collapse to one entry per name, preferring
        # the non-suffixed path so the classifier isn't scoring duplicates.
        collected: list[Skill] = []
        for md in skills_dir.glob("*/SKILL.md"):
            s = _parse_skill(md)
            if s:
                collected.append(s)
        by_name: dict[str, Skill] = {}
        for s in collected:
            existing = by_name.get(s.name)
            if existing is None or ".ccpilot" in existing.path:
                by_name[s.name] = s
        reg.skills = list(by_name.values())
    mcp_file = claude_dir / ".mcp.json"
    if mcp_file.is_file():
        try:
            data = json.loads(mcp_file.read_text())
            reg.mcp_servers = list((data.get("mcpServers") or {}).keys())
        except (OSError, json.JSONDecodeError):
            pass
    return reg


def load_or_build(claude_dir: Path = CLAUDE_DIR) -> Registry:
    if CACHE.is_file():
        try:
            data = json.loads(CACHE.read_text())
            reg = Registry()
            reg.skills = [Skill(**s) for s in data.get("skills", [])]
            reg.mcp_servers = list(data.get("mcp_servers", []))
            return reg
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    reg = build(claude_dir)
    save(reg)
    return reg


def save(reg: Registry) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(reg.to_dict(), indent=2))


_INTENT_TAG_MAP = {
    "design_ui": ("ui", "design", "css", "tailwind", "react", "accessibility"),
    "security": ("security", "audit", "vuln", "owasp"),
    "devops": ("docker", "k8s", "terraform", "ci", "cd", "pipeline", "deploy"),
    "multi_file_research": ("explore", "research", "map"),
    "planning": ("plan", "architecture", "design-doc"),
    "external_web": ("web", "browser", "scrape"),
    "scoped_edit": ("refactor", "edit", "code"),
    "quick_answer": ("explain", "debug", "regex", "stack", "lookup", "git", "docs", "decode", "trace"),
}


def semantic_top(reg: Registry, prompt_low: str, threshold: float = 0.15) -> list[Skill]:
    """Return top-matching skills by semantic score if the best hit clears threshold.

    Used by the router to promote a prompt classified as "trivial" into
    "quick_answer" when a short/simple prompt still has a clearly relevant
    skill (e.g. "explain this stack trace" → stack-trace-explainer).
    """
    if not reg.skills or not prompt_low.strip():
        return []
    from . import search as _search
    idx = _search.Index()
    idx.build((s.name, f"{s.name} {s.description} {' '.join(s.tags)}") for s in reg.skills)
    hits = idx.query(prompt_low, k=3)
    if not hits or hits[0].score < threshold:
        return []
    by_name = {s.name: s for s in reg.skills}
    return [by_name[h.name] for h in hits if h.name in by_name and h.score >= threshold * 0.6]


def pick_skills(
    reg: Registry,
    intent: str,
    prompt_low: str,
    limit: int = 4,
    semantic: bool = False,
) -> list[Skill]:
    tags = _INTENT_TAG_MAP.get(intent, ())
    scored: dict[str, float] = {}
    by_name = {s.name: s for s in reg.skills}
    for s in reg.skills:
        score = 0.0
        hay = (s.name + " " + s.description + " " + " ".join(s.tags)).lower()
        for t in tags:
            if t in hay:
                score += 1.0
        for word in s.name.lower().replace("-", " ").split():
            if word and word in prompt_low:
                score += 0.5
        if score > 0:
            scored[s.name] = score
    if semantic and reg.skills and prompt_low.strip():
        from . import search as _search
        idx = _search.Index()
        idx.build((s.name, f"{s.name} {s.description} {' '.join(s.tags)}") for s in reg.skills)
        for hit in idx.query(prompt_low, k=limit * 2):
            scored[hit.name] = scored.get(hit.name, 0.0) + hit.score * 2.0
    ranked = sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
    return [by_name[n] for n, _ in ranked[:limit] if n in by_name]
