---
name: test-writer
description: Generate unit and integration tests for the target code.
tags: [test, pytest, jest]
---

# test-writer

Generate unit and integration tests for the target code.

## When to use
Invoke this skill when the user's request matches any of: test, pytest, jest.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
