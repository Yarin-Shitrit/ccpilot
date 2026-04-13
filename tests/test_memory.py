from ccpilot import memory


def test_nudge_zero_without_data(tmp_path):
    assert memory.nudge("security", tmp_path / "m.sqlite") == 0.0


def test_nudge_positive_after_successes(tmp_path):
    p = tmp_path / "m.sqlite"
    for _ in range(6):
        memory.record("security", True, p)
    assert memory.nudge("security", p) > 0


def test_nudge_negative_after_failures(tmp_path):
    p = tmp_path / "m.sqlite"
    for _ in range(6):
        memory.record("devops", False, p)
    assert memory.nudge("devops", p) < 0
