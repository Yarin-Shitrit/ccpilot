"""Raft-lite quorum consensus over agent proposals.

Cooperating (not adversarial) agents — we only need quorum voting with
tiebreak. Optional Byzantine-lite mode requires 2f+1 agreement of 3f+1.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Proposal:
    agent_id: str
    role: str
    value: Any  # canonical-hashable representation of the answer
    confidence: float = 0.5
    raw: Any = None  # original full output
    ok: bool = True


@dataclass
class ConsensusResult:
    winner: Any
    votes: int
    total: int
    quorum: int
    reached: bool
    tiebreaker_used: bool
    proposals: list[Proposal]


def quorum_size(n: int, byzantine: bool = False) -> int:
    if byzantine:
        # Need 2f+1 of 3f+1; given n, the largest f is (n-1)//3
        f = max((n - 1) // 3, 0)
        return 2 * f + 1
    return n // 2 + 1


def tally(
    proposals: list[Proposal],
    byzantine: bool = False,
    judge: Callable[[list[Proposal]], Proposal] | None = None,
) -> ConsensusResult:
    valid = [p for p in proposals if p.ok]
    n = len(valid)
    q = quorum_size(n or 1, byzantine=byzantine)
    counts = Counter(p.value for p in valid)
    if not counts:
        return ConsensusResult(None, 0, 0, q, False, False, proposals)

    top_value, top_votes = counts.most_common(1)[0]
    tied = [v for v, c in counts.items() if c == top_votes]
    tiebreaker_used = False

    if len(tied) > 1:
        tied_props = [p for p in valid if p.value in tied]
        if judge is not None:
            winner_prop = judge(tied_props)
            top_value = winner_prop.value
            tiebreaker_used = True
        else:
            # Break tie by highest confidence, then first seen
            winner_prop = max(tied_props, key=lambda p: (p.confidence, -valid.index(p)))
            top_value = winner_prop.value
            tiebreaker_used = True

    return ConsensusResult(
        winner=top_value,
        votes=counts[top_value],
        total=n,
        quorum=q,
        reached=counts[top_value] >= q,
        tiebreaker_used=tiebreaker_used,
        proposals=proposals,
    )
