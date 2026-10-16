"""Exercise tool for Explorer; the interface gatekit expects.

Stdlib only and importable on Python 3.9. The level checks run under the
.venv (see checks/levelN.py); `gate` itself imports this package with the
system python3.
"""

import os
import shutil

from exploretool import gates

BROWSER_QUESTIONS = {
    "data/pulsars.csv": {
        "prompt": "Plot XX, YY and ZZ in 3D and rotate it: the known pulsars crowd "
                  "around one point. In a word or two, what is at that point?",
        "wrong_hint": "XX, YY and ZZ are Galactic coordinates: data/pulsars.columns.json "
                      "says where they are measured from. Why would the pulsars we know "
                      "cluster there?",
        "answer": "The gate unlock answer is the Sun (type sun): XX, YY and ZZ are measured from the "
                  "Galactic centre, with the Sun at (0, 8.5, 0) kpc, and the pulsars we "
                  "know are mostly nearby ones: the faint, distant ones are hard to "
                  "detect.",
    },
    "data/dimuons.csv": {
        "prompt": "Plot M against pt1 with log axes: there is a sharp band near "
                  "M = 3.1 GeV. In a word or two, which particle makes it?",
        "wrong_hint": "Each narrow band along M is a particle that decays to two muons. "
                      "The one near 3.1 GeV is a charm-anticharm bound state with a two-letter "
                      "name.",
        "answer": "The gate unlock answer is the J/psi meson (type jpsi): it is a charm-anticharm bound "
                  "state of mass 3.097 GeV that often decays to two muons, so the pair "
                  "mass M piles up there.",
    },
}

post_unlock = {"record_head": gates.record_head}


def browser_question(root, state, question):
    """The Level 1 question and hint for the dataset named in PLAN.md."""
    return BROWSER_QUESTIONS[gates.plan_dataset(root)]


questions = {"browser_question": browser_question}


def browser_answer(root, state, tier):
    """The Level 1 answer for the dataset named in PLAN.md."""
    return BROWSER_QUESTIONS[gates.plan_dataset(root)]["answer"]


hints = {"browser_answer": browser_answer}


def status_lines(root, state):
    lines = []
    try:
        lines.append("Dataset: %s (the Dataset: line in PLAN.md)" % gates.plan_dataset(root))
    except gates.CheckFailed:
        lines.append("Dataset: PLAN.md has no valid Dataset: line yet")
    except Exception as exc:
        lines.append("Dataset: unknown (%s)" % exc)
    page = os.path.join(root, "out", "explorer.html")
    lines.append("Page: %s" % ("out/explorer.html (make open)" if os.path.isfile(page)
                               else "not built yet (make explore)"))
    if state.get("complete"):
        return lines
    level = int(state.get("level", 0))
    need = gates.REQUIRED_COMMITS.get(level)
    if need is None:
        return lines
    try:
        count = gates.commits_since(root, level, gates.heads_from_state(state))
        since = "start" if level == 0 else "the last gate"
        lines.append("Commits since %s: %d (this level needs at least %d)"
                     % (since, count, need))
    except Exception as exc:
        lines.append("Commits: unknown (%s)" % exc)
    return lines


def on_reset(root):
    """Remove generated pages; the commit records live in state, which reset rewrites."""
    shutil.rmtree(os.path.join(root, "out"), ignore_errors=True)
