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
                  "around one point. What is at that point? (A word or two.)",
        "wrong_hint": "XX, YY and ZZ are Galactic coordinates: data/pulsars.columns.json "
                      "says where they are measured from. Why would the pulsars we know "
                      "cluster there?",
    },
    "data/dimuons.csv": {
        "prompt": "Plot M against pt1 with log axes: there is a sharp band near "
                  "M = 3.1 GeV. Which particle makes it? (A word or two.)",
        "wrong_hint": "Each narrow band along M is a particle that decays to two muons. "
                      "The one near 3.1 GeV is a charm-anticharm meson with a two-letter "
                      "name.",
    },
}

post_unlock = {"record_head": gates.record_head}


def browser_question(root, state, question):
    """The Level 1 question and hint for the dataset named in PLAN.md."""
    return BROWSER_QUESTIONS[gates.plan_dataset(root)]


questions = {"browser_question": browser_question}


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
