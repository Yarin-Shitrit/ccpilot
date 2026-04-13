"""Prompt complexity + intent classifier. Tier 1 heuristics, optional Tier 2 LLM."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

INTENTS = (
    "trivial",
    "quick_answer",
    "scoped_edit",
    "multi_file_research",
    "design_ui",
    "planning",
    "external_web",
    "security",
    "devops",
)

_VERBS = {
    "design_ui": r"\b(design|redesign|style|restyle|theme|layout|mockup|prototype|ui|ux)\b",
    "security": r"\b(audit|cve|vuln|exploit|owasp|secure|security|pentest)\b",
    "devops": r"\b(deploy|docker|k8s|kubernetes|terraform|pipeline|ci/?cd|helm)\b",
    "multi_file_research": (
        r"\b(audit|explore|map|survey|investigate|analyze|analyse|summarize|summarise|"
        r"overview|review the|walk through|deep[- ]?dive|understand (the|this)|"
        r"(entire|whole|full|complete) (codebase|project|repo|repository)|"
        r"across (the|this) (repo|codebase|project)|large project|big project)\b"
    ),
    "planning": r"\b(plan|architect|propose|design doc|rfc|adr|strategy|roadmap)\b",
    "external_web": r"\b(fetch|scrape|browser|web search|http get|curl|download)\b",
    "scoped_edit": r"\b(fix|rename|refactor|add|remove|update|tweak|change)\b",
    "quick_answer": r"\b(explain|decode|parse|lookup|what (is|does|are)|why does|meaning of|regex for|translate|convert|format)\b",
}

_SCALE_TERMS = (
    "large", "huge", "entire", "whole", "full", "complete", "comprehensive",
    "thorough", "in-depth", "deep", "codebase", "repository", "monorepo",
    "project-wide", "architecture", "system-wide",
)

_FILE_REF = re.compile(r"[\w./-]+\.[a-zA-Z]{1,6}\b")
_CODE_FENCE = re.compile(r"```")


@dataclass
class Classification:
    intent: str
    complexity: float  # 0..1
    confidence: float  # 0..1
    signals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "complexity": round(self.complexity, 3),
            "confidence": round(self.confidence, 3),
            "signals": self.signals,
        }


def classify(prompt: str) -> Classification:
    text = prompt.strip()
    low = text.lower()
    words = text.split()
    word_count = len(words)
    file_refs = len(_FILE_REF.findall(text))
    fences = len(_CODE_FENCE.findall(text))
    question = text.endswith("?") or low.startswith(("what", "why", "how", "can you explain"))

    scores: dict[str, float] = {}
    for intent, pat in _VERBS.items():
        hits = len(re.findall(pat, low))
        if hits:
            scores[intent] = scores.get(intent, 0.0) + hits

    # Complexity score 0..1
    complexity = 0.0
    complexity += min(word_count / 80.0, 0.4)
    complexity += min(file_refs * 0.05, 0.15)
    complexity += min(fences * 0.05, 0.1)
    if any(k in low for k in ("audit", "refactor across", "redesign", "rewrite", "migrate")):
        complexity += 0.2
    if any(k in low for k in ("multiple", "each", "all the", "every")):
        complexity += 0.1
    scale_hits = sum(1 for t in _SCALE_TERMS if t in low)
    complexity += min(scale_hits * 0.1, 0.3)
    # Research/security/planning prompts are inherently complex — floor lifted.
    complexity = min(complexity, 1.0)

    if not text:
        intent = "trivial"
    elif word_count < 6 and not scores:
        intent = "trivial"
    elif question and word_count < 30 and not scores:
        intent = "trivial"
    elif scores:
        intent = max(scores, key=lambda k: scores[k])
    else:
        intent = "scoped_edit"

    # Floor complexity for inherently-heavy intents so they cross the swarm threshold.
    if intent in ("multi_file_research", "security", "planning"):
        complexity = max(complexity, 0.55)

    # Confidence: gap between top two intents (or heuristic fallback)
    if scores:
        sorted_s = sorted(scores.values(), reverse=True)
        top = sorted_s[0]
        second = sorted_s[1] if len(sorted_s) > 1 else 0
        confidence = min(0.5 + (top - second) * 0.2, 0.95)
    else:
        confidence = 0.55 if intent == "trivial" else 0.45

    return Classification(
        intent=intent,
        complexity=complexity,
        confidence=confidence,
        signals={
            "words": word_count,
            "file_refs": file_refs,
            "fences": fences,
            "intent_scores": scores,
        },
    )


def maybe_escalate(prompt: str, c: Classification, cfg: dict[str, Any]) -> Classification:
    """Optional LLM re-classification. Returns original on any failure."""
    cls_cfg = cfg.get("classifier", {})
    if not cls_cfg.get("llm_escalation"):
        return c
    if c.confidence >= cls_cfg.get("confidence_threshold", 0.6):
        return c
    try:
        from .llm.client import classify_via_llm

        refined = classify_via_llm(prompt, cls_cfg)
        if refined:
            return refined
    except Exception:
        pass
    return c
