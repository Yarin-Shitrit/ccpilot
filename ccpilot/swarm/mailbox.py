"""SQLite-backed task queue + inter-agent mailbox.

Enables ruflo-style "agent teams" coordination: a coordinator writes tasks,
role-specialized workers claim them, post results, and exchange messages —
all through a single sqlite file so the scheme survives across process
boundaries and Claude Code sessions.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path.home() / ".claude" / "ccpilot" / "mailbox.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks(
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    created_at REAL NOT NULL,
    claimed_at REAL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at REAL NOT NULL,
    read_at REAL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, role);
CREATE INDEX IF NOT EXISTS idx_msg_to ON messages(to_agent, read_at);
"""


@dataclass
class Task:
    id: str
    role: str
    payload: dict
    status: str = "pending"
    result: dict | None = None


class Mailbox:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def post_task(self, role: str, payload: dict) -> str:
        tid = uuid.uuid4().hex[:12]
        with self._conn() as c:
            c.execute(
                "INSERT INTO tasks(id, role, payload, created_at) VALUES (?, ?, ?, ?)",
                (tid, role, json.dumps(payload), time.time()),
            )
        return tid

    def claim(self, role: str) -> Task | None:
        with self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute(
                "SELECT id, payload FROM tasks WHERE status='pending' AND role=? "
                "ORDER BY created_at LIMIT 1",
                (role,),
            ).fetchone()
            if not row:
                c.execute("COMMIT")
                return None
            tid, payload = row
            c.execute(
                "UPDATE tasks SET status='claimed', claimed_at=? WHERE id=?",
                (time.time(), tid),
            )
            c.execute("COMMIT")
            return Task(id=tid, role=role, payload=json.loads(payload), status="claimed")

    def finish(self, task_id: str, result: dict) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET status='done', result=?, finished_at=? WHERE id=?",
                (json.dumps(result), time.time(), task_id),
            )

    def results(self, ids: list[str]) -> dict[str, dict]:
        if not ids:
            return {}
        q = "SELECT id, result FROM tasks WHERE id IN (%s)" % ",".join("?" * len(ids))
        with self._conn() as c:
            return {
                tid: json.loads(r)
                for tid, r in c.execute(q, ids).fetchall()
                if r
            }

    def send(self, from_agent: str, to_agent: str, body: dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO messages(from_agent, to_agent, body, created_at) VALUES (?,?,?,?)",
                (from_agent, to_agent, json.dumps(body), time.time()),
            )

    def inbox(self, agent: str, mark_read: bool = True) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, from_agent, body FROM messages WHERE to_agent=? AND read_at IS NULL "
                "ORDER BY created_at",
                (agent,),
            ).fetchall()
            msgs = [{"id": r[0], "from": r[1], "body": json.loads(r[2])} for r in rows]
            if mark_read and rows:
                ids = [r[0] for r in rows]
                q = "UPDATE messages SET read_at=? WHERE id IN (%s)" % ",".join("?" * len(ids))
                c.execute(q, [time.time(), *ids])
        return msgs
