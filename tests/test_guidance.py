from ccpilot import guidance


def test_parse_rules():
    md = """
# Project

## Rules
- never spawn more than 2 agents
- never use skill dangerous-skill
- require skill security-audit for security
- max complexity 0.8
- remember to write tests
"""
    r = guidance.parse(md)
    assert r.max_agents == 2
    assert "dangerous-skill" in r.banned_skills
    assert r.required_skills["security"] == "security-audit"
    assert r.max_complexity == 0.8
    assert any("tests" in n for n in r.notes)


def test_apply_caps_agents_and_bans():
    r = guidance.Rules(max_agents=2, banned_skills={"x"})
    skills, agents = guidance.apply(r, "security", 0.5, ["x", "y"], 5)
    assert agents == 2 and "x" not in skills


def test_apply_complexity_floor_zero_agents():
    r = guidance.Rules(max_complexity=0.3)
    _, agents = guidance.apply(r, "security", 0.9, [], 4)
    assert agents == 0


def test_apply_required_skill_injected():
    r = guidance.Rules(required_skills={"security": "security-audit"})
    skills, _ = guidance.apply(r, "security", 0.5, [], 1)
    assert skills == ["security-audit"]
