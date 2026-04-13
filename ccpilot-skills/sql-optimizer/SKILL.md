---
name: sql-optimizer
description: Analyze and rewrite slow SQL; suggest indexes.
tags: [sql, database, index]
---

# sql-optimizer

Analyze and rewrite slow SQL; suggest indexes.

## When to use
Invoke this skill when the user's request matches any of: sql, database, index.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
