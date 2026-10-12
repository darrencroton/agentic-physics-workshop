#!/usr/bin/env python3
"""PreToolUse guard: keeps Claude out of the vault, the gate and frozen paths.

Reads the hook JSON on stdin and prints a deny decision with a teaching
message when the call is not allowed.  Anything unreadable denies.
"""

import os
import sys

ROOT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
sys.path.insert(0, os.path.join(ROOT, ".gatekit"))

try:
    from gatekit import hooklib as H
except ImportError:
    sys.stdout.write('{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
                     '"permissionDecision": "deny", "permissionDecisionReason": '
                     '"Workshop guard cannot load gatekit; ask a facilitator."}}\n')
    sys.exit(0)

EVENT = "PreToolUse"
MSG_SECRET = ("That path belongs to the workshop machinery (vault, state or "
              "tools). The gate is for humans to unlock. Ask the group what "
              "they observed instead.")
MSG_GATE = ("The gate terminal is for humans. Ask the group to run that "
            "command themselves and tell you the result.")
MSG_PKG = ("No package installs today. Everything needed is already in "
           ".venv. Use what is there.")
MSG_PTY = ("Faking a terminal is off limits. Human-only commands stay with "
           "the humans.")
MSG_FROZEN = ("That file is part of the exercise scaffolding and is "
              "read-only. Work in the files the current level allows.")
MSG_OUTSIDE = "Edits outside the workshop repo are not allowed today."
MSG_STATE = ("Workshop state is missing. A human should run ./gate reset in "
             "the gate terminal.")


def main():
    try:
        data = H.read_hook_input()
    except ValueError as exc:
        H.deny(EVENT, "Guard received malformed input (%s); failing closed."
               % exc)
    tool = data.get("tool_name")
    tool_input = data.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tool_input, dict):
        H.deny(EVENT, "Guard received an unexpected tool call; failing closed.")

    state = H.load_state(ROOT)
    if state is None:
        H.deny(EVENT, MSG_STATE)
    level = state.get("level", 0)
    guard = H.load_guard(ROOT, level) or {}
    phase = H.read_phase(ROOT)
    rules = dict(guard)
    phases = guard.get("phases") or {}
    if phases:
        rules.update(phases.get(phase) or phases.get("none") or {})
    editable = rules.get("editable") or []
    frozen_extra = rules.get("frozen") or []
    message = rules.get("message") or guard.get("message") or (
        "That file is frozen at this level. Allowed now: %s."
        % (", ".join(editable) or "nothing"))

    if tool in H.PATH_TOOLS:
        check_path_tool(tool, tool_input, editable, frozen_extra, message)
    elif tool == "Bash":
        check_bash(tool_input, editable, frozen_extra, message)
    H.allow()


def check_path_tool(tool, tool_input, editable, frozen_extra, message):
    field = H.PATH_TOOLS[tool]
    path = tool_input.get(field)
    if tool in ("Glob", "Grep"):
        for value in (tool_input.get("pattern"), tool_input.get("glob"),
                      tool_input.get("type"), path):
            if value and H.mentions_secret(str(value)):
                H.deny(EVENT, MSG_SECRET)
        if tool == "Glob" and H.re.search(r"(^|/)\.", str(tool_input.get("pattern") or "")):
            H.deny(EVENT, MSG_SECRET)
        path = path or "."
    if not isinstance(path, str) or not path:
        H.deny(EVENT, "Guard could not read the path for %s; failing closed."
               % tool)
    rel = H.relative_path(ROOT, path)
    if rel is None:
        if tool in H.EDIT_TOOLS:
            H.deny(EVENT, MSG_OUTSIDE)
        return
    if H.is_secret(rel):
        H.deny(EVENT, MSG_SECRET)
    if tool in H.EDIT_TOOLS:
        if H.is_frozen(rel) or H.any_match(rel, frozen_extra):
            H.deny(EVENT, MSG_FROZEN if H.is_frozen(rel) else message)
        if not H.any_match(rel, editable):
            H.deny(EVENT, message)


def check_bash(tool_input, editable, frozen_extra, message):
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        H.deny(EVENT, "Guard could not read the Bash command; failing closed.")
    re = H.re
    if H.mentions_secret(command):
        H.deny(EVENT, MSG_SECRET)
    text = H.normalise_command(command)
    if (re.search(H.HUMAN_GATE, text) or re.search(H.HUMAN_TDD, text)
            or re.search(H.HUMAN_INDIRECT, text)):
        H.deny(EVENT, MSG_GATE)
    if any(re.search(p, text) for p in H.PACKAGE_MANAGERS):
        H.deny(EVENT, MSG_PKG)
    if any(re.search(p, text) for p in H.PTY_TRICKS):
        H.deny(EVENT, MSG_PTY)
    if any(re.search(p, text) for p in H.GIT_READERS):
        H.deny(EVENT, "That git command can print the vault or the tool sources. "
               "Use git status, git diff, git log --stat and git add/commit.")
    if H.has_write_verb(command):
        for frozen in H.FROZEN_FILES + H.FROZEN_DIRS:
            if H.mentions_path(command, frozen):
                H.deny(EVENT, MSG_FROZEN)
        for pattern in frozen_extra:
            if H.mentions_path(command, pattern):
                H.deny(EVENT, message)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail closed on anything unexpected
        H.deny(EVENT, "Guard hit an internal error (%s); failing closed."
               % exc.__class__.__name__)
