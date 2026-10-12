"""./race submit and ./race install-solution (humans, in the gate terminal).

submit: refuse unless paircount/ and race.toml are committed and race.toml is
valid; decrypt .vault/scoring.pack (scoring secret from keys.bin) to a temp
dir; run the entry on the hidden catalogue through bench/harness.py (same
memory and time limits, a fresh process per repeat); if it passes, time
hidden calibration.py the same way on every submit (no cache, so a busy
machine affects only that submit); score = calibration / entry seconds;
record the submission in state and as a signed `submission` line in the
bench log; print the board line. The temp dir is always removed.

The hidden golden counts never reach the output or the log: the harness
reports only the number of failing bins and the largest difference.
"""

import glob
import json
import os
import shutil
import subprocess
import tempfile

from gatekit import crypto, packs, state as st, tty
from racetool import common as C
from racetool import records

HIDDEN_CATALOGUE = "mock_hidden_200k.npy"
HIDDEN_GOLDEN = "golden_hidden.json"
CALIBRATION = "calibration.py"


def _dirty_entry(root):
    """Uncommitted changes under paircount/ or to race.toml.

    Untracked compiled artefacts (.so, .dylib, .o) are allowed: they are
    built from committed sources on first import.
    """
    code, out, err = C.git(root, "status", "--porcelain", "--", "paircount", "race.toml")
    if code != 0:
        raise C.RaceError("git status failed: %s" % err.strip())
    dirty = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status, path = line[:2], line[3:].strip().strip('"')
        if status == "??" and path.endswith(C.BUILD_ARTEFACTS):
            continue
        dirty.append(path)
    return dirty


def _run_harness(root, python, args):
    """Run bench/harness.py bench with tool-only options; return the result record."""
    fd, out = tempfile.mkstemp(prefix="race-result-", suffix=".json")
    os.close(fd)
    os.unlink(out)
    try:
        proc = subprocess.run([python, C.harness_path(root), "bench"] + args
                              + ["--no-record", "--json-out", out], cwd=root)
        if proc.returncode == 2 or not os.path.exists(out):
            raise C.RaceError("the bench harness refused or crashed (exit %d); "
                              "see the message above" % proc.returncode)
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)
    finally:
        if os.path.exists(out):
            os.unlink(out)


def _reason(result):
    if result.get("error"):
        return result["error"]
    if result.get("pass") is not True:
        return ("%d bin(s) fail against the hidden golden counts (%s division; "
                "largest difference %d counts)"
                % (result.get("fail_bins") or 0, result.get("division"),
                   result.get("diff_max") or 0))
    if result.get("peak_rss_bytes", 0) >= C.PASS_RSS_BYTES:
        return "peak memory %s is over the %s ceiling" % (
            C.format_gb(result["peak_rss_bytes"]), C.format_gb(C.PASS_RSS_BYTES))
    if not isinstance(result.get("seconds"), (int, float)) or result["seconds"] <= 0:
        return "no time was measured"
    return ""


