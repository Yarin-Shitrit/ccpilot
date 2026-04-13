"""Generate the top-30 SKILL.md files from a manifest. Run once at build time."""
from __future__ import annotations

import sys
from pathlib import Path

SKILLS = [
    ("code-review", "Diff-aware code review: critique correctness, style, safety.", ["review", "code", "diff"]),
    ("security-audit", "Audit code/deps for OWASP Top 10 and common CWE issues.", ["security", "owasp", "vuln", "audit"]),
    ("test-writer", "Generate unit and integration tests for the target code.", ["test", "pytest", "jest"]),
    ("refactor-assistant", "Plan and execute safe multi-file refactors.", ["refactor", "edit", "code"]),
    ("doc-generator", "Write README/ADR/API docs from code or diffs.", ["docs", "readme", "adr"]),
    ("dependency-auditor", "Scan lockfiles for outdated or vulnerable deps.", ["deps", "cve", "audit"]),
    ("perf-profiler", "Identify performance hotspots and propose fixes.", ["performance", "profile"]),
    ("sql-optimizer", "Analyze and rewrite slow SQL; suggest indexes.", ["sql", "database", "index"]),
    ("api-designer", "Design REST/GraphQL schemas and endpoints.", ["api", "rest", "graphql"]),
    ("migration-writer", "Scaffold DB migrations (alembic, knex, goose, etc).", ["migration", "database", "schema"]),
    ("ci-cd-builder", "Author GitHub Actions / GitLab CI / Jenkins pipelines.", ["ci", "cd", "pipeline", "deploy"]),
    ("dockerfile-optimizer", "Shrink and harden Dockerfiles (multi-stage, non-root).", ["docker", "container", "deploy"]),
    ("k8s-manifest-writer", "Generate/lint Kubernetes manifests and Helm charts.", ["k8s", "kubernetes", "helm", "deploy"]),
    ("terraform-scaffolder", "Scaffold Terraform modules with sane defaults.", ["terraform", "iac", "deploy"]),
    ("log-analyzer", "Parse log excerpts, cluster errors, surface anomalies.", ["logs", "observability"]),
    ("stack-trace-explainer", "Explain a stack trace and map to source locations.", ["debug", "trace", "error"]),
    ("regex-builder", "Construct and explain regular expressions from examples.", ["regex", "pattern"]),
    ("commit-message-writer", "Write conventional-commit messages from a diff.", ["git", "commit"]),
    ("pr-describer", "Draft PR titles and descriptions from commits + diff.", ["git", "pr", "review"]),
    ("changelog-generator", "Produce a changelog entry grouped by type.", ["changelog", "release"]),
    ("architecture-diagrammer", "Emit mermaid diagrams for system architecture.", ["architecture", "diagram", "mermaid", "design"]),
    ("error-triage", "Triage an incoming error/bug report and propose next steps.", ["debug", "triage", "bug"]),
    ("accessibility-reviewer", "Review UI for WCAG/a11y issues.", ["accessibility", "a11y", "ui"]),
    ("i18n-extractor", "Extract strings for internationalization.", ["i18n", "l10n", "ui"]),
    ("config-linter", "Lint JSON/YAML/TOML configs against schemas.", ["config", "lint"]),
    ("env-doctor", "Diagnose local dev-env failures (paths, versions, tools).", ["env", "setup", "debug"]),
    ("git-archaeologist", "Reason over git blame/log to explain code history.", ["git", "history", "blame"]),
    ("license-checker", "Check dependency licenses against an allow-list.", ["license", "compliance", "deps"]),
    ("prompt-improver", "Rewrite ambiguous user prompts into crisp requirements.", ["prompt", "meta"]),
    ("release-notes-writer", "Draft user-facing release notes from a changelog.", ["release", "docs"]),
]

TEMPLATE = """---
name: {name}
description: {desc}
tags: [{tags}]
---

# {name}

{desc}

## When to use
Invoke this skill when the user's request matches any of: {tags}.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
"""


def main(root: Path) -> int:
    for name, desc, tags in SKILLS:
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(
            TEMPLATE.format(name=name, desc=desc, tags=", ".join(tags))
        )
    print(f"wrote {len(SKILLS)} skills to {root}")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "ccpilot-skills"
    sys.exit(main(root))
