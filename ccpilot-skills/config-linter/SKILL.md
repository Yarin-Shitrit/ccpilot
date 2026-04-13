---
name: config-linter
description: Lint JSON/YAML/TOML configs against schemas.
tags: [config, lint]
---

# config-linter

Lint JSON/YAML/TOML configs against schemas.

## When to use
Invoke this skill when the user's request matches any of: config, lint.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
