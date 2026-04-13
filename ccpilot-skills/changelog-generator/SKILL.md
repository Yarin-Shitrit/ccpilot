---
name: changelog-generator
description: Produce a changelog entry grouped by type.
tags: [changelog, release]
---

# changelog-generator

Produce a changelog entry grouped by type.

## When to use
Invoke this skill when the user's request matches any of: changelog, release.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
