---
name: license-checker
description: Check dependency licenses against an allow-list.
tags: [license, compliance, deps]
---

# license-checker

Check dependency licenses against an allow-list.

## When to use
Invoke this skill when the user's request matches any of: license, compliance, deps.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
