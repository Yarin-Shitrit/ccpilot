---
name: prompt-improver
description: Rewrite ambiguous user prompts into crisp requirements.
tags: [prompt, meta]
---

# prompt-improver

Rewrite ambiguous user prompts into crisp requirements.

## When to use
Invoke this skill when the user's request matches any of: prompt, meta.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
