from ccpilot import search


def test_semantic_rank_finds_relevant():
    idx = search.Index()
    idx.build([
        ("ui-styling", "tailwind css styling for react components"),
        ("sql-optimizer", "postgres query planner index tuning"),
        ("security-audit", "owasp cwe vulnerability scan"),
    ])
    hits = idx.query("redesign the landing page with tailwind", k=2)
    assert hits and hits[0].name == "ui-styling"


def test_empty_query_returns_nothing():
    idx = search.Index()
    idx.build([("a", "hello"), ("b", "world")])
    assert idx.query("", k=3) == []
