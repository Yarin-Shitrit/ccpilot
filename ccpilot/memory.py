"""Verdict memory — tracks per-intent success/failure for Bayesian confidence nudges.

Piggybacks on the PostToolUse hook (ccpilot/learn.py). For each intent we
keep a Beta(alpha, beta) prior updated from observed outcomes; `nudge()`
returns a small delta in [-0.15, +0.15] added to classifier confidence.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DEFAULT_PATH = Path.home() / ".claude" / "ccpilot" / "memory.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS verdicts(
    intent TEXT PRIMARY KEY,
    alpha REAL NOT NULL DEFAULT 1.0,
    beta REAL NOT NULL DEFAULT 1.0,
    last_update REAL NOT NULL DEFAULT 0
);
"""


def _conn(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    c.executescript(_SCHEMA)
    return c


def record(intent: str, success: bool, path: Path = DEFAULT_PATH) -> None:
    with _conn(path) as c:
        c.execute(
            "INSERT INTO verdicts(intent, alpha, beta, last_update) VALUES(?, ?, ?, ?) "
            "ON CONFLICT(intent) DO UPDATE SET "
            "alpha=alpha+excluded.alpha-1, beta=beta+excluded.beta-1, last_update=excluded.last_update",
            (
                intent,
                1.0 + (1.0 if success else 0.0),
                1.0 + (0.0 if success else 1.0),
                time.time(),
            ),
        )


def nudge(intent: str, path: Path = DEFAULT_PATH) -> float:
    """Return a confidence delta in [-0.15, +0.15] from the Beta posterior mean."""
    if not path.is_file():
        return 0.0
    with _conn(path) as c:
        row = c.execute(
            "SELECT alpha, beta FROM verdicts WHERE intent=?", (intent,)
        ).fetchone()
    if not row:
        return 0.0
    alpha, beta = row
    if alpha + beta < 4:  # need a few observations before trusting
        return 0.0
    mean = alpha / (alpha + beta)
    return max(-0.15, min(0.15, (mean - 0.5) * 0.3))
