"""Verified-gate conditions, validators and post-unlock actions."""

import os
import re

from gatekit import answers
from tddtool import common as C

NOT_QUITE = "Not quite. Discuss and try again."
SPEC_ITEM = re.compile(
    r"^\s*(?:[|\-*]\s*)?(?:#+\s*)?(?:\*\*)?(?:decision\s*|[SD])?\s*(\d{1,2})\s*(?:\*\*)?\s*[.):|\-\u2013\u2014]",
    re.MULTILINE | re.IGNORECASE)


def _level(state):
    return int(state.get("level", 0))


# ------------------------------------------------------------- conditions

def score_recorded_at_level(root, state, manifest):
    s = C.last_score(state, _level(state))
    if s is None:
        return False, "no score recorded at this level yet. Run ./tdd score."
    return True, "score recorded: %d/%d acceptance" % (s["acceptance"], s["acceptance_total"])


def new_attempt_and_score_at_level(root, state, manifest):
    level = _level(state)
    attempts = [a for a in C.records(state).get("new_attempts", []) if a.get("level") == level]
    if not attempts:
        return False, ("this level has no fresh attempt (the unlock should have made one). "
                       "Run ./tdd new-attempt in the gate terminal, redo the work, then run ./tdd score.")
    s = C.last_score(state, level)
    if s is None or s["ts"] < attempts[-1]["ts"]:
        return False, ("no score recorded since the fresh attempt began. "
                       "Run ./tdd score in the gate terminal.")
    return True, "new attempt made and scored (%d/%d killed)" % (s["killed"], s["mutants_total"])


def _level2_changes(root, state):
    """Name the files that differ from the Level 2 snapshot, with how to undo each."""
    tree = C.records(state).get("tree_hash", {})
    before = tree.get("level2_files")
    commit = tree.get("level2_commit")
    if not isinstance(before, dict) or not commit:
        return " For committed work, run git checkout -- src tests."
    now = C.tree_files(root, "src", "tests")
    changed = sorted(p for p in before if p in now and before[p] != now[p])
    added = sorted(p for p in now if p not in before)
    missing = sorted(p for p in before if p not in now)
    lines = []
    if changed or missing:
        lines.append("restore with git checkout %s -- %s"
                     % (commit[:10], " ".join(changed + missing)))
    if added:
        lines.append("delete the new file(s): %s (if one was added with git add, "
                     "run git rm --cached -f on it first)" % ", ".join(added))
    return " To fix: %s." % "; ".join(lines) if lines else ""


def count_spec_decisions(text):
    return len({m.group(1) for m in SPEC_ITEM.finditer(text)})


def spec_written_and_code_untouched(root, state, manifest):
    path = os.path.join(root, "SPEC.md")
    if not os.path.exists(path):
        return False, ("SPEC.md does not exist yet. Ask Claude to write it from your decisions, "
                       "with numbered items (1. ..., 2. ...).")
    with open(path, encoding="utf-8") as fh:
        count = count_spec_decisions(fh.read())
    if count < 6:
        return False, ("SPEC.md has %d numbered decisions; at least 6 are needed. Start each "
                       "decision on its own line as 1. ..., 2. ... and keep interviewing "
                       "if you have fewer." % count)
    recorded = C.records(state).get("tree_hash", {}).get("level2")
    if recorded and recorded != C.tree_hash(root, "src", "tests"):
        return False, ("src/ or tests/ changed during Level 2. This level is decisions only: "
                       "put them back exactly as they were when Level 2 began.%s"
                       % _level2_changes(root, state))
    return True, "SPEC.md has %d numbered decisions and the code is untouched" % count


def cycles_and_rung4_score(root, state, manifest):
    level = _level(state)
    cycles = C.valid_cycles(root, level)
    phase = C.read_phase(root)
    if phase != "none":
        return False, ("a cycle is still open (phase %s). Finish it with ./tdd done, or close "
                       "it with ./tdd abort, then try again." % phase.upper())
    if len(cycles) < 5:
        return False, ("%d valid cycle(s) so far; 5 are needed (red seen for the right reason, "
                       "closed with ./tdd done)." % len(cycles))
    s = C.last_score(state, level)
    if s is None:
        return False, "no score at this level yet. Run ./tdd score."
    if s["false_alarms"]:
        return False, "last score has %d false alarm(s); it must have 0." % len(s["false_alarms"])
    if s["killed"] < 9:
        return False, ("last score killed %d/16 mutants; at least 9 are needed. Run ./tdd score to "
                       "see which spec decisions have survivors, then add cycles for them." % s["killed"])
    return True, "%d valid cycles, %d/16 killed, 0 false alarms" % (len(cycles), s["killed"])


