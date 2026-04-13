#!/usr/bin/env sh
# ccpilot PostToolUse learning hook (POSIX). Fails open.
set -u
PY="${CCPILOT_PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    PY=python
fi
if ! command -v "$PY" >/dev/null 2>&1; then
    exit 0
fi
"$PY" -m ccpilot learn 2>>"${HOME}/.claude/ccpilot/hook.err" || exit 0
