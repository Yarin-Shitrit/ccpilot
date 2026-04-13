"""Semantic search over skills/memory.

Stdlib fallback: hashed-ngram TF-IDF cosine (sub-ms at <500 skills, but
collapses on morphology — "auth" vs "authentication" miss).

Upgrade path: if `model2vec` is installed (ccpilot[smart]), a static dense
embedding (numpy-only, ~30MB, <50ms cold import) replaces hashed TF-IDF
transparently. Catches paraphrases the stdlib path misses without dragging
in torch/transformers on the hot hook path.
"""
from __future__ import annotations

import math
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_USE_DENSE = os.environ.get("CCPILOT_DENSE", "1").strip().lower() not in ("0", "false", "no", "off")

CACHE = Path.home() / ".claude" / "ccpilot" / "vectors.sqlite"
_TOKEN = re.compile(r"[a-z0-9]{2,}")
_NGRAM = 3
_DIM = 1024  # hash dim for stdlib TF-IDF


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _hash_vec(text: str, dim: int = _DIM) -> dict[int, float]:
    """Hashed ngram TF. Returns sparse {idx: weight}."""
    toks = _tokens(text)
    vec: dict[int, float] = {}
    grams: list[str] = list(toks)
    for n in (2, _NGRAM):
        grams.extend(" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1))
    for g in grams:
        idx = hash(g) % dim
        vec[idx] = vec.get(idx, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / norm for k, v in vec.items()}


def _cosine_sparse(a: dict[int, float], b: dict[int, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


@dataclass
class Hit:
    name: str
    score: float


_DENSE_MODEL = None  # lazy singleton


def _load_dense_model():
    """Return a model2vec StaticModel, or None if the lib isn't available."""
    global _DENSE_MODEL
    if _DENSE_MODEL is not None:
        return _DENSE_MODEL
    if not _USE_DENSE:
        return None
    try:
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
        from model2vec import StaticModel  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        # Tiny static model — pure numpy at query time, no torch required.
        _DENSE_MODEL = StaticModel.from_pretrained("minishlab/potion-base-8M")
        return _DENSE_MODEL
    except Exception:
        return None


class Index:
    """Skill index. Uses model2vec dense embeddings when available, else hashed TF-IDF."""

    def __init__(self) -> None:
        self._docs: list[tuple[str, dict[int, float]]] = []
        self._dense_names: list[str] = []
        self._dense_vecs = None  # np.ndarray | None
        self._model = _load_dense_model()

    def add(self, name: str, text: str) -> None:
        # Incremental add only supported on sparse path; dense path uses build().
        self._docs.append((name, _hash_vec(text)))

    def build(self, items: Iterable[tuple[str, str]]) -> None:
        items_list = list(items)
        if self._model is not None:
            try:
                import numpy as np
                names = [n for n, _ in items_list]
                texts = [t for _, t in items_list]
                vecs = self._model.encode(texts)
                norms = np.linalg.norm(vecs, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self._dense_vecs = vecs / norms
                self._dense_names = names
                return
            except Exception:
                self._dense_vecs = None
                self._dense_names = []
        self._docs = [(n, _hash_vec(t)) for n, t in items_list]

    def query(self, text: str, k: int = 5) -> list[Hit]:
        if self._dense_vecs is not None and self._model is not None:
            try:
                import numpy as np
                q = self._model.encode([text])[0]
                n = np.linalg.norm(q) or 1.0
                q = q / n
                scores = self._dense_vecs @ q
                order = np.argsort(-scores)[:k]
                return [Hit(self._dense_names[i], float(scores[i])) for i in order if scores[i] > 0.0]
            except Exception:
                pass
        q = _hash_vec(text)
        scored = [Hit(n, _cosine_sparse(q, v)) for n, v in self._docs]
        scored.sort(key=lambda h: h.score, reverse=True)
        return [h for h in scored[:k] if h.score > 0.0]


def persist(index: Index, path: Path = CACHE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS docs(name TEXT PRIMARY KEY, vec BLOB)")
        con.execute("DELETE FROM docs")
        import json as _json
        con.executemany(
            "INSERT OR REPLACE INTO docs(name, vec) VALUES (?, ?)",
            [(n, _json.dumps(v)) for n, v in index._docs],
        )
        con.commit()


def load(path: Path = CACHE) -> Index | None:
    if not path.is_file():
        return None
    import json as _json
    idx = Index()
    with sqlite3.connect(path) as con:
        for n, blob in con.execute("SELECT name, vec FROM docs"):
            idx._docs.append((n, {int(k): float(v) for k, v in _json.loads(blob).items()}))
    return idx
