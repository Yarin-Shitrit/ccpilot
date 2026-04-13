---
name: env-doctor
description: Diagnose local dev-env failures (paths, versions, tools).
tags: [env, setup, debug]
---

# env-doctor

Diagnose local dev-env failures (paths, versions, tools).

## When to use
Invoke this skill when the user's request matches any of: env, setup, debug.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
