#!/usr/bin/env python3
"""Scripted walkthrough of dist/speed-run (PLAN.md section 7).

usage: selftest/run.py --master-passphrase-file PATH [--dist DIR] [--skip-build]
                       [--skip-assets]

Rebuilds the participant repo (keeping its .venv), checks the hidden assets,
then plays every level as a group would: bench runs through make, sample
entries from selftest/samples copied into paircount/, human-only commands
(gate unlock, race submit, race install-solution, gate skip/reset) driven
through a pty. Prints the measured timings. Exit code 0 only when every
check passes.
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXERCISE = os.path.dirname(HERE)
TOP = os.path.dirname(os.path.dirname(EXERCISE))
sys.path.insert(0, os.path.join(TOP, "gatekit"))

from gatekit import ptyhelper, state as st  # noqa: E402

SAMPLES = os.path.join(HERE, "samples")
SOLUTIONS = os.path.join(EXERCISE, "hidden", "solutions")
PY = sys.executable
GB = 1e9
ZEROS_ENTRY = """import numpy as np


def count_pairs(pos, edges):
    return np.zeros(len(edges) - 1, dtype=np.int64)
"""
TOUCHING_ENTRY = """import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def count_pairs(pos, edges):
    with open(os.path.join(HERE, "touched.txt"), "a") as fh:
        fh.write("x")
    return np.zeros(len(edges) - 1, dtype=np.int64)
"""
checks = []
timings = []


class Fail(Exception):
    pass


def check(ok, label, detail=""):
    checks.append((ok, label))
    print("[%s] %s%s" % ("ok  " if ok else "FAIL", label, (": " + detail) if detail else ""))
    if not ok:
        raise Fail(label)


def section(title):
    print("\n=== %s" % title)


def flat(text):
    return " ".join(text.replace("\r", "").split())


class Repo:
    def __init__(self, root):
        self.root = root
        self.venv = os.path.join(root, ".venv", "bin", "python")

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    # -- process helpers
    def run(self, argv, ok_codes=(0,), env=None):
        proc = subprocess.run(argv, cwd=self.root, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, env=env)
        if ok_codes is not None and proc.returncode not in ok_codes:
            raise Fail("%s -> %d\n%s%s" % (" ".join(argv), proc.returncode,
                                            proc.stdout[-1500:], proc.stderr[-1500:]))
        return proc

    def git(self, *args):
        return self.run(["git", "-c", "commit.gpgsign=false"] + list(args)).stdout.strip()

    def commit_entry(self, message):
        self.git("add", "-A", "--", "paircount", "race.toml")
        self.git("commit", "-q", "-m", message)

    def make(self, *args, env=None):
        """make <args>; returns (exit code, stdout + stderr)."""
        full = dict(os.environ, **(env or {}))
        proc = self.run(["make"] + list(args), ok_codes=None, env=full)
        return proc.returncode, proc.stdout + proc.stderr

    def pty(self, argv, answers=(), timeout=180):
        return ptyhelper.run_pty([PY] + argv, answers, cwd=self.root, timeout=timeout)

    def gate(self, *args, answers=(), timeout=180):
        return self.pty([self.path("gate")] + list(args), answers, timeout)

    def race(self, *args, answers=(), timeout=600):
        return self.pty([self.path("race")] + list(args), answers, timeout)

    def gate_check(self):
        proc = self.run([PY, self.path("gate"), "check"], ok_codes=(0, 1))
        return proc.returncode, flat(proc.stdout + proc.stderr)

    def state(self):
        return st.load_state(self.root)

    def level(self):
        return self.state()["level"]

    def records(self):
        try:
            with open(self.path(".workshop", "race", "bench.jsonl")) as fh:
                return [json.loads(line) for line in fh if line.strip()]
        except OSError:
            return []

    def last_record(self):
        recs = self.records()
        return recs[-1] if recs else {}

    # -- file helpers
    def install(self, sample):
        """Copy a sample's files into paircount/ (fresh mtimes, like an edit)."""
        src = os.path.join(SAMPLES, sample)
        for name in sorted(os.listdir(src)):
            shutil.copy(os.path.join(src, name), self.path("paircount", name))

    def set_toml(self, sample):
        shutil.copy(os.path.join(SAMPLES, sample), self.path("race.toml"))

    def write_entry(self, text):
        with open(self.path("paircount", "fast.py"), "w") as fh:
            fh.write(text)

    def source_hash(self):
        code = ("import sys; sys.path.insert(0, '.gatekit'); "
                "from racetool import common; print(common.source_hash('.'))")
        return self.run([PY, "-c", code]).stdout.strip()


