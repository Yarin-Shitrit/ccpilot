import io
import json
import sys

from ccpilot import route


def test_route_emits_block_for_security(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(route, "LOG_PATH", tmp_path / "log.jsonl")
    payload = {"prompt": "audit this repo for security issues across the codebase"}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    rc = route.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "ccpilot-routing" in out
    assert "security" in out


def test_route_disabled_via_env(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("CCPILOT_DISABLED", "1")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"prompt": "audit security"})))
    rc = route.main()
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_route_silent_for_trivial(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(route, "LOG_PATH", tmp_path / "log.jsonl")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"prompt": "hi"})))
    rc = route.main()
    assert rc == 0
    assert capsys.readouterr().out == ""
