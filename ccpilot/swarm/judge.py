"""Default judge: confidence-weighted winner. Plug in an LLM judge if desired."""
from __future__ import annotations

from .consensus import Proposal


def default_judge(tied: list[Proposal]) -> Proposal:
    if not tied:
        raise ValueError("no tied proposals to judge")
    return max(tied, key=lambda p: p.confidence)
