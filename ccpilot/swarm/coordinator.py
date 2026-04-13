"""In-process swarm coordinator.

The SDK cannot directly spawn Claude Code subagents from a hook — those are
spawned by the model via the Agent tool. This coordinator is the offline
harness used for (a) local testing of the consensus logic and (b) when the
SDK is invoked in scripted mode against the private LLM endpoint.
"""
from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .consensus import Proposal, tally
from .judge import default_judge
from .roles import Role

LOG_PATH = Path.home() / ".claude" / "ccpilot" / "swarm.jsonl"


@dataclass
class SwarmConfig:
    roles: list[str]
    byzantine: bool = False
    timeout_s: int = 60
    judge: Callable[[list[Proposal]], Proposal] = default_judge


@dataclass
class SwarmRound:
    round_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.time)
    proposals: list[Proposal] = field(default_factory=list)


AgentFn = Callable[[Role, str], Proposal]
"""An agent function takes a role + task and returns a Proposal."""


def run(task: str, cfg: SwarmConfig, agent_fn: AgentFn) -> dict[str, Any]:
    rnd = SwarmRound()
    roles = [Role.get(r) for r in cfg.roles]
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _run_one(r: Role) -> Proposal:
        try:
            return agent_fn(r, task)
        except Exception as e:  # pragma: no cover - defensive
            return Proposal(
                agent_id=uuid.uuid4().hex[:8],
                role=r.name,
                value=None,
                confidence=0.0,
                raw={"error": str(e)},
                ok=False,
            )

    with ThreadPoolExecutor(max_workers=max(len(roles), 1)) as ex:
        futs = [ex.submit(_run_one, r) for r in roles]
        for fut in as_completed(futs, timeout=cfg.timeout_s):
            try:
                rnd.proposals.append(fut.result(timeout=cfg.timeout_s))
            except Exception:
                continue

    result = tally(rnd.proposals, byzantine=cfg.byzantine, judge=cfg.judge)
    entry = {
        "round_id": rnd.round_id,
        "started_at": rnd.started_at,
        "finished_at": time.time(),
        "byzantine": cfg.byzantine,
        "quorum": result.quorum,
        "votes": result.votes,
        "total": result.total,
        "reached": result.reached,
        "tiebreaker_used": result.tiebreaker_used,
        "winner": result.winner,
        "proposals": [
            {"role": p.role, "agent_id": p.agent_id, "value": p.value, "confidence": p.confidence, "ok": p.ok}
            for p in result.proposals
        ],
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    return entry
