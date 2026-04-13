---
name: stack-trace-explainer
description: Explain a stack trace and map to source locations.
tags: [debug, trace, error]
---

# stack-trace-explainer

Explain a stack trace and map to source locations.

## When to use
Invoke this skill when the user's request matches any of: debug, trace, error.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
