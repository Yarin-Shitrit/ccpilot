"""Role catalog for swarm agents."""
from __future__ import annotations

from dataclasses import dataclass

ROLE_PROMPTS: dict[str, str] = {
    "orchestrator": "Coordinate the swarm. Break the task into subtasks and assign.",
    "explorer": "Read the codebase to gather facts. Report file paths and structure.",
    "implementer": "Propose concrete code changes with diffs.",
    "reviewer": "Critique proposed changes for correctness, safety, and style.",
    "tester": "Write or identify tests that verify the change.",
    "security-auditor": "Audit for OWASP/CWE issues, unsafe patterns, secret leaks.",
    "ui-designer": "Propose UI/UX improvements with concrete component/style choices.",
    "doc-writer": "Draft or update documentation for the change.",
    "judge": "Given disagreeing proposals, pick the winner with a short rationale.",
}


@dataclass
class Role:
    name: str
    prompt: str

    @classmethod
    def get(cls, name: str) -> "Role":
        return cls(name=name, prompt=ROLE_PROMPTS.get(name, f"Act as a {name}."))