def rung5_score(root, state, manifest):
    s = C.last_score(state, _level(state))
    if s is None:
        return False, "no score at this level yet. Run ./tdd score."
    if s["false_alarms"]:
        return False, "last score has %d false alarm(s); it must have 0." % len(s["false_alarms"])
    if s["killed"] < 14:
        return False, "last score killed %d/16; at least 14 are needed." % s["killed"]
    if s["suite_seconds"] >= 10:
        return False, "your suite takes %.1f s; it must run in under 10 s." % s["suite_seconds"]
    return True, "%d/16 killed, 0 false alarms, suite %.1f s" % (s["killed"], s["suite_seconds"])


def mutation_report_in_log(root, state, manifest):
    try:
        with open(os.path.join(root, "LOG.md"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False, "LOG.md is missing."
    if re.search(r"^##+\s*mutation report", text, re.IGNORECASE | re.MULTILINE):
        return True, "LOG.md has a mutation report section"
    return False, "LOG.md needs a '## Mutation report' section."


# ------------------------------------------------------------- validators

def equals_last_acceptance_count(root, state, question, answer):
    s = C.last_score(state, _level(state))
    try:
        value = int(round(answers.parse_number(answer)))
    except answers.AnswerError:
        return False, "Answer with a whole number."
    if s and value == s["acceptance"]:
        return True, ""
    return False, NOT_QUITE


def spec_id_in_last_survivors(root, state, question, answer):
    s = C.last_score(state, _level(state))
    if s is None:
        return False, "no score recorded."
    text = answer.strip().lower()
    if text in ("none", "no", "nil", "0"):
        if not s["survivors"]:
            return True, ""
        return False, NOT_QUITE
    sid = C.spec_id(answer)
    accepted = {part for spec in s["survivor_specs"] for part in spec.split("/")}
    if sid and sid in accepted:
        return True, ""
    return False, NOT_QUITE


# ------------------------------------------------------------ post-unlock

def _commit_level2_start(root):
    """Commit src/ and tests/ as they stand and return the commit hash (or None)."""
    try:
        C.git(root, "add", "-A", "--", "src", "tests")
        if C.dirty_paths(root, "src", "tests"):
            C.git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m",
                  "Level 2 start", "--", "src", "tests")
        return C.git_head(root)
    except C.TddError:
        return None


def record_tree_hash(root, state, manifest, new_level):
    hashes = C.records(state)["tree_hash"]
    hashes["level2_commit"] = _commit_level2_start(root)
    hashes["level2"] = C.tree_hash(root, "src", "tests")
    hashes["level2_files"] = C.tree_files(root, "src", "tests")
    return None


def start_from_stub(root, state, manifest, new_level):
    from tddtool import phases
    branch = phases.new_attempt(root, state, "Level %d" % new_level)
    return ("Level %d starts from the stub: your earlier work is saved on "
            "branch %s, and src/hzbin/binning.py and tests/ are reset. "
            "(./tdd new-attempt does the same again if you want to restart.)"
            % (new_level, branch))


conditions = {
    "score_recorded_at_level": score_recorded_at_level,
    "new_attempt_and_score_at_level": new_attempt_and_score_at_level,
    "spec_written_and_code_untouched": spec_written_and_code_untouched,
    "cycles_and_rung4_score": cycles_and_rung4_score,
    "rung5_score": rung5_score,
    "mutation_report_in_log": mutation_report_in_log,
}

validators = {
    "equals_last_acceptance_count": equals_last_acceptance_count,
    "spec_id_in_last_survivors": spec_id_in_last_survivors,
}

post_unlock = {
    "record_tree_hash": record_tree_hash,
    "start_from_stub": start_from_stub,
}
