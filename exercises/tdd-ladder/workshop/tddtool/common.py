"""Shared helpers for the tdd tool: paths, phase, run log, git, pytest."""

import datetime
import hashlib
import json
import os
import re
import subprocess
import uuid

from gatekit import crypto, packs, state as st

PHASES = ("none", "red", "green", "refactor")
GOOD_FAILURES = ("AssertionError", "NotImplementedError")
STUB_FILES = ("src/hzbin/binning.py", "tests")


class TddError(Exception):
    """A user-facing refusal with an explanation."""


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def tdd_dir(root):
    return os.path.join(root, ".tdd")


def ensure_tdd_dir(root):
    os.makedirs(tdd_dir(root), exist_ok=True)


def venv_python(root):
    path = os.path.join(root, ".venv", "bin", "python")
    if not os.path.exists(path):
        raise TddError("No .venv found. A human should run ./preflight --setup.")
    return path


# ------------------------------------------------------------------ phase

def read_phase(root):
    try:
        with open(os.path.join(tdd_dir(root), "phase"), encoding="utf-8") as fh:
            phase = fh.read().strip().lower()
    except OSError:
        return "none"
    return phase if phase in PHASES else "none"


def write_phase(root, phase):
    ensure_tdd_dir(root)
    tmp = os.path.join(tdd_dir(root), "phase.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(phase + "\n")
    os.replace(tmp, os.path.join(tdd_dir(root), "phase"))


def read_cycle(root):
    try:
        with open(os.path.join(tdd_dir(root), "cycle.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_cycle(root, cycle):
    ensure_tdd_dir(root)
    tmp = os.path.join(tdd_dir(root), "cycle.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cycle, fh, indent=2, sort_keys=True)
    os.replace(tmp, os.path.join(tdd_dir(root), "cycle.json"))


def clear_cycle(root):
    try:
        os.unlink(os.path.join(tdd_dir(root), "cycle.json"))
    except OSError:
        pass


def append_jsonl(root, name, record):
    ensure_tdd_dir(root)
    with open(os.path.join(tdd_dir(root), name), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def read_jsonl(root, name):
    records = []
    try:
        with open(os.path.join(tdd_dir(root), name), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return records


def valid_cycles(root, level=None):
    cycles = [c for c in read_jsonl(root, "cycles.jsonl") if c.get("valid")]
    if level is not None:
        cycles = [c for c in cycles if c.get("level") == level]
    return cycles


# -------------------------------------------------------------------- git

def git(root, *args, check=True):
    proc = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                          text=True)
    if check and proc.returncode != 0:
        raise TddError("git %s failed: %s" % (args[0], proc.stderr.strip()))
    return proc.stdout


def git_head(root):
    return git(root, "rev-parse", "HEAD").strip()


def dirty_paths(root, *paths):
    out = git(root, "status", "--porcelain", "--", *paths)
    return [line[3:] for line in out.splitlines() if line.strip()]


def diff_names(root, since, *paths):
    out = git(root, "diff", "--name-only", since, "HEAD", "--", *paths)
    return [line for line in out.splitlines() if line.strip()]


def tests_changed_since(root, commit):
    """Committed or uncommitted changes to tests/ since `commit`."""
    changed = diff_names(root, commit, "tests")
    changed += dirty_paths(root, "tests")
    return sorted(set(changed))


def tree_hash(root, *paths):
    """Content hash of all files under the given paths."""
    digest = hashlib.sha256()
    for base in paths:
        full = os.path.join(root, base)
        if os.path.isfile(full):
            files = [full]
        else:
            files = []
            for dirpath, dirnames, filenames in os.walk(full):
                dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
                files += [os.path.join(dirpath, f) for f in sorted(filenames)
                          if not f.endswith(".pyc")]
        for path in files:
            digest.update(os.path.relpath(path, root).encode("utf-8") + b"\0")
            with open(path, "rb") as fh:
                digest.update(fh.read())
            digest.update(b"\0")
    return digest.hexdigest()


# ----------------------------------------------------------------- pytest

def run_pytest(root, extra_args=(), capture=False):
    """Run the repo's pytest in .venv; return (exit code, run record or None)."""
    python = venv_python(root)
    run_id = uuid.uuid4().hex
    env = dict(os.environ, TDD_RUN_ID=run_id)
    env.pop("TDD_NO_LOG", None)
    cmd = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider"] + list(extra_args)
    proc = subprocess.run(cmd, cwd=root, env=env, capture_output=capture,
                          text=True)
    record = None
    for rec in reversed(read_jsonl(root, "runs.jsonl")):
        if rec.get("run_id") == run_id:
            record = rec
            break
    return proc.returncode, record, (proc.stdout if capture else "")


def summarise_run(record):
    tests = record.get("tests", {})
    passed = sorted(n for n, t in tests.items() if t["outcome"] == "passed")
    failed = {n: t for n, t in tests.items() if t["outcome"] in ("failed", "error")}
    skipped = sorted(n for n, t in tests.items() if t["outcome"] == "skipped")
    return passed, failed, skipped, record.get("collection_errors", [])


# ------------------------------------------------------------------ state

def records(state):
    return state.setdefault("records", {}).setdefault(
        "tdd", {"scores": [], "new_attempts": [], "tree_hash": {}})


def last_score(state, level=None):
    scores = records(state).get("scores", [])
    if level is not None:
        scores = [s for s in scores if s.get("level") == level]
    return scores[-1] if scores else None


def load_state(root):
    return st.load_state(root)


def save_state(root, state):
    st.save_state(root, state)


# ------------------------------------------------------------- vault keys

def vault_keys(root):
    """Level and scoring secrets from .vault/keys.bin (obfuscated)."""
    try:
        from tddtool import _pepper
    except ImportError:
        raise TddError("this repo was not built with a pepper; rebuild it")
    key = crypto.obfuscation_key("tdd-ladder", _pepper.PEPPER)
    try:
        with open(os.path.join(root, ".vault", "keys.bin"), "rb") as fh:
            return packs.unseal_json(fh.read(), key)
    except (OSError, crypto.PackError) as exc:
        raise TddError("cannot read .vault/keys.bin: %s" % exc)


def spec_id(text):
    """Canonical spec id ('S4') from loose input ('s4', '4', 'S 4'), or None."""
    match = re.search(r"\bS?\s*(\d{1,2})\b", text.strip(), re.IGNORECASE)
    if not match:
        return None
    return "S%d" % int(match.group(1))
