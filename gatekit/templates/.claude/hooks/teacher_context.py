#!/usr/bin/env python3
"""UserPromptSubmit hook: prints the current level and persona as context."""

import importlib
import os
import sys

ROOT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
sys.path.insert(0, os.path.join(ROOT, ".gatekit"))


def main():
    try:
        from gatekit import hooklib as H
    except ImportError:
        print("WORKSHOP: gatekit is missing; ask a facilitator.")
        return
    state = H.load_state(ROOT)
    manifest = H.load_manifest(ROOT)
    if state is None or manifest is None:
        print("WORKSHOP: state is missing. A human should run ./gate reset.")
        return
    level = state.get("level", 0)
    levels = manifest.get("levels", [])
    title = levels[level]["title"] if 0 <= level < len(levels) else "?"
    persona_text = H.read_text(os.path.join(H.level_dir(ROOT, level),
                                            "persona.txt")) or ""
    lines = persona_text.strip().splitlines()
    mode = state.get("persona", "coach")
    if lines and lines[0].lower().startswith("persona:"):
        mode = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    print("WORKSHOP LEVEL %d — %s — persona: %s" % (level, title, mode))
    body = "\n".join(lines).strip()
    if body:
        print(body)
    tool_name = manifest.get("tool")
    if tool_name:
        try:
            tool = importlib.import_module(tool_name)
            extra = getattr(tool, "teacher_context_extra", None)
            if extra:
                text = extra(ROOT, state)
                if text:
                    print(text)
        except Exception as exc:
            print("(exercise tool context unavailable: %s)"
                  % exc.__class__.__name__)


if __name__ == "__main__":
    main()
