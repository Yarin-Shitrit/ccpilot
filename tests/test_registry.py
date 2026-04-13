from pathlib import Path

from ccpilot import registry


def test_build_from_tmp(tmp_path: Path):
    skills = tmp_path / "skills" / "demo-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: demo\ntags: [demo, ui]\n---\n# demo"
    )
    reg = registry.build(tmp_path)
    assert any(s.name == "demo-skill" for s in reg.skills)


def test_pick_skills_matches_tags(tmp_path: Path):
    reg = registry.Registry(skills=[
        registry.Skill(name="ui-styling", path="", description="styling", tags=["ui", "design"]),
        registry.Skill(name="sql-optimizer", path="", description="sql", tags=["sql"]),
    ])
    picks = registry.pick_skills(reg, "design_ui", "redesign the landing page")
    assert picks and picks[0].name == "ui-styling"
