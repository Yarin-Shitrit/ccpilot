---
name: migration-writer
description: Scaffold DB migrations (alembic, knex, goose, etc).
tags: [migration, database, schema]
---

# migration-writer

Scaffold DB migrations (alembic, knex, goose, etc).

## When to use
Invoke this skill when the user's request matches any of: migration, database, schema.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
