"""Gate logic: the verified-gate condition and the crypto-gate level checks.

The level checks (checks/levelN.py) call `evaluate(root, level)`, which reads
the signed bench log and returns (ok, sentence). On success the check prints
`success_line(level)` and nothing else; make_answers.py hashes the same text.
"""

import json

from racetool import common as C

L1_MAX_SECONDS = 10.0
L2_MAX_SECONDS = 60.0


def success_line(level):
    """The exact stdout of a passing level check."""
    return json.dumps({"level": level, "ok": True}, sort_keys=True) + "\n"


# ------------------------------------------------------------- conditions

def submitted_ok(root, state, manifest):
    level = int(state.get("level", 0))
    subs = [s for s in (state.get("records") or {}).get("submissions") or []
            if s.get("level") == level]
    good = [s for s in subs if s.get("pass") is True]
    if good:
        best = max(s.get("score") or 0 for s in good)
        return True, "%d passing submission(s); best score %s" % (
            len(good), C.format_score(best))
    if subs:
        return False, ("%d submission(s) at this level, none passing yet. Fix the "
                       "entry, commit it and run ./race submit again." % len(subs))
    return False, ("no submission at this level yet. Commit your entry and run "
                   "./race submit in the gate terminal.")


conditions = {"submitted_ok": submitted_ok}


# ------------------------------------------------------------ level checks

def _bad_note(root, pep):
    bad = C.bad_record_count(root, pep)
    if not bad:
        return ""
    return (" (%d line(s) in the bench log have bad signatures and do not count)"
            % bad)


def check_level0(root, records, pep):
    here = [r for r in records if r.get("level") == 0 and not r.get("error")]
    refs = {r["n"] for r in here if r.get("impl") == "reference"
            and isinstance(r.get("n"), int) and 500 <= r["n"] <= 4000
            and r.get("pass") is True}
    profiles = [r for r in here if r.get("impl") == "profile"
                and r.get("sqrt_calls") is not None]
    if len(refs) < 3:
        fast = [r for r in here if r.get("impl") == "fast"]
        sizes = ", ".join(str(n) for n in sorted(refs)) or "none"
        if fast and not refs:
            return False, ("%d bench run(s) were recorded for fast, not reference: run "
                           "make bench N=500 IMPL=reference, then N=1000 and N=2000%s"
                           % (len(fast), _bad_note(root, pep)))
        if fast:
            return False, ("%d bench run(s) were recorded for fast, not reference, and "
                           "the reference has only %d of the 3 sizes needed (N = %s): "
                           "run make bench N=... IMPL=reference for more sizes between "
                           "500 and 4000%s" % (len(fast), len(refs), sizes,
                                                 _bad_note(root, pep)))
        return False, ("no bench runs" if not refs else
                       "reference runs at %d of the 3 different sizes needed (N = %s)"
                       % (len(refs), sizes)) + (
            ": run make bench N=500 IMPL=reference, then N=1000 and N=2000"
            " (any 3 sizes from 500 to 4000)") + _bad_note(root, pep)
    if not profiles:
        return False, ("reference runs are recorded but no profile yet: run make "
                       "profile" + _bad_note(root, pep))
    return True, "reference runs at N = %s and a profile" % ", ".join(
        str(n) for n in sorted(refs))


def _stopped(error, how):
    """Sentence tail for a run that was killed or stopped, naming the reason."""
    reason = error.replace("; estimate before you run", "")
    if reason.startswith("killed: "):
        verb = "was killed"
        reason = reason[len("killed: "):]
    else:
        verb = "was stopped"
    advice = "fix fast.py, then run %s again." % how
    if "resident memory" in reason:
        advice = "Estimate memory before you run, " + advice
    else:
        advice = advice[0].upper() + advice[1:]
    return "%s: %s. %s" % (verb, reason.rstrip("."), advice)


def _fast_check(root, records, pep, level, catalogue, n, max_seconds, need_exact,
                need_toml):
    how = "make bench N=%d" % n
    candidates = [r for r in records if r.get("level") == level
                  and r.get("impl") == "fast" and r.get("catalogue") == catalogue
                  and r.get("n") == n]
    if not candidates:
        return False, ("no fast run at N = %d recorded at this level yet: run %s%s"
                       % (n, how, _bad_note(root, pep)))
    current_src = C.source_hash(root)
    current_toml = C.toml_hash(root)

    def problem(r):
        if r.get("error") == C.CHANGED_DURING_RUN:
            return ("is stale: paircount/ or race.toml changed while it was running; "
                    "run %s again" % how)
        if r.get("error"):
            return _stopped(r["error"], how)
        if r.get("pass") is not True:
            return ("does not match the golden counts (%d bin(s) differ, %s division): "
                    "fix fast.py and run %s again" % (len(r.get("diff") or []),
                                                      r.get("division"), how))
        if need_exact and r.get("division") != "exact":
            return ("used the %s division, but this level needs exact: set "
                    "name = \"exact\" in race.toml and run %s again"
                    % (r.get("division"), how))
        if not isinstance(r.get("seconds"), (int, float)) or r["seconds"] >= max_seconds:
            return ("took %s; this level needs under %d s: make fast.py faster and "
                    "run %s again" % (C.format_seconds(r.get("seconds")),
                                      max_seconds, how))
        if not isinstance(r.get("peak_rss_bytes"), int) \
                or r["peak_rss_bytes"] >= C.PASS_RSS_BYTES:
            return ("peaked at %s of memory; this level needs under %s: use less "
                    "memory and run %s again" % (C.format_gb(r.get("peak_rss_bytes")),
                                                 C.format_gb(C.PASS_RSS_BYTES), how))
        if r.get("source_hash") != current_src:
            return ("is stale: paircount/ (fast.py or another file) changed since "
                    "that run; run %s again" % how)
        if need_toml and r.get("toml_hash") != current_toml:
            return ("is stale: race.toml changed since that run; run %s again" % how)
        return None

    for r in candidates:
        if problem(r) is None:
            return True, "fast run at N = %d: %s, %s, %s" % (
                n, C.format_seconds(r["seconds"]), C.format_gb(r["peak_rss_bytes"]),
                r.get("division"))
    return False, "your last fast run at N = %d %s" % (n, problem(candidates[-1]))


def evaluate(root, level):
    """(ok, sentence) for the crypto gate that leaves `level`."""
    pep = C.pepper(root)
    records = C.valid_records(root, pep)
    if level == 0:
        return check_level0(root, records, pep)
    if level == 1:
        return _fast_check(root, records, pep, 1, "mock_20k", 20000,
                           L1_MAX_SECONDS, need_exact=True, need_toml=False)
    if level == 2:
        return _fast_check(root, records, pep, 2, "mock_200k", 200000,
                           L2_MAX_SECONDS, need_exact=False, need_toml=True)
    return False, "there is no bench check for level %d" % level


def run_check(root, level, out, err):
    """Entry point for checks/levelN.py; returns the exit status."""
    try:
        ok, sentence = evaluate(root, level)
    except Exception as exc:
        err.write("the check could not read the bench evidence: %s\n" % exc)
        return 1
    if not ok:
        err.write(sentence.rstrip(".") + ".\n")
        return 1
    out.write(success_line(level))
    return 0
