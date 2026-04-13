from ccpilot.swarm.consensus import Proposal, quorum_size, tally


def _p(role, value, conf=0.5, ok=True):
    return Proposal(agent_id=role, role=role, value=value, confidence=conf, ok=ok)


def test_quorum_simple():
    assert quorum_size(3) == 2
    assert quorum_size(5) == 3
    assert quorum_size(4) == 3


def test_quorum_byzantine():
    # n=4 -> f=1 -> need 2f+1=3
    assert quorum_size(4, byzantine=True) == 3
    # n=7 -> f=2 -> need 5
    assert quorum_size(7, byzantine=True) == 5


def test_tally_majority():
    r = tally([_p("a", "x"), _p("b", "x"), _p("c", "y")])
    assert r.winner == "x"
    assert r.reached


def test_tally_tiebreak_by_confidence():
    r = tally([_p("a", "x", conf=0.4), _p("b", "y", conf=0.9)])
    assert r.winner == "y"
    assert r.tiebreaker_used


def test_tally_filters_failed():
    r = tally([_p("a", "x"), _p("b", "x"), _p("c", None, ok=False)])
    assert r.winner == "x"
    assert r.total == 2
