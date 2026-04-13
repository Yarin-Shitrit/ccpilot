"""LLM classifier client for a private Claude/OpenAI-compatible endpoint.

Prefers the official `anthropic` SDK (or `openai` SDK when protocol=openai).
Falls back to a stdlib HTTP call so ccpilot still works with zero deps.
Returns None on any failure so the caller keeps its heuristic result.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ..classifier import INTENTS, Classification

_PROMPT_TEMPLATE = (
    "Classify this developer prompt. Respond with strict JSON: "
    '{"intent": "<one of: %s>", "complexity": <0..1>, "confidence": <0..1>}.\n\n'
    "PROMPT:\n%s"
)


def _build_prompt(prompt: str) -> str:
    return _PROMPT_TEMPLATE % (", ".join(INTENTS), prompt[:4000])


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _to_classification(obj: dict[str, Any], source: str) -> Classification | None:
    intent = str(obj.get("intent", "")).strip()
    if intent not in INTENTS:
        return None
    try:
        return Classification(
            intent=intent,
            complexity=float(obj.get("complexity", 0.5)),
            confidence=float(obj.get("confidence", 0.7)),
            signals={"source": source},
        )
    except (TypeError, ValueError):
        return None


def _via_anthropic_sdk(prompt: str, base: str, model: str, api_key: str, timeout: int) -> Classification | None:
    try:
        from anthropic import Anthropic  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        client = Anthropic(base_url=base or None, api_key=api_key or None, timeout=timeout)
        resp = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": _build_prompt(prompt)}],
        )
        text = resp.content[0].text  # type: ignore[attr-defined]
    except Exception:
        return None
    obj = _parse_json_obj(text)
    return _to_classification(obj, "anthropic-sdk") if obj else None


def _via_openai_sdk(prompt: str, base: str, model: str, api_key: str, timeout: int) -> Classification | None:
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        client = OpenAI(base_url=base or None, api_key=api_key or "sk-missing", timeout=timeout)
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": _build_prompt(prompt)}],
        )
        text = resp.choices[0].message.content or ""
    except Exception:
        return None
    obj = _parse_json_obj(text)
    return _to_classification(obj, "openai-sdk") if obj else None


def _via_stdlib_http(prompt: str, base: str, model: str, api_key: str, timeout: int) -> Classification | None:
    if not base:
        return None
    headers = {"Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    if api_key:
        headers["x-api-key"] = api_key
    body = {
        "model": model,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": _build_prompt(prompt)}],
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/messages",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["content"][0]["text"]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, KeyError, IndexError, OSError):
        return None
    obj = _parse_json_obj(text)
    return _to_classification(obj, "stdlib-http") if obj else None


def classify_via_llm(prompt: str, cls_cfg: dict[str, Any]) -> Classification | None:
    base = (cls_cfg.get("base_url") or "").rstrip("/")
    model = cls_cfg.get("model") or ""
    if not model:
        return None
    api_key = os.environ.get(cls_cfg.get("api_key_env", "CLAUDE_API_KEY"), "")
    timeout = int(cls_cfg.get("timeout_s", 8))
    protocol = (cls_cfg.get("protocol") or "anthropic").lower()

    if protocol == "openai":
        result = _via_openai_sdk(prompt, base, model, api_key, timeout)
        if result:
            return result
        # No stdlib fallback for OpenAI shape — too divergent to hand-roll here.
        return None

    # Anthropic protocol: SDK first, then stdlib HTTP fallback.
    result = _via_anthropic_sdk(prompt, base, model, api_key, timeout)
    if result:
        return result
    return _via_stdlib_http(prompt, base, model, api_key, timeout)
