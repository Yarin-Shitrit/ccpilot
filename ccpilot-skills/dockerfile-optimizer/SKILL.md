---
name: dockerfile-optimizer
description: Shrink and harden Dockerfiles (multi-stage, non-root).
tags: [docker, container, deploy]
---

# dockerfile-optimizer

Shrink and harden Dockerfiles (multi-stage, non-root).

## When to use
Invoke this skill when the user's request matches any of: docker, container, deploy.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
