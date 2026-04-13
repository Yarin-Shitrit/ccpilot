---
name: k8s-manifest-writer
description: Generate/lint Kubernetes manifests and Helm charts.
tags: [k8s, kubernetes, helm, deploy]
---

# k8s-manifest-writer

Generate/lint Kubernetes manifests and Helm charts.

## When to use
Invoke this skill when the user's request matches any of: k8s, kubernetes, helm, deploy.

## Approach
1. Read the minimum context required (focus files, diffs, or configs).
2. Produce the concrete artifact the user needs — not an outline.
3. Flag risks or unknowns explicitly instead of guessing.
