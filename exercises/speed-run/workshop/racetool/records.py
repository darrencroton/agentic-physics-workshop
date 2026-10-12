"""./race log, ./race board and the status views of the bench log."""

from racetool import common as C


def _when(ts):
    return (ts or "")[:19].replace("T", " ")


def _rows(root):
    try:
        pep = C.pepper(root)
    except C.RaceError:
        pep = None
    return C.read_log(root, pep), pep


def cmd_log(root, args):
    rows, pep = _rows(root)
    if pep is None:
        print("This repo has no build pepper, so no record can be verified.")
    if not rows:
        print("The bench log is empty. Run make bench N=2000 IMPL=reference to "
              "record a first run.")
        return 0
    print("%3s  %-19s  %-3s  %s" % ("#", "when (UTC)", "lvl", "run"))
    bad = 0
    for i, (rec, ok) in enumerate(rows, 1):
        if rec is None:
            print("%3d  %-19s  %-3s  BAD LINE (not a JSON record; ignored)" % (i, "", ""))
            bad += 1
            continue
        flag = "" if ok else "  BAD SIGNATURE (ignored by the gate)"
        bad += 0 if ok else 1
        print("%3d  %-19s  %-3s  %s%s" % (i, _when(rec.get("ts")), rec.get("level", "?"),
                                          C.record_line(rec), flag))
    if bad:
        print("\n%d record(s) failed verification. Only make bench writes this log; "
              "edited lines do not count." % bad)
    return 0


def board_line(sub):
    return "score %5s | %-10s | %9s | %s | commit %s | %s UTC" % (
        C.format_score(sub.get("score"), sub.get("pass") is True),
        sub.get("division", "?"),
        C.format_seconds(sub.get("seconds")), "pass" if sub.get("pass") else "FAIL",
        (sub.get("commit") or "-")[:7], _when(sub.get("ts"))[11:16])


def cmd_board(root, args):
    state = C.load_state(root)
    subs = C.records(state).get("submissions", [])
    if not subs:
        print("No submissions yet. Commit your entry and run ./race submit in the "
              "gate terminal.")
        return 0
    for i, sub in enumerate(subs, 1):
        line = board_line(sub)
        if sub.get("reason"):
            line += " | %s" % sub["reason"]
        print("%2d  %s" % (i, line))
    return 0


def last_records(root, count=3):
    rows, pep = _rows(root)
    return [rec for rec, ok in rows if ok][-count:]
