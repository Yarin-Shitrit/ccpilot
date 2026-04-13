#!/usr/bin/env sh
# ccpilot UserPromptSubmit hook launcher (POSIX).
# Forwards stdin (hook JSON) to the Python router. Fails open: any error
# exits 0 with no stdout so the user prompt is unaffected.
set -u
PY="${CCPILOT_PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    PY=python
fi
if ! command -v "$PY" >/dev/null 2>&1; then
    exit 0
fi
"$PY" -m ccpilot route 2>>"${HOME}/.claude/ccpilot/hook.err" || exit 0