def cmd_submit(root, args):
    state = C.load_state(root)
    python = C.venv_python(root)
    if not os.path.exists(C.harness_path(root)):
        raise C.RaceError("bench/harness.py is missing; restore it with "
                          "git checkout -- bench")
    dirty = _dirty_entry(root)
    if dirty:
        raise C.RaceError("commit your entry first; uncommitted changes in: %s. "
                          "The board line names a commit, so the entry must be in "
                          "it (git add paircount race.toml && git commit)."
                          % ", ".join(dirty))
    division = C.read_division(root)
    commit = C.git_head(root)
    if commit is None:
        raise C.RaceError("this folder has no git commit to name on the board")
    keys = C.vault_keys(root)
    if "scoring" not in keys:
        raise C.RaceError("no scoring secret in keys.bin; rebuild the repo")
    level = state.get("level", 0)
    recs = C.records(state)
    base = tempfile.mkdtemp(prefix="race-submit-")
    try:
        hidden = os.path.join(base, "hidden")
        print("Opening the hidden catalogue...")
        C.open_scoring_pack(root, bytes.fromhex(keys["scoring"]), hidden)
        catalogue = C.find_file(hidden, HIDDEN_CATALOGUE)
        golden = C.find_file(hidden, HIDDEN_GOLDEN)
        calibration = C.find_file(hidden, CALIBRATION)
        if not (catalogue and golden and calibration):
            raise C.RaceError("the scoring pack is incomplete; tell a facilitator")
        hidden_args = ["--catalogue", catalogue, "--golden", golden,
                       "--label", "hidden"]
        print("Running your entry on the hidden catalogue (limits: %s to pass, "
              "%g GB cap, %d s)...\n" % (C.format_gb(C.PASS_RSS_BYTES),
                                         C.DEFAULT_RSS_CAP_GB, C.DEFAULT_TIMEOUT_S))
        result = _run_harness(root, python, ["--impl", "fast"] + hidden_args)
        reason = _reason(result)
        passed = not reason
        cal = None
        if passed:
            print("\nTiming the calibration counter on this machine, now, so "
                  "the score is fair to its current load...\n")
            cal_result = _run_harness(root, python, ["--impl-file", calibration]
                                      + hidden_args)
            if _reason(cal_result):
                raise C.RaceError("the calibration counter failed on this machine "
                                  "(%s); tell a facilitator" % _reason(cal_result))
            cal = cal_result["seconds"]
    finally:
        shutil.rmtree(base, ignore_errors=True)

    score = round(cal / result["seconds"], 4) if passed else 0.0
    submission = {
        "ts": C.now_iso(), "level": level, "commit": commit,
        "division": division["name"], "sigma_fraction": division["sigma_fraction"],
        "pass": passed, "seconds": result.get("seconds"),
        "calibration_seconds": cal,
        "score": score, "peak_rss_bytes": result.get("peak_rss_bytes"),
        "reason": reason,
    }
    recs["submissions"].append(submission)
    C.save_state(root, state)
    line = {k: v for k, v in result.items() if k != "diff"}
    line.update({"ts": submission["ts"], "level": level, "impl": "submission",
                 "catalogue": "hidden", "pass": passed, "score": score,
                 "calibration_seconds": submission["calibration_seconds"],
                 "reason": reason})
    C.append_record(root, line)

    print("")
    if passed:
        print("PASSED on the hidden catalogue: %s (calibration %s): score %s" % (
            C.format_seconds(result["seconds"]), C.format_seconds(cal),
            C.format_score(score)))
    else:
        print("NOT PASSED: %s. Score 0." % reason)
    print("Copy this line to the board (add your group name):")
    print("  " + records.board_line(submission))
    return 0


def _verify_master(root, secret):
    try:
        with open(os.path.join(root, ".vault", "master.check"), "rb") as fh:
            packs.open_pack(fh.read(), [secret])
    except (OSError, crypto.PackError):
        return False
    return True


def cmd_install_solution(root, args):
    if len(args) != 1 or not args[0].isdigit():
        raise C.RaceError("usage: ./race install-solution <level> (1, 2 or 3)")
    level = int(args[0])
    state = C.load_state(root)
    passphrase = tty.ask_secret("Master passphrase: ")
    if not passphrase.strip():
        raise C.RaceError("no passphrase given")
    secret = crypto.master_secret(passphrase)
    if not _verify_master(root, secret):
        st.log_failed_attempt(state, "master")
        C.save_state(root, state)
        raise C.RaceError("that is not the master passphrase")
    base = tempfile.mkdtemp(prefix="race-solution-")
    copied = []
    removed = []
    try:
        hidden = os.path.join(base, "hidden")
        C.open_scoring_pack(root, secret, hidden)
        src = os.path.join(hidden, "solutions", "level%d" % level)
        if not os.path.isdir(src):
            raise C.RaceError("there is no solution for level %d" % level)
        dest = os.path.join(root, "paircount")
        for lib in sorted(glob.glob(os.path.join(dest, "_pairs*.so"))):
            os.unlink(lib)
            removed.append(os.path.basename(lib))
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if name.endswith(".pyc"):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, name), src)
                target = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy(os.path.join(dirpath, name), target)
                copied.append("paircount/" + rel.replace(os.sep, "/"))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("Installed the level %d solution: %s" % (level, ", ".join(copied)))
    if removed:
        print("Removed compiled libraries: %s (rebuilt on first import)."
              % ", ".join(removed))
    print("Run make bench to record it, and commit before ./race submit.")
    st.append_log(root, "Facilitator installed the level %d solution" % level,
                  "Files: %s" % ", ".join(copied))
    return 0
