---
name: dependency-auditor
description: Scan lockfiles for outdated or vulnerable deps.
tags: [deps, cve, audit]
---

# dependency-auditor

Scan lockfiles for outdated or vulnerable deps.

## When to use
Invoke this skill when the user's request matches any of: deps, cve, audit.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
