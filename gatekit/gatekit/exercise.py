"""Loading the optional exercise tool module and resolving dotted names.

An exercise tool (for example `tddtool`) is a package under `.gatekit/`
that may provide:

- `conditions`: {name: fn(root, state, manifest) -> (ok, reason)}
- `validators`: {name: fn(root, state, question, answer) -> (ok, reason)}
- `post_unlock`: {name: fn(root, state, manifest, new_level) -> message}
- `questions`: {name: fn(root, state, question) -> {"prompt": str,
  "wrong_hint": str}} for a gate question's `text_from`; either key is
  optional, and an exception or bad return falls back to the static
  `prompt` and `wrong_hint`
- `hints`: {name: fn(root, state, tier) -> str} for a hint tier's
  `text_from`; a non-empty string replaces the tier's `text`, and an
  exception or bad return falls back to the static `text`
- `level_secret(root, level) -> bytes` for verified gates
- `status_lines(root, state) -> [str]`
- `teacher_context_extra(root, state) -> str`
- `on_reset(root)`
"""

import importlib

from . import answers


class ExerciseError(Exception):
    """Raised when an exercise tool or a dotted name cannot be resolved."""


def load_tool(manifest):
    """Import the manifest's tool module, or return None when there is none."""
    name = manifest.get("tool")
    if not name:
        return None
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise ExerciseError("cannot import exercise tool '%s': %s"
                            % (name, exc))


def _builtin_validator(kind):
    def validate(root, state, question, answer):
        if answers.matches(question, answer):
            return True, ""
        return False, "Not quite. Discuss and try again."
    return validate


BUILTIN_VALIDATORS = {
    "gate.answer": _builtin_validator("answer"),
}


def resolve(tool, table, dotted):
    """Resolve 'tool.name' or 'gate.name' to a callable."""
    if not dotted or "." not in dotted:
        raise ExerciseError("expected a dotted name, got %r" % (dotted,))
    prefix, name = dotted.split(".", 1)
    if prefix == "gate":
        if table == "validators" and name in ("answer",):
            return BUILTIN_VALIDATORS["gate." + name]
        raise ExerciseError("unknown built-in %s '%s'" % (table, name))
    if tool is None:
        raise ExerciseError("manifest names '%s' but has no tool" % dotted)
    registry = getattr(tool, table, {})
    if name not in registry:
        raise ExerciseError("exercise tool has no %s '%s'" % (table, name))
    return registry[name]
