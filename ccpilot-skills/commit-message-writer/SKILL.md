---
name: commit-message-writer
description: Write conventional-commit messages from a diff.
tags: [git, commit]
---

# commit-message-writer

Write conventional-commit messages from a diff.

## When to use
Invoke this skill when the user's request matches any of: git, commit.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
