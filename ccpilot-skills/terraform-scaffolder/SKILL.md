---
name: terraform-scaffolder
description: Scaffold Terraform modules with sane defaults.
tags: [terraform, iac, deploy]
---

# terraform-scaffolder

Scaffold Terraform modules with sane defaults.

## When to use
Invoke this skill when the user's request matches any of: terraform, iac, deploy.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
