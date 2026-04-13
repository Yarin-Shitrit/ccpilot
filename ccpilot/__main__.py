"""CLI entry: `python -m ccpilot [route|registry|classify]`."""
from __future__ import annotations

import json
import sys

from . import classifier, learn, registry, route


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "route"
    if cmd == "route":
        return route.main()
    if cmd == "learn":
        return learn.main()
    if cmd == "registry":
        reg = registry.build()
        registry.save(reg)
        print(json.dumps(reg.to_dict(), indent=2))
        return 0
    if cmd == "classify":
        prompt = sys.stdin.read()
        c = classifier.classify(prompt)
        print(json.dumps(c.to_dict(), indent=2))
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
