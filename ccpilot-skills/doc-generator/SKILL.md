---
name: doc-generator
description: Write README/ADR/API docs from code or diffs.
tags: [docs, readme, adr]
---

# doc-generator

Write README/ADR/API docs from code or diffs.

## When to use
Invoke this skill when the user's request matches any of: docs, readme, adr.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
