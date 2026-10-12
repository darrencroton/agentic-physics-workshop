#!/usr/bin/env python3
"""PreModelSwitch hook: allow only models listed in .workshop/state.json."""

import json
import os
import sys

ROOT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
EVENT = "PreModelSwitch"


def deny(reason):
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": EVENT, "permissionDecision": "deny",
        "permissionDecisionReason": reason}}) + "\n")
    sys.exit(0)


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        target = str(data.get("to_model") or data.get("requested_model") or "")
    except ValueError:
        deny("Model lock received malformed input; the switch is refused.")
    try:
        with open(os.path.join(ROOT, ".workshop", "state.json"),
                  encoding="utf-8") as fh:
            allowed = [str(m).lower() for m in json.load(fh)["allowed_models"]]
    except (OSError, ValueError, KeyError, TypeError):
        deny("Workshop state is missing, so model switches are refused. "
             "A human should run ./gate reset in the gate terminal.")
    if not target:
        deny("Model lock could not read the target model; the switch is refused.")
    if any(alias and alias in target.lower() for alias in allowed):
        sys.exit(0)
    deny("Today's exercise uses %s. Ask a facilitator for a power-up."
         % (allowed[0] if allowed else "the configured model"))


if __name__ == "__main__":
    main()
