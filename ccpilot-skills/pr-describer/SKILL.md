---
name: pr-describer
description: Draft PR titles and descriptions from commits + diff.
tags: [git, pr, review]
---

# pr-describer

Draft PR titles and descriptions from commits + diff.

## When to use
Invoke this skill when the user's request matches any of: git, pr, review.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
