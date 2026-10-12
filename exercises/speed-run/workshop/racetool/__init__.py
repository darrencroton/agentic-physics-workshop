"""Exercise tool for the Speed Run; the interface gatekit expects.

Stdlib only and importable on Python 3.9. Numerical work runs in the .venv
through bench/harness.py.
"""

import os

from racetool import common as C
from racetool.gates import conditions  # noqa: F401


def status_lines(root, state):
    lines = ["Division: %s (race.toml)" % C.division_summary(root)]
    try:
        from racetool import records
        recent = records.last_records(root, 3)
    except Exception:
        recent = []
    if recent:
        lines.append("Last bench runs:")
        for rec in recent:
            lines.append("  L%s  %s" % (rec.get("level", "?"), C.record_line(rec)))
    else:
        lines.append("No bench runs recorded yet.")
    subs = (state.get("records") or {}).get("submissions") or []
    if subs:
        good = [s for s in subs if s.get("pass")]
        best = max([s.get("score") or 0 for s in good] or [0])
        lines.append("Submissions: %d (%d passing; best score %s)"
                     % (len(subs), len(good), C.format_score(best, bool(good))))
    else:
        lines.append("Submissions: none yet")
    return lines


def teacher_context_extra(root, state):
    try:
        text = "RACE: division %s" % C.division_summary(root)
        from racetool import records
        recent = records.last_records(root, 1)
        if recent:
            text += "; last bench: %s" % C.record_line(recent[-1])
        return text + "."
    except Exception:
        return ""


def on_reset(root):
    import shutil
    shutil.rmtree(os.path.join(root, ".workshop", "race"), ignore_errors=True)
