from ccpilot import classifier


def test_trivial():
    c = classifier.classify("hi")
    assert c.intent == "trivial"


def test_security_audit():
    c = classifier.classify("please audit this repo for security vulnerabilities and OWASP issues")
    assert c.intent == "security"
    assert c.complexity > 0.2


def test_design_ui():
    c = classifier.classify("redesign the landing page with a modern UI and better layout")
    assert c.intent == "design_ui"


def test_scoped_edit():
    c = classifier.classify("fix the typo in README.md")
    assert c.intent == "scoped_edit"


def test_complexity_scales_with_length():
    short = classifier.classify("fix bug")
    long = classifier.classify(
        "refactor the payment module across services, redesign the api, and audit for security" * 3
    )
    assert long.complexity > short.complexity
