#!/usr/bin/env python3
"""Scripted walkthrough of dist/tdd-ladder (BUILD-SPEC Section 7.2).

usage: selftest/run.py --master-passphrase-file PATH [--dist DIR] [--skip-build]

Drives every human-only command through a pty, feeds the sample suites in
as if Claude had written them, and checks the expected score bands, the
gate refusals, the guard and the master skip.  Prints the measured score
runtimes.  Exit code 0 only when every check passes.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXERCISE = os.path.dirname(HERE)
TOP = os.path.dirname(os.path.dirname(EXERCISE))
sys.path.insert(0, os.path.join(TOP, "gatekit"))

from gatekit import ptyhelper, state as st  # noqa: E402

SAMPLES = os.path.join(HERE, "samples")
PY = sys.executable
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


class Repo:
    def __init__(self, root, passfile):
        self.root = root
        self.passfile = passfile
        self.venv = os.path.join(root, ".venv", "bin", "python")

    # -- process helpers
    def run(self, argv, ok_codes=(0,), stdin=subprocess.DEVNULL, env=None):
        proc = subprocess.run(argv, cwd=self.root, capture_output=True, text=True,
                              stdin=stdin, env=env)
        if proc.returncode not in ok_codes:
            raise Fail("%s -> %d\n%s%s" % (" ".join(argv), proc.returncode, proc.stdout, proc.stderr))
        return proc

    def git(self, *args):
        return self.run(["git", "-c", "commit.gpgsign=false"] + list(args)).stdout.strip()

    def commit_all(self, message):
        self.git("add", "-A", "--", "src", "tests", "SPEC.md") if os.path.exists(
            os.path.join(self.root, "SPEC.md")) else self.git("add", "-A", "--", "src", "tests")
        if self.git("status", "--porcelain", "--", "src", "tests"):
            self.git("commit", "-q", "-m", message)

    def pty(self, argv, answers=(), timeout=180):
        code, out = ptyhelper.run_pty([PY] + argv, answers, cwd=self.root, timeout=timeout)
        return code, out

    def gate(self, *args, answers=(), timeout=120):
        return self.pty([os.path.join(self.root, "gate")] + list(args), answers, timeout)

    def tdd(self, *args, answers=(), timeout=300):
        return self.pty([os.path.join(self.root, "tdd")] + list(args), answers, timeout)

    def state(self):
        return st.load_state(self.root)

    def level(self):
        return self.state()["level"]

    def phase(self):
        try:
            with open(os.path.join(self.root, ".tdd", "phase")) as fh:
                return fh.read().strip()
        except OSError:
            return "none"

    # -- file helpers
    def install_sample(self, name, with_binning=True):
        sample = os.path.join(SAMPLES, name)
        tests = os.path.join(self.root, "tests")
        shutil.rmtree(tests, ignore_errors=True)
        shutil.copytree(os.path.join(sample, "tests"), tests)
        open(os.path.join(tests, "__init__.py"), "a").close()
        if with_binning and os.path.exists(os.path.join(sample, "binning.py")):
            shutil.copy(os.path.join(sample, "binning.py"),
                        os.path.join(self.root, "src", "hzbin", "binning.py"))

    def is_stub(self):
        with open(os.path.join(self.root, "src", "hzbin", "binning.py")) as fh:
            return "raise NotImplementedError" in fh.read()

    def guard(self, tool_name, **tool_input):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
        proc = subprocess.run([PY, os.path.join(self.root, ".claude", "hooks", "guard.py")],
                              input=payload, capture_output=True, text=True, env=env, cwd=self.root)
        if not proc.stdout.strip():
            return None, ""
        spec = json.loads(proc.stdout.strip().splitlines()[-1])["hookSpecificOutput"]
        return spec["permissionDecision"], spec["permissionDecisionReason"]

    def score(self):
        code, out = self.tdd("score")
        check(code == 0, "./tdd score ran", out[-400:] if code else "")
        acc = int(re.search(r"ACCEPTANCE\s+(\d+)/", out).group(1))
        killed = int(re.search(r"MUTANTS KILLED\s+(\d+)/", out).group(1))
        fa = int(re.search(r"FALSE ALARMS\s+(\d+) of", out).group(1))
        secs = float(re.search(r"score took ([\d.]+) s", out).group(1))
        suite = float(re.search(r"SUITE RUNTIME\s+([\d.]+) s", out).group(1))
        timings.append(secs)
        print("    acceptance %d/12, killed %d/16, false alarms %d, suite %.2f s, score %.1f s"
              % (acc, killed, fa, suite, secs))
        return acc, killed, fa, suite, out


def build(args):
    section("Build")
    cmd = [PY, os.path.join(TOP, "tools", "build.py"), "tdd-ladder",
           "--master-passphrase-file", args.master_passphrase_file, "--out", args.dist, "--keep-venv"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    check(proc.returncode == 0, "tools/build.py tdd-ladder", proc.stderr[-500:])
    print(proc.stdout.strip())


def level0(repo):
    section("Level 0: just build it")
    check(repo.level() == 0, "starts at level 0")
    check(repo.git("tag", "-l", "start") == "start", "tag start exists")
    check(repo.git("status", "--porcelain") == "", "clean working tree")
    code, out = repo.gate("unlock")
    check(code == 1 and "no score recorded" in out, "unlock refused before a score")
    repo.install_sample("l0_naive")
    repo.run(["make", "plot"])
    check(os.path.exists(os.path.join(repo.root, "results", "hz_binned.png")), "make plot wrote the PNG")
    check(os.path.exists(os.path.join(repo.root, "results", "hz_binned_L0.png")),
          "make plot also kept results/hz_binned_L0.png")
    acc, killed, fa, _, _ = repo.score()
    check(4 <= acc <= 9, "L0 acceptance in band 4-9", str(acc))
    check(killed <= 6, "L0 kills <= 6", str(killed))
    code, out = repo.gate("unlock", answers=[("acceptance tests passed?", str(acc + 1))])
    check(code == 1 and "Not quite" in out, "wrong acceptance count rejected")
    code, out = repo.gate("unlock", answers=[("acceptance tests passed?", str(acc)),
                                             ("nobody asked you about.", "edges; empty bins")])
    check(code == 0 and "Level 1 unlocked" in out, "L0 -> L1 unlock", out[-300:])
    check("Level 1 starts from the stub" in out and "attempt-L1-" in out,
          "unlock says it started a fresh attempt (automatic new-attempt)")
    check(os.path.exists(os.path.join(repo.root, "BRIEF.md")), "BRIEF.md written")
    with open(os.path.join(repo.root, "LOG.md")) as fh:
        check("edges; empty bins" in fh.read(), "reflection logged to LOG.md")


def level1(repo):
    section("Level 1: use TDD, please")
    check(repo.is_stub(), "binning.py already restored to the stub by the L0 unlock")
    check(sorted(os.listdir(os.path.join(repo.root, "tests"))) == ["__init__.py"], "tests/ already emptied")
    check("attempt-L1-" in repo.git("branch", "--list", "attempt-L1-*"), "attempt branch exists")
    branch = repo.git("branch", "--list", "attempt-L1-*", "--format=%(refname:short)").split()[0]
    check("NotImplementedError" not in repo.git("show", branch + ":src/hzbin/binning.py"),
          "Level 0 work is saved on the attempt branch")
    code, out = repo.gate("unlock")
    check(code == 1 and "no score recorded since the fresh attempt" in out,
          "unlock refused before a score at Level 1")
    code, out = repo.tdd("new-attempt")
    check(code == 0 and "attempt-L1-" in out, "./tdd new-attempt still works as a manual restart", out[-300:])
    check(repo.is_stub(), "binning.py is the stub after the manual restart")
    # Claude-style: tests and code land together; first run is green.
    repo.install_sample("l1_tests_after")
    repo.run([os.path.join(repo.root, "tdd"), "test"], ok_codes=(0, 1))
    # Level 1 work is left uncommitted, as a literal-persona group would leave it.
    repo.run(["make", "plot"])
    check(os.path.exists(os.path.join(repo.root, "results", "hz_binned_L1.png"))
          and os.path.exists(os.path.join(repo.root, "results", "hz_binned_L0.png")),
          "make plot at Level 1 kept both hz_binned_L0.png and hz_binned_L1.png")
    runs = [json.loads(line) for line in open(os.path.join(repo.root, ".tdd", "runs.jsonl"))]
    newest = runs[-1]
    failed = [n for n, t in newest["tests"].items() if t["outcome"] != "passed"]
    check(newest["phase"] == "none" and not failed, "run log shows first run all green (red never observed)")
    acc, killed, fa, _, _ = repo.score()
    check(6 <= acc <= 10, "L1 acceptance in band 6-10", str(acc))
    check(killed <= 8, "L1 kills <= 8", str(killed))
    code, out = repo.gate("unlock", answers=[("(y/n)", "n"), ("independent reference.", "c")])
    check(code == 0 and "Level 2 unlocked" in out, "L1 -> L2 unlock", out[-300:])


def level2(repo):
    section("Level 2: decide before you test")
    code, out = repo.gate("unlock")
    check(code == 1 and "SPEC.md does not exist" in out, "unlock refused without SPEC.md")
    with open(os.path.join(repo.root, "SPEC.md"), "w") as fh:
        fh.write("# Spec\n\n1. one\n2. two\n3. three\n")
    code, out = repo.gate("unlock")
    check(code == 1 and "at least 6" in out, "unlock refused with 3 decisions")
    shutil.copy(os.path.join(SAMPLES, "l2", "SPEC.md"), os.path.join(repo.root, "SPEC.md"))
    with open(os.path.join(repo.root, "src", "hzbin", "binning.py"), "a") as fh:
        fh.write("\n# sneaky edit\n")
    code, out = repo.gate("unlock")
    check(code == 1 and "changed during Level 2" in out, "unlock refused after a src edit")
    flat = out.replace("\r\n", " ").replace("\n", " ")
    level2_commit = repo.state()["records"]["tdd"]["tree_hash"].get("level2_commit")
    check(bool(level2_commit) and not repo.is_stub(), "Level 2 snapshot is a commit holding the Level 1 work")
    advice = "To fix: restore with git checkout %s -- src/hzbin/binning.py" % level2_commit[:10]
    check(advice in flat, "refusal names the Level 2 commit, the changed file and how to restore it", flat[-300:])
    repo.git("checkout", level2_commit[:10], "--", "src/hzbin/binning.py")
    check(repo.git("diff", level2_commit, "--", "src", "tests") == "",
          "following the advice restores src/ and tests/ to the Level 2 snapshot")
    check(not repo.is_stub(), "restored binning.py is the Level 1 code, not the stub")
    with open(os.path.join(repo.root, "tests", "test_stray.py"), "w") as fh:
        fh.write("def test_x():\n    pass\n")
    code, out = repo.gate("unlock")
    check(code == 1 and "delete the new file(s): tests/test_stray.py" in out.replace("\r\n", " ").replace("\n", " "),
          "refusal names a stray new file")
    os.unlink(os.path.join(repo.root, "tests", "test_stray.py"))
    code, out = repo.gate("unlock", answers=[("(0-10)", "6")])
    check(code == 0 and "Level 3 unlocked" in out, "L2 -> L3 unlock", out[-400:])
    check("CLIENT_SPEC.md is now in the repo" in out, "pre-reflection note shown before the question")
    check(os.path.exists(os.path.join(repo.root, "CLIENT_SPEC.md")), "CLIENT_SPEC.md visible")
    check(repo.is_stub() and sorted(os.listdir(os.path.join(repo.root, "tests"))) == ["__init__.py"],
          "Level 3 starts from the stub (automatic new-attempt)")
    check("starts from the stub" in out, "unlock says the stub was restored")


def run_cycle(repo, n):
    cyc = os.path.join(SAMPLES, "l3_cycles", "cycle%d" % n)
    behaviour = open(os.path.join(cyc, "behaviour.txt")).read().strip()
    code, out = repo.tdd("red", behaviour)
    check(code == 0 and repo.phase() == "red", "cycle %d: red opened" % n, out[-300:])
    shutil.copy(os.path.join(cyc, "tests", "test_cycle%d.py" % n),
                os.path.join(repo.root, "tests", "test_cycle%d.py" % n))
    code, out = repo.tdd("green")
    check(code == 1 and "uncommitted" in out, "cycle %d: green refuses uncommitted test" % n)
    repo.commit_all("cycle %d: test" % n)
    code, out = repo.tdd("green")
    check(code == 0 and repo.phase() == "green", "cycle %d: green (red seen for the right reason)" % n, out[-300:])
    shutil.copy(os.path.join(cyc, "binning.py"), os.path.join(repo.root, "src", "hzbin", "binning.py"))
    code, out = repo.tdd("done")
    check(code == 1 and "uncommitted" in out, "cycle %d: done refuses uncommitted code" % n)
    repo.commit_all("cycle %d: green" % n)
    code, out = repo.tdd("done")
    check(code == 0 and repo.phase() == "none", "cycle %d: done" % n, out[-300:])


def level3(repo):
    section("Level 3: red, green, refactor")
    decision, reason = repo.guard("Write", file_path="tests/test_a.py", content="x")
    check(decision == "deny" and "./tdd red" in reason, "guard: tests/ frozen in phase none")
    code, out = repo.tdd("green")
    check(code == 1 and "follows red" in out, "green refused before red")
    # Red for the wrong reason: ImportError.
    code, out = repo.tdd("red", "a test that cannot even import")
    check(code == 0, "red opened for the bad-import check")
    shutil.copy(os.path.join(SAMPLES, "l3_cycles", "bad_import", "tests", "test_bad_import.py"),
                os.path.join(repo.root, "tests", "test_bad_import.py"))
    repo.commit_all("bad import test")
    code, out = repo.tdd("green")
    check(code == 1 and "ImportError" in out and "wrong reason" in out, "green refuses an ImportError red")
    os.unlink(os.path.join(repo.root, "tests", "test_bad_import.py"))
    repo.commit_all("remove bad import test")
    # Now a real cycle with the guard and backstop checks in the middle.
    cyc = os.path.join(SAMPLES, "l3_cycles", "cycle1")
    shutil.copy(os.path.join(cyc, "tests", "test_cycle1.py"), os.path.join(repo.root, "tests", "test_cycle1.py"))
    repo.commit_all("cycle 1: test")
    code, out = repo.tdd("green")
    check(code == 0 and repo.phase() == "green", "cycle 1: green", out[-300:])
    decision, reason = repo.guard("Edit", file_path="tests/test_cycle1.py", old_string="a", new_string="b")
    check(decision == "deny" and "frozen in GREEN" in reason, "guard blocks a tests/ edit in green")
    decision, reason = repo.guard("Bash", command="echo 'x' >> tests/test_cycle1.py")
    check(decision == "deny", "guard blocks a Bash edit of tests/ in green")
    decision, _ = repo.guard("Edit", file_path="src/hzbin/binning.py", old_string="a", new_string="b")
    check(decision is None, "guard allows a src/ edit in green")
    with open(os.path.join(repo.root, "tests", "test_cycle1.py"), "a") as fh:
        fh.write("\n# edited behind the guard's back\n")
    code, out = repo.tdd("refactor")
    check(code == 1 and "changed since GREEN" in out, "refactor refuses after a Bash edit to tests/")
    repo.git("checkout", "--", "tests")
    shutil.copy(os.path.join(cyc, "binning.py"), os.path.join(repo.root, "src", "hzbin", "binning.py"))
    repo.commit_all("cycle 1: green")
    code, out = repo.tdd("refactor")
    check(code == 0 and repo.phase() == "refactor", "cycle 1: refactor", out[-300:])
    code, out = repo.tdd("done")
    check(code == 0 and repo.phase() == "none", "cycle 1: done")
    for n in (2, 3, 4, 5):
        run_cycle(repo, n)
    # A test that passes straight away: green refuses, abort closes without credit.
    code, out = repo.tdd("red", "a behaviour that already works")
    check(code == 0, "red opened for the already-passing case")
    with open(os.path.join(repo.root, "tests", "test_already.py"), "w") as fh:
        fh.write("from hzbin.binning import binned_weighted_mean\n\n\n"
                 "def test_single_point():\n"
                 "    assert list(binned_weighted_mean([0.5], [2.0], [1.0], [0.0, 1.0]).mean) == [2.0]\n")
    repo.commit_all("already passing test")
    code, out = repo.tdd("green")
    check(code == 1 and "nothing fails" in out and "abort" in out, "green refuses when nothing fails, suggests abort")
    code, out = repo.tdd("abort", "already satisfied", answers=[("Keep the test", "y")])
    check(code == 0 and repo.phase() == "none", "abort closes the cycle, test kept")
    check(os.path.exists(os.path.join(repo.root, "tests", "test_already.py")), "kept test still present")
    # Wrong oracle discovered in GREEN: abort without keeping restores tests/ so RED can restart.
    code, out = repo.tdd("red", "a behaviour with a wrong oracle")
    check(code == 0, "red opened for the wrong-oracle case")
    with open(os.path.join(repo.root, "tests", "test_wrong.py"), "w") as fh:
        fh.write("from hzbin.binning import binned_weighted_mean\n\n\n"
                 "def test_wrong_value():\n"
                 "    assert list(binned_weighted_mean([0.5], [2.0], [1.0], [0.0, 1.0]).mean) == [3.0]\n")
    repo.commit_all("wrong oracle test")
    code, out = repo.tdd("green")
    check(code == 0 and repo.phase() == "green", "green accepted the wrong-oracle test")
    code, out = repo.tdd("red", "another")
    check(code == 1 and "already open" in out, "red refused while a cycle is open")
    code, out = repo.tdd("abort", "wrong oracle", answers=[("Keep the test", "n")])
    check(code == 0 and "restored" in out and not os.path.exists(os.path.join(repo.root, "tests", "test_wrong.py")),
          "abort from GREEN restores tests/")
    check(repo.git("status", "--porcelain", "--", "tests") == "", "restore is committed")
    code, out = repo.tdd("red", "restart after abort")
    check(code == 0, "red restarts after the restore")
    code, out = repo.tdd("abort", "cleanup", answers=[("Keep the test", "y")])
    check(code == 0, "cleanup abort")
    # A failing suite at red entry shows which tests fail (not a masked exit code).
    with open(os.path.join(repo.root, "tests", "test_failing.py"), "w") as fh:
        fh.write("def test_fails():\n    assert 1 == 2\n")
    repo.commit_all("failing test")
    code, out = repo.tdd("red", "something")
    check(code == 1 and "test_fails" in out and "1 test(s) fail" in out, "red names the failing test")
    os.unlink(os.path.join(repo.root, "tests", "test_failing.py"))
    repo.commit_all("remove failing test")
    # A skipped test is refused at the next red.
    with open(os.path.join(repo.root, "tests", "test_skip.py"), "w") as fh:
        fh.write("import pytest\n\n\n@pytest.mark.skip\ndef test_skipped():\n    assert False\n")
    repo.commit_all("skipped test")
    code, out = repo.tdd("red", "something")
    check(code == 1 and "skipped" in out, "red refuses a skipped test")
    os.unlink(os.path.join(repo.root, "tests", "test_skip.py"))
    repo.commit_all("remove skipped test")
    cycles = [json.loads(line) for line in open(os.path.join(repo.root, ".tdd", "cycles.jsonl"))]
    check(sum(1 for c in cycles if c["valid"]) == 5, "5 valid cycles recorded")
    check(sum(1 for c in cycles if not c["valid"]) == 3, "aborted cycles recorded without credit")
    code, out = repo.gate("unlock")
    check(code == 1 and "no score" in out, "unlock refused without a score")
    # The group's finished Rung-4 suite.
    repo.install_sample(os.path.join("l3_cycles", "rung4"))
    with open(os.path.join(repo.root, "tests", "test_data_file.py"), "w") as fh:
        fh.write("from hzbin.data import load_hz\n\n\ndef test_data_loads():\n"
                 "    z, h, s = load_hz('data/hz_mock.csv')\n    assert len(z) == 40\n")
    repo.commit_all("rung 4 suite")
    acc, killed, fa, _, out = repo.score()
    check(killed >= 9 and fa == 0, "L3 score: >= 9 kills, 0 false alarms", "%d/%d" % (killed, fa))
    survivors = re.search(r"surviving mutants violate: (.*)", out).group(1)
    spec_ids = re.findall(r"S\d+", survivors)
    not_survivor = next(s for s in ("S3", "S4", "S5", "S1", "S6") if s not in spec_ids)
    code, out = repo.gate("unlock", answers=[("surviving mutant?", not_survivor)])
    check(code == 1 and "Not quite" in out, "wrong survivor spec rejected")
    code, out = repo.gate("unlock", answers=[("surviving mutant?", "none")])
    check(code == 1 and "Not quite" in out, "'none' rejected while mutants survive")
    code, out = repo.gate("unlock", answers=[("surviving mutant?", spec_ids[0].lower())])
    check(code == 0 and "Level 4 unlocked" in out, "L3 -> L4 unlock", out[-300:])


def level4(repo):
    section("Level 4: think like a physicist")
    repo.install_sample("l4_rung5")
    repo.commit_all("rung 5 suite")
    acc, killed, fa, suite, _ = repo.score()
    check(killed >= 14 and fa == 0 and suite < 10, "L4 score: >= 14 kills, 0 FA, < 10 s",
          "%d/%d/%.1f" % (killed, fa, suite))
    code, out = repo.gate("unlock", answers=[("coverage fraction?", "0.02")])
    check(code == 1 and "Not quite" in out, "wrong binomial sigma rejected")
    code, out = repo.gate("unlock", answers=[("coverage fraction?", "0.0093")])
    check(code == 0 and "Level 5 unlocked" in out, "L4 -> L5 unlock", out[-300:])


def level5(repo):
    section("Level 5: test the tests")
    code, out = repo.gate("unlock")
    check(code == 1 and "Mutation report" in out, "unlock refused without a mutation report")
    with open(os.path.join(repo.root, "LOG.md"), "a") as fh:
        fh.write("\n## Mutation report\n\nSix mutants, all killed.\n")
    code, out = repo.gate("unlock", answers=[("and why?", "test_x: duplicates test_y")])
    check(code == 0 and "Final level complete" in out, "L5 complete", out[-300:])
    check(repo.state()["complete"], "state marked complete")
    code, out = repo.tdd("ladder")
    check(code == 0 and out.count("\n") >= 5, "./tdd ladder lists the scores")
    print(out.strip())


def master_skip(repo, passfile):
    section("Master skip and reset")
    passphrase = open(passfile).read().strip()
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and repo.level() == 0, "./gate reset back to level 0")
    repo.git("reset", "-q", "--hard", "start")
    repo.git("clean", "-fdq", "--", "src", "tests")
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", "wrong-" + passphrase)])
    check(code == 1 and "not the master" in out, "wrong master passphrase rejected")
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", passphrase), ("Reason", "selftest")])
    check(code == 0 and repo.level() == 1, "master skip unlocks level 1", out[-300:])
    code, out = repo.gate("allow-model", "sonnet", answers=[("passphrase:", passphrase)])
    check(code == 0 and "sonnet" in repo.state()["allowed_models"], "allow-model power-up")
    # Leave the repo at the start for the facilitator.
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and "Removed unlocked files: BRIEF.md" in out, "reset removes unlocked briefs")
    repo.git("reset", "-q", "--hard", "start")
    repo.git("clean", "-fdq")
    for branch in repo.git("branch", "--list", "attempt-*").split():
        repo.git("branch", "-D", branch)
    check(repo.level() == 0 and repo.git("status", "--porcelain") == "", "repo left clean at level 0")


def verify_assets(repo):
    section("Hidden assets (reference, mutants, sample bands)")
    proc = subprocess.run([repo.venv, os.path.join(EXERCISE, "hidden", "verify_assets.py")],
                          cwd=EXERCISE, capture_output=True, text=True)
    tail = "\n".join(proc.stdout.strip().splitlines()[-3:])
    check(proc.returncode == 0, "hidden/verify_assets.py", proc.stdout[-800:] if proc.returncode else tail)


def preflight(repo):
    section("Preflight")
    code, out = repo.pty([os.path.join(repo.root, "preflight")], timeout=120)
    check(code == 0 and "Preflight passed" in out, "./preflight passes through a pty", out[-600:] if code else "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-passphrase-file", required=True)
    parser.add_argument("--dist", default=os.path.join(TOP, "dist", "tdd-ladder"))
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-assets", action="store_true")
    args = parser.parse_args()
    started = time.time()
    repo = Repo(os.path.abspath(args.dist), args.master_passphrase_file)
    try:
        if not args.skip_build:
            build(args)
        if not os.path.exists(repo.venv):
            raise Fail("no .venv in %s; run ./preflight --setup there first" % repo.root)
        preflight(repo)
        if not args.skip_assets:
            verify_assets(repo)
        level0(repo)
        level1(repo)
        level2(repo)
        level3(repo)
        level4(repo)
        level5(repo)
        master_skip(repo, args.master_passphrase_file)
    except Fail as exc:
        print("\nSELF-TEST FAILED: %s" % exc)
        return 1
    except ptyhelper.PtyTimeout as exc:
        print("\nSELF-TEST FAILED (pty timeout): %s" % exc)
        return 1
    print("\n=== Summary")
    print("%d checks passed" % len(checks))
    if timings:
        print("score runtimes: %s s (target < 20 s)" % ", ".join("%.1f" % t for t in timings))
    print("total wall time: %.0f s" % (time.time() - started))
    print("ALL SELF-TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
