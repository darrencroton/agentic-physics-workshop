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
        return False, "start this level with ./tdd new-attempt (stub restored)."
    s = C.last_score(state, level)
    if s is None or s["ts"] < attempts[-1]["ts"]:
        return False, "no score recorded since the new attempt. Run ./tdd score."
    return True, "new attempt made and scored (%d/%d killed)" % (s["killed"], s["mutants_total"])


def count_spec_decisions(text):
    return len({m.group(1) for m in SPEC_ITEM.finditer(text)})


def spec_written_and_code_untouched(root, state, manifest):
    path = os.path.join(root, "SPEC.md")
    if not os.path.exists(path):
        return False, "SPEC.md does not exist yet."
    with open(path, encoding="utf-8") as fh:
        count = count_spec_decisions(fh.read())
    if count < 6:
        return False, "SPEC.md has %d numbered decisions; at least 6 are needed." % count
    recorded = C.records(state).get("tree_hash", {}).get("level2")
    if recorded and recorded != C.tree_hash(root, "src", "tests"):
        return False, ("src/ or tests/ changed during Level 2. This level is decisions only: "
                       "put them back exactly as they were when Level 2 began "
                       "(for committed work, git checkout -- src tests).")
    return True, "SPEC.md has %d numbered decisions and the code is untouched" % count


def cycles_and_rung4_score(root, state, manifest):
    level = _level(state)
    cycles = C.valid_cycles(root, level)
    if len(cycles) < 5:
        return False, ("%d valid cycle(s) so far; 5 are needed (red seen for the right reason, "
                       "closed with ./tdd done)." % len(cycles))
    s = C.last_score(state, level)
    if s is None:
        return False, "no score at this level yet. Run ./tdd score."
    if s["false_alarms"]:
        return False, "last score has %d false alarm(s); it must have 0." % len(s["false_alarms"])
    if s["killed"] < 9:
        return False, "last score killed %d/16 mutants; at least 9 are needed." % s["killed"]
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

def record_tree_hash(root, state, manifest, new_level):
    C.records(state)["tree_hash"]["level2"] = C.tree_hash(root, "src", "tests")
    return None


def start_from_stub(root, state, manifest, new_level):
    from tddtool import phases
    branch = phases.new_attempt(root, state, "Level 3")
    return ("Level 3 starts from the stub: your Level 0-2 work is saved on "
            "branch %s, and src/hzbin/binning.py and tests/ are reset." % branch)


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
