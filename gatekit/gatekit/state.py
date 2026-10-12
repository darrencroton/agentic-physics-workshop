"""Workshop state in .workshop/state.json, written atomically."""

import datetime
import json
import os
import tempfile

STATE_DIR = ".workshop"
STATE_FILE = "state.json"


class StateError(Exception):
    """Raised when the state file is missing or corrupt."""


def now_iso():
    """Current UTC time as an ISO-8601 string."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def parse_iso(text):
    """Parse an ISO-8601 string written by now_iso()."""
    return datetime.datetime.fromisoformat(text)


def state_path(root):
    """Path of state.json under `root`."""
    return os.path.join(root, STATE_DIR, STATE_FILE)


def initial_state(manifest):
    """Fresh state at level 0 for the given manifest."""
    level0 = manifest["levels"][0]
    return {
        "exercise": manifest["exercise"],
        "level": 0,
        "persona": level0.get("persona", "coach"),
        "allowed_models": list(manifest.get("models", {}).get("allowed", [])),
        "levels": {"0": {"started": now_iso(), "unlocked": None,
                         "hints_used": [], "failed_attempts": 0}},
        "attempts": [],
        "skips": [],
        "records": {},
        "complete": False,
    }


def load_state(root):
    """Load and minimally validate state.json."""
    path = state_path(root)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except FileNotFoundError:
        raise StateError("no workshop state at %s (run ./gate reset)" % path)
    except (ValueError, OSError) as exc:
        raise StateError("corrupt workshop state: %s" % exc)
    for key in ("exercise", "level", "levels", "allowed_models"):
        if key not in state:
            raise StateError("workshop state is missing '%s'" % key)
    if not isinstance(state["level"], int):
        raise StateError("workshop state level is not an integer")
    return state


def save_state(root, state):
    """Write state.json atomically (temporary file + rename)."""
    directory = os.path.join(root, STATE_DIR)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".state-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, state_path(root))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def level_record(state, level=None):
    """The per-level record, created if needed."""
    key = str(state["level"] if level is None else level)
    record = state["levels"].setdefault(
        key, {"started": now_iso(), "unlocked": None, "hints_used": [],
              "failed_attempts": 0})
    return record


def minutes_on_level(state):
    """Minutes since the current level started."""
    started = parse_iso(level_record(state)["started"])
    delta = datetime.datetime.now(datetime.timezone.utc) - started
    return delta.total_seconds() / 60.0


def advance_level(state, persona):
    """Mark the current level unlocked and start the next one."""
    level_record(state)["unlocked"] = now_iso()
    state["level"] += 1
    state["persona"] = persona
    level_record(state)
    return state


def log_failed_attempt(state, kind):
    """Record a failed gate attempt (timestamp and kind only)."""
    level_record(state)["failed_attempts"] += 1
    state["attempts"].append({"ts": now_iso(), "level": state["level"],
                              "kind": kind})


def append_log(root, heading, body):
    """Append a dated section to LOG.md."""
    path = os.path.join(root, "LOG.md")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n### %s (%s)\n\n%s\n" % (heading, now_iso(), body.rstrip()))
