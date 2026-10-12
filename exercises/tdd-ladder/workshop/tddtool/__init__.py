"""Exercise tool for the TDD Ladder; the interface gatekit expects."""

import os

from tddtool import common as C
from tddtool.gates import conditions, post_unlock, validators  # noqa: F401


def level_secret(root, level):
    """Secret that opens the pack for level + 1 (verified gates)."""
    keys = C.vault_keys(root)
    try:
        return bytes.fromhex(keys[str(level)])
    except KeyError:
        raise C.TddError("no secret for level %d in keys.bin" % level)


def status_lines(root, state):
    lines = []
    level = state.get("level", 0)
    phase = C.read_phase(root)
    if level >= 3:
        cycle = C.read_cycle(root) or {}
        lines.append("TDD phase: %s%s" % (phase.upper(), (
            " (%s)" % cycle["behaviour"]) if cycle.get("behaviour") else ""))
        lines.append("Valid cycles at this level: %d" % len(C.valid_cycles(root, level)))
    score = C.last_score(state, level)
    if score:
        lines.append("Last score at this level: acceptance %d/%d, killed %d/%d, "
                     "false alarms %d" % (score["acceptance"], score["acceptance_total"],
                                          score["killed"], score["mutants_total"],
                                          len(score["false_alarms"])))
    else:
        lines.append("No score at this level yet.")
    return lines


def teacher_context_extra(root, state):
    level = state.get("level", 0)
    if level < 3 or level > 4:
        return ""
    phase = C.read_phase(root)
    cycle = C.read_cycle(root) or {}
    rules = {
        "none": "No cycle is open: src/ and tests/ are frozen until a human runs ./tdd red.",
        "red": "RED: write ONE test for the behaviour below; src/ is frozen.",
        "green": "GREEN: tests/ are frozen; write the minimum code to pass.",
        "refactor": "REFACTOR: tests/ are frozen; improve the code with all tests green.",
    }
    text = "TDD PHASE: %s. %s" % (phase.upper(), rules[phase])
    if cycle.get("behaviour"):
        text += "\nCurrent behaviour: %s" % cycle["behaviour"]
    return text


def on_reset(root):
    import shutil
    shutil.rmtree(os.path.join(root, ".tdd"), ignore_errors=True)