def build(args):
    section("1. Build and preflight")
    cmd = [PY, os.path.join(TOP, "tools", "build.py"), "speed-run",
           "--master-passphrase-file", args.master_passphrase_file, "--out", args.dist,
           "--keep-venv"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    check(proc.returncode == 0, "tools/build.py speed-run", proc.stderr[-500:])
    print(proc.stdout.strip())


def preflight(repo):
    code, out = repo.pty([repo.path("preflight")], timeout=300)
    check(code == 0 and "Preflight passed" in out, "./preflight passes through a pty",
          out[-600:] if code else "")


def verify_assets(repo):
    section("2. Hidden assets (hidden/verify_assets.py on the source tree)")
    started = time.time()
    proc = subprocess.run([repo.venv, os.path.join(EXERCISE, "hidden", "verify_assets.py")],
                          cwd=EXERCISE, capture_output=True, text=True)
    lines = proc.stdout.splitlines()
    for line in lines:
        if "scipy" in line or "(iv) C FMA" in line or "!!!" in line or "CHECK FAILED" in line:
            print("    " + line.strip())
    print("    " + "\n    ".join(lines[lines.index("== timings"):] if "== timings" in lines
                                  else lines[-25:]))
    check(proc.returncode == 0 and "ALL CHECKS PASSED" in proc.stdout,
          "hidden/verify_assets.py exits 0 (%.0f s)" % (time.time() - started),
          (proc.stdout[-1500:] + proc.stderr[-800:]) if proc.returncode else "")
    check("DID NOT FIRE" not in proc.stdout, "the FMA variant (iv) fired on every catalogue")
    for sample, solution in (("l1_chunked", "level1"), ("l2_celllist", "level2"),
                             ("l3_c_off", "level3")):
        names = sorted(os.listdir(os.path.join(SOLUTIONS, solution)))
        same = all(filecmp.cmp(os.path.join(SAMPLES, sample, n),
                               os.path.join(SOLUTIONS, solution, n), shallow=False)
                   for n in names if not n.startswith("__"))
        check(same, "samples/%s is a current copy of hidden/solutions/%s" % (sample, solution))


def talked(out, prompt, label):
    """The unlock screen shows the talk prompt and asks for nothing."""
    text = " ".join(out.split())
    check("Talk it over (30 seconds, nothing to type):" in text and prompt in text
          and "Next: swap the Driver" in text, label, text[-300:])


def level0(repo):
    section("3. Level 0: measure before you touch anything")
    check(repo.level() == 0, "starts at level 0")
    check(repo.git("tag", "-l", "start") == "start", "tag start exists")
    check(repo.git("status", "--porcelain") == "", "clean working tree")
    check(repo.records() == [], "bench log is empty")
    code, out = repo.gate("unlock")
    check(code == 1 and "no bench runs" in out, "unlock refused before any run", flat(out)[-300:])
    code, out = repo.make("bench", "N=500", "IMPL=fast")
    check(code == 0 and "note: Level 0 measures the reference" in out,
          "make bench IMPL=fast at level 0 runs, with a note", "" if code == 0 else out[-400:])
    check(re.search(r"time \(import \+ count\)\s+\S+ s\s+\(median of 3 runs, each in a "
                    r"fresh process", out) is not None,
          "time line reports import + count, median of 3 fresh processes", flat(out)[-300:])
    code, out = repo.gate_check()
    check(code == 1 and "recorded for fast, not reference" in out,
          "gate check: fast run named as the wrong impl", out[-300:])
    for n in (500, 1000, 2000):
        code, out = repo.make("bench", "N=%d" % n, "IMPL=reference")
        rec = repo.last_record()
        check(code == 0 and "recorded as run" in out and rec.get("impl") == "reference"
              and rec.get("n") == n and rec.get("pass") is True,
              "make bench N=%d IMPL=reference recorded, correct" % n,
              "%.3f s" % (rec.get("seconds") or -1) if code == 0 else out[-400:])
    code, out = repo.make("bench", "N=8000", "IMPL=reference")
    check(code == 2 and "capped at N <= 4000" in out and "from your fit" in out,
          "reference refused above N = 4000, quoting the 200k time from the fit", flat(out)[-250:])
    code, out = repo.gate_check()
    check(code == 1 and "no profile yet" in out, "gate check asks for a profile", out[-200:])
    code, out = repo.make("profile")
    rec = repo.last_record()
    check(code == 0 and "499,500 calls" in out and rec.get("sqrt_calls") == 499500,
          "make profile reports 499,500 math.sqrt calls", out[-300:] if code else "")
    code, out = repo.make("fit")
    alpha = re.search(r"alpha \(scaling exponent\)\s+([\d.]+)", out)
    check(code == 0 and alpha and 1.8 <= float(alpha.group(1)) <= 2.2,
          "make fit exponent in [1.8, 2.2]", alpha.group(1) if alpha else out[-300:])
    print("    " + "\n    ".join(line for line in out.splitlines() if "predicted" in line))
    code, out = repo.gate("unlock", answers=[("N = 1000?", "N(N+1)/2 = 500500")])
    check(code == 1 and "Not quite" in out, "wrong pair count (N(N+1)/2 = 500500) rejected")
    code, out = repo.gate("unlock", answers=[("N = 1000?", "N(N-1)/2 = 499,500")])
    check(code == 0 and "Level 1 unlocked" in out, "N(N-1)/2 = 499,500 unlocks level 1", flat(out)[-300:])
    check(os.path.exists(repo.path("BRIEF.md")), "BRIEF.md appears")
    talked(out, "From your fit, what runtime does the reference predict at N = 200,000, and how did you get it?",
           "level 0 unlock shows the talk prompt")


def level1(repo):
    section("4. Level 1: vectorise, and survive the memory wall")
    code, out = repo.gate_check()
    check(code == 1 and "no fast run at N = 20000" in out, "gate check: no 20k run yet", out[-200:])
    tool_only_runs(repo)
    changed_during_run(repo)
    repo.install("l1_naive_matrix")
    code, out = repo.make("bench", "N=20000", env={"RACE_RSS_CAP_GB": "9"})
    rec = repo.last_record()
    check("RACE_RSS_CAP_GB=9 is above the 2.5 GB limit and is ignored" in out,
          "RACE_RSS_CAP_GB above 2.5 is ignored with a note", flat(out)[-300:])
    check(code != 0 and re.search(r"STOPPED\s+killed: resident memory passed 2\.5 GB", out)
          and "recorded as run" in out, "naive N x N matrix killed at the 2.5 GB cap",
          "peak %.1f GB" % ((repo.last_record().get("peak_rss_bytes") or 0) / GB))
    check("memory" in (rec.get("error") or "") and rec.get("pass") is False
          and rec.get("impl") == "fast" and rec.get("n") == 20000,
          "its record's error says memory", repr(rec.get("error")))
    code, out = repo.gate_check()
    check(code == 1 and "was killed: resident memory passed 2.5 GB" in flat(out)
          and "Estimate memory before you run" in flat(out),
          "gate check names the killed run", out[-250:])
    repo.install("l1_chunked")
    code, out = repo.make("bench", "N=20000")
    rec = repo.last_record()
    secs, rss = rec.get("seconds") or 99, rec.get("peak_rss_bytes") or 9e9
    check(code == 0 and "correct       yes" in out and rec.get("pass") is True
          and rec.get("division") == "exact" and secs < 10 and rss < 1.5 * GB,
          "chunked entry passes exact, < 10 s, < 1.5 GB", "%.2f s, %.2f GB" % (secs, rss / GB))
    timings.append(("bench 20k, chunked numpy (level 1)", "%.2f s, %.2f GB" % (secs, rss / GB)))
    before = repo.source_hash()
    with open(repo.path("paircount", "x.so"), "wb") as fh:
        fh.write(b"not a library")
    after = repo.source_hash()
    os.unlink(repo.path("paircount", "x.so"))
    check(before == after and len(before) == 64,
          "source_hash ignores compiled artefacts (paircount/x.so)", before[:12])
    with open(repo.path("paircount", "fast.py"), "a") as fh:
        fh.write("\n# a tweak after the run\n")
    code, out = repo.gate("unlock")
    check(code == 1 and "changed since that run" in flat(out),
          "unlock refused: stale evidence after editing fast.py", flat(out)[-300:])
    repo.install("l1_chunked")
    code, out = repo.gate("unlock", answers=[("float64 matrix?", "500")])
    check(code == 1 and "Not quite" in out, "wrong matrix size (500 GB) rejected")
    code, out = repo.gate("unlock", answers=[("float64 matrix?", "200000^2 * 8 / 1e9 = 320")])
    check(code == 0 and "Level 2 unlocked" in out, "'200000^2 * 8 / 1e9 = 320' unlocks level 2", flat(out)[-300:])
    talked(out, "What was your memory estimate before the 20k run, and what did the harness measure?",
           "level 1 unlock shows the talk prompt")


def tool_only_runs(repo):
    """Tool-only harness options never reach the bench log (review item 1)."""
    repo.write_entry(ZEROS_ENTRY)
    scratch = tempfile.mkdtemp(prefix="selftest-golden-")
    try:
        golden = os.path.join(scratch, "my.json")
        with open(golden, "w") as fh:
            json.dump({"counts": [0] * 15}, fh)
        before = len(repo.records())
        code, out = repo.make("bench", "N=20000",
                              "CAT=data/mock_20k.npy --golden %s" % golden)
        check(code != 0 and "CAT must be one catalogue name" in out
              and len(repo.records()) == before,
              "make bench refuses a CAT that is not one catalogue name", flat(out)[-200:])
        proc = repo.run([repo.venv, repo.path("bench", "harness.py"), "bench", "--impl", "fast",
                         "--n", "20000", "--catalogue", "data/mock_20k.npy",
                         "--golden", golden], ok_codes=None)
        out = proc.stdout + proc.stderr
        check(proc.returncode == 0 and "correct       yes" in out
              and "not recorded (tool-only options)" in out
              and len(repo.records()) == before,
              "zeros entry + zeros --golden passes but is not recorded", flat(out)[-300:])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    code, out = repo.gate_check()
    check(code == 1 and "no fast run at N = 20000" in out,
          "gate check still refuses after the --golden run", out[-200:])


def changed_during_run(repo):
    """An entry that edits paircount/ while it runs is recorded as stale (item 3)."""
    repo.write_entry(TOUCHING_ENTRY)
    code, out = repo.make("bench", "N=20000")
    rec = repo.last_record()
    os.unlink(repo.path("paircount", "touched.txt"))
    check(code != 0 and "changed during the run" in out and rec.get("pass") is None
          and rec.get("error") == "paircount/ or race.toml changed during the run",
          "paircount/ edited during a run: recorded with an error, pass null",
          repr(rec.get("error")))
    code, out = repo.gate_check()
    check(code == 1 and "changed while it was running" in out and "run make bench N=20000 again"
          in out, "gate check rejects it as stale and says to re-run", out[-250:])


def bench_200k(repo, label, expect_pass):
    code, out = repo.make("bench", "N=200000")
    rec = repo.last_record()
    check((code == 0) == expect_pass and rec.get("n") == 200000
          and rec.get("pass") is expect_pass and not rec.get("error"),
          label, "%.2f s, %s" % (rec.get("seconds") or -1, rec.get("division")))
    return out, rec


def level2(repo):
    section("5. Level 2: reduce the work, defend the answer")
    repo.install("l2_sumsq")
    out, rec = bench_200k(repo, "s < e*e cell list fails the exact division", False)
    check("correct       NO" in out and "<- fails" in out and "difference" in out,
          "harness prints the diff table with failing bins")
    print("\n".join("    " + line for line in out.splitlines() if "<- fails" in line))
    repo.set_toml("race_toleranced.toml")
    out, rec = bench_200k(repo, "s < e*e passes toleranced at sigma 0.1", True)
    check("within the toleranced division" in out and rec.get("division") == "toleranced"
          and rec.get("sigma_fraction") == 0.1 and rec.get("diff"),
          "record shows toleranced, sigma 0.1, bins differ")
    before = len(repo.records())
    repo.set_toml("race_invalid.toml")
    proc = repo.run([repo.venv, repo.path("bench", "harness.py"), "bench", "--impl", "fast",
                     "--n", "200000"], ok_codes=None)
    check(proc.returncode == 2 and "sigma_fraction <= 0.2" in proc.stderr
          and "0.5" in proc.stderr and len(repo.records()) == before,
          "invalid race.toml (sigma 0.5) refused by the harness, exit 2, nothing recorded",
          flat(proc.stdout + proc.stderr)[-300:])
    proc = repo.run([PY, repo.path("race"), "status"])
    check("Division: INVALID" in proc.stdout, "./race status flags the invalid race.toml")
    repo.git("checkout", "--", "race.toml")
    code, out = repo.gate_check()
    check(code == 1 and "race.toml changed since that run" in out,
          "gate check: toleranced evidence stale once race.toml changes", out[-250:])
    repo.install("l2_celllist")
    out, rec = bench_200k(repo, "cell list passes exact at 200k", True)
    check(rec.get("division") == "exact" and not rec.get("diff") and rec["seconds"] < 60
          and rec["peak_rss_bytes"] < 1.5 * GB, "exact, < 60 s, < 1.5 GB",
          "%.2f s, %.2f GB" % (rec["seconds"], rec["peak_rss_bytes"] / GB))
    timings.append(("bench 200k, numpy cell list (level 2)", "%.2f s (median of %d), %.2f GB"
                    % (rec["seconds"], rec["repeats"], rec["peak_rss_bytes"] / GB)))
    code, out = repo.gate("unlock", answers=[("(a-d):", "a")])
    check(code == 1 and "Not quite" in out, "wrong letter (a) rejected")
    code, out = repo.gate("unlock", answers=[("(a-d):", "c - the second only")])
    check(code == 0 and "Level 3 unlocked" in out, "'c - the second only' unlocks level 3", flat(out)[-300:])
    talked(out, "Which division did you enter, and what evidence decided it?",
           "level 2 unlock shows the talk prompt")


def submit(repo, label):
    started = time.time()
    code, out = repo.race("submit")
    wall = time.time() - started
    check(code == 0, "./race submit ran (%s)" % label, flat(out)[-500:] if code else "%.1f s" % wall)
    return out, wall, repo.state()["records"]["submissions"][-1]


def level3(repo):
    section("6. Level 3: open race")
    proc = repo.run([PY, repo.path("race"), "submit"], ok_codes=None)
    check(proc.returncode == 3 and "for humans" in proc.stderr,
          "./race submit refused without a terminal (exit 3)", flat(proc.stderr)[-200:])
    check(repo.git("status", "--porcelain", "--", "paircount") != "", "paircount/ is dirty")
    code, out = repo.race("submit")
    check(code == 1 and "commit your entry first" in out and "paircount/fast.py" in flat(out),
          "submit refused on a dirty paircount/", flat(out)[-300:])
    check(not repo.state().get("records", {}).get("submissions"), "nothing submitted")
    code, out = repo.gate("unlock")
    check(code == 1 and "no submission at this level" in out, "unlock refused before a submission")
    repo.install("l3_c_default")
    repo.commit_entry("C counter, default contraction")
    out, wall, sub = submit(repo, "C, default contraction")
    fails = re.search(r"NO: (\d+) of 15 bins fail against the hidden golden counts "
                      r"\(largest difference (\d+) counts\)", flat(out))
    check("NOT PASSED" in out and "Score 0" in out and fails and int(fails.group(1)) > 0
          and "make check N=200000" in out and sub["pass"] is False and sub["score"] == 0,
          "FMA build fails exact on the hidden catalogue, scores 0, failing-bin count shown",
          sub.get("reason", ""))
    check("<- fails" not in out and "yours" not in out,
          "no per-bin diff table for the hidden catalogue")
    line = repo.last_record()
    check(line.get("impl") == "submission" and "diff" not in line
          and line.get("fail_bins") == int(fails.group(1)),
          "bench-log submission line has the count and max difference only")
    check(sub.get("calibration_seconds") is None, "no calibration run for a failing entry")
    proc = repo.run([PY, repo.path("race"), "board"])
    check("FAIL" in proc.stdout and "score  0.00" in proc.stdout, "board lists the failing entry")
    code, out = repo.gate("unlock")
    check(code == 1 and "none passing yet" in out, "unlock refused with only a failing submission")
    repo.install("l3_c_off")
    repo.commit_entry("C counter, -ffp-contract=off")
    out, wall, sub = submit(repo, "C, -ffp-contract=off, with calibration")
    score = re.search(r"score (\d+\.\d\d)\b", out)
    check("PASSED on the hidden catalogue" in out and sub["pass"] is True and sub["score"] > 1
          and score and score.group(1) == "%.2f" % sub["score"],
          "-ffp-contract=off passes, score > 1 (2 decimals)", "score %s" % sub["score"])
    cal = sub.get("calibration_seconds")
    check("Timing the calibration counter" in out and isinstance(cal, (int, float)) and cal > 0
          and "calibration_seconds" not in repo.state()["records"],
          "calibration timed on this submit, not cached in state", "%.2f s" % (cal or 0))
    timings.append(("submit, C entry + calibration (wall)", "%.1f s" % wall))
    timings.append(("hidden 200k: C entry / calibration", "%.2f s / %.2f s (score %.2f)"
                    % (sub["seconds"], cal, sub["score"])))
    out, wall, sub2 = submit(repo, "again, calibration re-timed")
    check(sub2["pass"] is True and "Timing the calibration counter" in out
          and isinstance(sub2["calibration_seconds"], (int, float)),
          "second submit re-times the calibration",
          "%.2f s then %.2f s" % (cal, sub2["calibration_seconds"] or 0))
    timings.append(("submit again (wall)", "%.1f s" % wall))
    proc = repo.run([PY, repo.path("race"), "board"])
    board = proc.stdout.strip().splitlines()
    check(len(board) == 3 and "pass" in board[1]
          and "score %5s" % ("%.2f" % sub["score"]) in board[1],
          "./race board lists all three submissions")
    print("\n".join("    " + line for line in board))
    code, out = repo.gate("unlock")
    check(code == 0 and "Exercise complete. Well done." in out and repo.state()["complete"],
          "level 3 unlock completes the exercise", flat(out)[-300:])
    check("What was your biggest wrong turn, and what evidence showed it?" in flat(out)
          and "Next:" not in out, "final level: talk prompt, no Next line")


def finale(repo, passfile):
    section("7. Facilitator commands, skip and reset")
    with open(passfile) as fh:
        passphrase = fh.read().strip()
    code, out = repo.race("install-solution", "2", answers=[("passphrase:", "wrong-" + passphrase)])
    check(code == 1 and "not the master passphrase" in out, "install-solution: wrong passphrase rejected")
    code, out = repo.race("install-solution", "2", answers=[("passphrase:", passphrase)])
    check(code == 0 and "Installed the level 2 solution: paircount/fast.py" in out,
          "./race install-solution 2 with the master passphrase", flat(out)[-300:])
    check(filecmp.cmp(repo.path("paircount", "fast.py"),
                      os.path.join(SOLUTIONS, "level2", "fast.py"), shallow=False),
          "paircount/fast.py is now the level 2 solution")
    with open(repo.path("LOG.md")) as fh:
        check("installed the level 2 solution" in fh.read(), "install logged to LOG.md")
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and repo.level() == 0 and not os.path.exists(repo.path("BRIEF.md")),
          "./gate reset back to level 0, BRIEF.md removed", flat(out)[-200:])
    check(repo.records() == [], "reset removed the bench log")
    repo.git("reset", "-q", "--hard", "start")
    check(repo.git("status", "--porcelain") == "", "git reset --hard start leaves a clean tree")
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", "wrong-" + passphrase)])
    check(code == 1 and "not the master" in out, "gate skip: wrong passphrase rejected")
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", passphrase),
                                                       ("Reason", "selftest")])
    check(code == 0 and repo.level() == 1 and os.path.exists(repo.path("BRIEF.md")),
          "./gate skip --master at level 0 opens level 1", flat(out)[-300:])
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and "Removed unlocked files: BRIEF.md" in out, "reset removes the brief")
    repo.git("reset", "-q", "--hard", "start")
    repo.git("clean", "-fdq")
    check(repo.level() == 0 and repo.git("status", "--porcelain") == ""
          and repo.records() == [], "repo left clean at level 0")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-passphrase-file", required=True)
    parser.add_argument("--dist", default=os.path.join(TOP, "dist", "speed-run"))
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-assets", action="store_true")
    args = parser.parse_args()
    started = time.time()
    repo = Repo(os.path.abspath(args.dist))
    try:
        if not args.skip_build:
            build(args)
        if not os.path.exists(repo.venv):
            raise Fail("no .venv in %s; run ./preflight there first (it sets up .venv)" % repo.root)
        preflight(repo)
        if not args.skip_assets:
            verify_assets(repo)
        level0(repo)
        level1(repo)
        level2(repo)
        level3(repo)
        finale(repo, args.master_passphrase_file)
    except Fail as exc:
        print("\nSELF-TEST FAILED: %s" % exc)
        return 1
    except ptyhelper.PtyTimeout as exc:
        print("\nSELF-TEST FAILED (pty timeout): %s" % exc)
        return 1
    print("\n=== Summary")
    print("%d checks passed" % len(checks))
    for label, value in timings:
        print("  %-46s %s" % (label, value))
    print("total wall time: %.0f s" % (time.time() - started))
    print("ALL SELF-TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
