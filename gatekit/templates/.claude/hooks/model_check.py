#!/usr/bin/env python3
"""SessionStart hook: best-effort warning when the session model is not allowed.

Claude Code does not always include `model` in SessionStart input, so a
launch-time override can go unnoticed.  This is documented as an honest limit.
"""

import json
import os
import sys

ROOT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    model = str(data.get("model") or "")
    try:
        with open(os.path.join(ROOT, ".workshop", "state.json"),
                  encoding="utf-8") as fh:
            allowed = [str(m).lower() for m in json.load(fh)["allowed_models"]]
    except (OSError, ValueError, KeyError, TypeError):
        print("WORKSHOP: state is missing. A human should run ./gate reset "
              "in the gate terminal before starting.")
        return
    if model and not any(a in model.lower() for a in allowed):
        print("WORKSHOP WARNING: this session is running on '%s' but today's "
              "exercise uses %s. Tell the group and the facilitator before "
              "continuing." % (model, ", ".join(allowed)))


if __name__ == "__main__":
    main()
