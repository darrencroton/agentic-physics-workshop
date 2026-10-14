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
    from gatekit import manifest as manifest_mod
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
MSG_PIPE = ("Piping code into a shell or Python is off limits. Run the "
            "command or script directly.")
MSG_PTY = ("Faking a terminal is off limits. Human-only commands stay with "
           "the humans.")
MSG_FROZEN = ("That file is part of the exercise scaffolding and is "
              "read-only. Work in the files the current level allows.")
MSG_OUTSIDE = "Edits outside the workshop repo are not allowed today."
MSG_APPEAL = (" If you think this refusal is wrong, don't reword or retry it to "
              "slip past the guard: tell the group in one line and use a make "
              "target or the tests instead.")
MAX_DEPTH = 3


def refuse(reason):
    """Deny a Bash or path-tool call with the shared appeal sentence."""
    H.deny(EVENT, reason + MSG_APPEAL)


def plan_file(path):
    """Claude Code's own plan-mode files (~/.claude/plans or $CLAUDE_CONFIG_DIR/plans)."""
    homes = [os.path.join(os.path.expanduser("~"), ".claude")]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        homes.append(os.environ["CLAUDE_CONFIG_DIR"])
    try:
        real = os.path.realpath(os.path.expanduser(path))
    except (OSError, ValueError):
        return False
    for home in homes:
        plans = os.path.realpath(os.path.join(home, "plans"))
        if real == plans or real.startswith(plans + os.sep):
            return True
    return False
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
                refuse(MSG_SECRET)
        if tool == "Glob" and H.re.search(r"(^|/)\.", str(tool_input.get("pattern") or "")):
            refuse(MSG_SECRET)
        path = path or "."
    if not isinstance(path, str) or not path:
        refuse("Guard could not read the path for %s; failing closed." % tool)
    lexical, resolved = H.relative_paths(ROOT, path)
    candidates = [r for r in (lexical, resolved) if r is not None]
    if not candidates:
        if tool in H.EDIT_TOOLS and not plan_file(path):
            refuse(MSG_OUTSIDE)
        return
    if any(H.is_secret(r) for r in candidates):
        refuse(MSG_SECRET)
    if tool in H.EDIT_TOOLS:
        if resolved is None:
            refuse(MSG_OUTSIDE)
        launchers = tuple(human_only_spec())
        for rel in candidates:
            if H.is_frozen(rel, launchers):
                refuse(MSG_FROZEN)
            if H.any_match(rel, frozen_extra):
                refuse(message)
        if not all(H.any_match(rel, editable) for rel in candidates):
            refuse(message)


def human_only_spec():
    """Launcher -> human-only subcommands from the manifest; deny when unreadable."""
    try:
        manifest = manifest_mod.load_root_manifest(ROOT)
        return H.human_only(manifest)
    except (manifest_mod.ManifestError, ValueError) as exc:
        refuse("Guard could not read the workshop manifest (%s); "
               "failing closed." % exc)


def check_bash(tool_input, editable, frozen_extra, message):
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        refuse("Guard could not read the Bash command; failing closed.")
    for prefix in {ROOT, os.environ.get("CLAUDE_PROJECT_DIR") or ROOT}:
        command = command.replace(prefix.rstrip("/") + "/", "")
    analyse_bash(command, frozen_extra, message, 0)


def check_redirect(word, launchers, frozen_extra, message):
    """Deny a redirect whose target is secret, build-frozen or level-frozen."""
    if ".." in word.split("/"):
        for frozen in H.FROZEN_FILES + launchers + H.FROZEN_DIRS:
            if H.mentions_path(word, frozen):
                refuse(MSG_FROZEN)
        if any(H.mentions_path(word, p) for p in frozen_extra):
            refuse(message)
    lexical, resolved = H.relative_paths(ROOT, word)
    for rel in (r for r in (lexical, resolved) if r is not None):
        if H.is_secret(rel):
            refuse(MSG_SECRET)
        if H.is_frozen(rel, launchers):
            refuse(MSG_FROZEN)
        if any(H.pattern_hit(rel, p) for p in frozen_extra):
            refuse(message)


def analyse_bash(command, frozen_extra, message, depth):
    """Apply every Bash rule to `command`; heredoc bodies fed to a shell recurse."""
    if depth > MAX_DEPTH:
        refuse("Guard found shell input nested too deeply; failing closed.")
    re = H.re
    command = H.strip_noise(command)
    parsed = H.parse_shell(command)
    if H.mentions_secret(command, parsed.masked):
        refuse(MSG_SECRET)
    text = H.normalise_command(command)
    if any(re.search(p, text) for p in H.ALWAYS_DENY):
        refuse("Symbolic links are not needed today; work in the "
               "files the level allows.")
    spec = human_only_spec()
    direct, indirect = H.human_only_patterns(spec)
    if (re.search(H.HUMAN_GATE, text) or re.search(indirect, text)
            or any(re.search(p, text) for p in direct)):
        refuse(MSG_GATE)
    if any(re.search(p, text) for p in H.PACKAGE_MANAGERS):
        refuse(MSG_PKG)
    if re.search(H.PIPE_TO_INTERPRETER, H.normalise_command(parsed.outside)):
        refuse(MSG_PIPE)
    if any(re.search(p, text) for p in H.PTY_TRICKS):
        refuse(MSG_PTY)
    if any(re.search(p, text) for p in H.GIT_READERS):
        refuse("That git command can print the vault or the tool sources. "
               "Use git status, git diff, git log --stat and git add/commit.")
    for word in parsed.redirects:
        check_redirect(word, tuple(spec), frozen_extra, message)
    if H.has_write_verb(parsed):
        for frozen in H.FROZEN_FILES + tuple(spec) + H.FROZEN_DIRS:
            if H.mentions_path(parsed.text, frozen):
                refuse(MSG_FROZEN)
        for pattern in frozen_extra:
            if H.mentions_path(parsed.text, pattern):
                refuse(message)
    for body in parsed.shell_bodies:
        analyse_bash(body, frozen_extra, message, depth + 1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail closed on anything unexpected
        H.deny(EVENT, "Guard hit an internal error (%s); failing closed."
               % exc.__class__.__name__)
