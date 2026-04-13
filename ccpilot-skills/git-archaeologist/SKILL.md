---
name: git-archaeologist
description: Reason over git blame/log to explain code history.
tags: [git, history, blame]
---

# git-archaeologist

Reason over git blame/log to explain code history.

## When to use
Invoke this skill when the user's request matches any of: git, history, blame.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
