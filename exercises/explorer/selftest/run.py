#!/usr/bin/env python3
"""Scripted walkthrough of dist/explorer (PLAN.md section 7).

usage: selftest/run.py --master-passphrase-file PATH [--dist DIR] [--skip-build]

Rebuilds the participant repo (keeping its .venv), runs preflight, then plays
every level as a group would, installing the reference solution from
selftest/solution/ step by step and committing as Claude would. Most of the
gate refusals named in PLAN.md sections 3.7, 4 and 5 are provoked once, mostly by
small uncommitted edits that are reverted afterwards. The guard is probed
with synthetic PreToolUse JSON at each level. A second pass after a reset
covers the dimuon dataset. Human-only commands (gate unlock, skip, reset) run
through a pty. Prints the measured timings; exit code 0 only when every
check passes. Leaves the repo clean at level 0 with its .venv kept.
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

SOLUTION = os.path.join(HERE, "solution")
SOLUTION_NAN = os.path.join(HERE, "solution_nan")
PY = sys.executable
EXPLORE_LIMIT_S = 5.0
L1_PROMPTS = {
    "pulsars": ("what is at that point?",
                "Hint: XX, YY and ZZ are Galactic coordinates"),
    "dimuons": ("which particle makes it?",
                "Hint: Each narrow band along M is a particle"),
}
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


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class Repo:
    def __init__(self, root):
        self.root = root
        self.venv = os.path.join(root, ".venv", "bin", "python")

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    # -- process helpers
    def run(self, argv, ok_codes=(0,), env=None, stdin_text=None):
        proc = subprocess.run(argv, cwd=self.root, capture_output=True, text=True,
                              input=stdin_text,
                              stdin=None if stdin_text is not None else subprocess.DEVNULL,
                              env=env)
        if ok_codes is not None and proc.returncode not in ok_codes:
            raise Fail("%s -> %d\n%s%s" % (" ".join(argv), proc.returncode,
                                            proc.stdout[-1500:], proc.stderr[-1500:]))
        return proc

    def git(self, *args):
        return self.run(["git", "-c", "commit.gpgsign=false"] + list(args)).stdout.strip()

    def commit(self, message, *paths):
        self.git("add", "-A", "--", *paths)
        self.git("commit", "-q", "-m", message)

    def make(self, *args):
        """make <args>; returns (exit code, stdout + stderr, seconds)."""
        started = time.time()
        proc = self.run(["make"] + list(args), ok_codes=None)
        return proc.returncode, proc.stdout + proc.stderr, time.time() - started

    def pty(self, argv, answers=(), timeout=180):
        return ptyhelper.run_pty([PY] + argv, answers, cwd=self.root, timeout=timeout)

    def gate(self, *args, answers=(), timeout=300):
        return self.pty([self.path("gate")] + list(args), answers, timeout)

    def gate_check(self):
        started = time.time()
        proc = self.run([PY, self.path("gate"), "check"], ok_codes=(0, 1))
        return proc.returncode, flat(proc.stdout + proc.stderr), time.time() - started

    def state(self):
        return st.load_state(self.root)

    def level(self):
        return self.state()["level"]

    def heads(self):
        return (self.state().get("records") or {}).get("heads") or {}

    # -- file helpers
    def write(self, rel, text):
        with open(self.path(rel), "w", encoding="utf-8") as fh:
            fh.write(text)

    def text(self, rel):
        return read(self.path(rel))

    def install(self, src, rel):
        """Copy a file or a directory's files (not __pycache__) to rel."""
        if os.path.isfile(src):
            shutil.copy(src, self.path(rel))
            return
        os.makedirs(self.path(rel), exist_ok=True)
        for name in sorted(os.listdir(src)):
            if not name.startswith("__pycache__") and os.path.isfile(os.path.join(src, name)):
                shutil.copy(os.path.join(src, name), self.path(rel, name))

    def append(self, rel, line):
        with open(self.path(rel), "a", encoding="utf-8") as fh:
            fh.write(line)

    def revert(self, *paths):
        self.git("checkout", "-q", "--", *paths)

    # -- guard probe
    def guard(self, rel):
        """Decision of .claude/hooks/guard.py for an Edit of rel: 'deny' or None."""
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
                   "tool_input": {"file_path": self.path(rel), "old_string": "a",
                                  "new_string": "b"},
                   "session_id": "selftest", "cwd": self.root}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        proc = self.run(["python3", self.path(".claude", "hooks", "guard.py")],
                        env=env, stdin_text=json.dumps(payload))
        if not proc.stdout.strip():
            return None
        out = json.loads(proc.stdout.strip().splitlines()[-1])
        return out.get("hookSpecificOutput", {}).get("permissionDecision")


def refused(repo, expected, label):
    """gate check fails and its sentence contains `expected`."""
    code, out, _ = repo.gate_check()
    check(code == 1 and expected in out, "refused: %s" % label, out if expected not in out else "")


def passes(repo, label):
    code, out, seconds = repo.gate_check()
    check(code == 0 and "PASS" in out, "gate check passes: %s (%.1f s)" % (label, seconds), out)
    return seconds


def mutation(repo, rel, old, new, expected, label):
    """Edit rel without committing, expect a refusal, then revert."""
    text = repo.text(rel)
    if old not in text:
        raise Fail("mutation '%s': %r not found in %s" % (label, old, rel))
    repo.write(rel, text.replace(old, new, 1))
    try:
        refused(repo, expected, label)
    finally:
        repo.revert(rel)


def guard_probe(repo, denied, allowed):
    level = repo.level()
    for rel in denied:
        check(repo.guard(rel) == "deny", "guard at level %d refuses an Edit to %s" % (level, rel))
    for rel in allowed:
        check(repo.guard(rel) is None, "guard at level %d allows an Edit to %s" % (level, rel))


def brief_ok(repo):
    text = repo.text("BRIEF.md")
    check("commit, then `./gate unlock`" in text, "BRIEF.md ends with 'commit, then ./gate unlock'")


def logged(repo, answer):
    check("A: %s" % answer in repo.text("LOG.md"), "reflection logged to LOG.md")


def plan_variant(text, which):
    """A copy of a sample PLAN.md with one completeness rule broken."""
    lines = text.splitlines(keepends=True)
    if which == "decision":
        return re.sub(r"(?m)^(- Missing values in a selected column:).*$", r"\1", text)
    if which == "dataset":
        return re.sub(r"(?m)^Dataset: (\S+)$", r"Dataset: `\1`", text)
    if which == "manysteps":
        return text.replace("## Acceptance", "3. A third step.\n\n## Acceptance", 1)
    heading = {"criteria": "## Acceptance criteria", "steps": "## Steps"}[which]
    keep = {"criteria": 2, "steps": 1}[which]
    out, inside, seen = [], False, 0
    for line in lines:
        if line.startswith("## "):
            inside = line.startswith(heading)
        elif inside and re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", line):
            seen += 1
            if seen > keep:
                continue
        out.append(line)
    return "".join(out)


# ------------------------------------------------------------------ steps

def build(args):
    section("1. Build and preflight")
    cmd = [PY, os.path.join(TOP, "tools", "build.py"), "explorer",
           "--master-passphrase-file", args.master_passphrase_file, "--out", args.dist,
           "--keep-venv"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    check(proc.returncode == 0, "tools/build.py explorer", proc.stderr[-500:])
    print(proc.stdout.strip())


def preflight(repo):
    code, out = repo.pty([repo.path("preflight")], timeout=300)
    check(code == 0 and "Preflight passed" in out, "./preflight passes through a pty",
          out[-600:] if code else "")
    for rel in ("README.md", "AGENTS.md", "CLAUDE.md", "OTHER-AGENTS.md",
                "PLAN.md", "PLAYBOOK.md", "LOG.md", "Makefile",
                "requirements.txt", "data/pulsars.csv", "data/dimuons.csv",
                "explorer/__init__.py", "tests/__init__.py", ".claude/agents/reviewer.md",
                ".claude/skills/plan-code/SKILL.md",
                ".claude/skills/review-code/SKILL.md",
                ".claude/skills/style-code/SKILL.md",
                ".claude/skills/test-code/SKILL.md",
                ".gatekit/exploretool/checks/level3.py"):
        check(os.path.isfile(repo.path(rel)), "%s shipped" % rel)
    for rel in ("BRIEF.md", "TESTS.md", "REVIEW.md", "explorer/__main__.py", "answers.json"):
        check(not os.path.exists(repo.path(rel)), "%s not shipped at level 0" % rel)
    check(repo.git("status", "--porcelain") == "" and repo.level() == 0,
          "fresh build: clean tree at level 0")


def level0(repo, plan_name):
    section("Level 0: plan (%s)" % plan_name)
    check(repo.level() == 0, "at level 0")
    guard_probe(repo, denied=("explorer/data.py", "tests/test_x.py", "PLAYBOOK.md", "README.md"),
                allowed=("PLAN.md", "LOG.md"))
    refused(repo, "PLAN.md is still the template", "template PLAN.md")
    sample = read(os.path.join(SOLUTION, plan_name))
    for which, expected in (
            ("decision", 'decision "Missing values in a selected column" is blank'),
            ("dataset", "it must be exactly data/pulsars.csv or data/dimuons.csv"),
            ("criteria", "PLAN.md lists 2 acceptance criteria; it needs at least 3"),
            ("steps", "PLAN.md lists 1 step; it needs two, each ending in something you can "
                      "run and look at"),
            ("manysteps", "PLAN.md lists 3 steps; merge them into two, each ending in "
                          "something you can run and look at")):
        repo.write("PLAN.md", plan_variant(sample, which))
        refused(repo, expected, "PLAN.md with %s broken" % which)
    # A "#" comment inside a code fence under Steps is not a heading.
    fenced = re.sub(r"(?m)^(## Steps.*)$",
                    r"\1\n```bash\n# generate data.json\nmake explore\n```", sample, count=1)
    repo.write("PLAN.md", fenced)
    refused(repo, "no commit since start", "PLAN.md with a fenced # comment under Steps")
    repo.write("PLAN.md", sample)
    refused(repo, "no commit since start", "complete PLAN.md not committed")
    repo.commit("Plan", "PLAN.md")
    repo.append("PLAN.md", "\nA stray line.\n")
    refused(repo, "PLAN.md has uncommitted changes: ask the agent to commit, then unlock",
            "PLAN.md edited after the commit")
    repo.revert("PLAN.md")
    passes(repo, "level 0")
    head = repo.git("rev-parse", "HEAD")
    answer = "we made the log-axis rule explicit"
    code, out = repo.gate("unlock", answers=[("and why:", answer)])
    check(code == 0 and "Level 1 unlocked" in out and repo.level() == 1,
          "level 0 unlock opens level 1", flat(out)[-300:])
    check(repo.heads().get("1") == head, "records.heads['1'] is the PLAN.md commit")
    check(os.path.isfile(repo.path("BRIEF.md")), "BRIEF.md present at level 1")
    brief_ok(repo)
    logged(repo, answer)


def install_solution(repo, nan=False):
    repo.install(os.path.join(SOLUTION, "explorer"), "explorer")
    if nan:
        repo.install(os.path.join(SOLUTION_NAN, "explorer", "__main__.py"),
                     os.path.join("explorer", "__main__.py"))


def time_explore(repo, label, *args):
    code, out, seconds = repo.make("explore", *args)
    check(code == 0 and seconds < EXPLORE_LIMIT_S,
          "make explore %s in %.2f s (limit %.0f s)" % (label, seconds, EXPLORE_LIMIT_S),
          out[-400:] if code else "")
    timings.append(("make explore, %s" % label, "%.2f s" % seconds))
    return out


def level1_pulsars(repo):
    section("Level 1: build (pulsars)")
    guard_probe(repo, denied=("tests/test_x.py", "PLAYBOOK.md", "Makefile", "data/pulsars.csv"),
                allowed=("explorer/data.py", "PLAN.md"))
    refused(repo, "there is no explorer/__main__.py yet: ask the agent to add the command line",
            "no __main__.py")
    install_solution(repo, nan=True)
    repo.commit("Step 1 (writes NaN)", "explorer")
    refused(repo, "data.json is not valid JSON (NaN is not JSON; write it with allow_nan=False)",
            "NaN in data.json")
    nan_main = read(os.path.join(SOLUTION_NAN, "explorer", "__main__.py"))
    check('float("nan")' in nan_main, "solution_nan writes float('nan')")
    install_solution(repo)
    refused(repo, "1 commit since the last gate; this level needs at least 2: ask the agent to "
            "commit each step that works (two commits or more)", "1 commit")
    repo.commit("Step 1: strict JSON", "explorer")
    repo.install(os.path.join(SOLUTION_NAN, "explorer", "__main__.py"),
                 os.path.join("explorer", "__main__.py"))
    mutation(repo, "explorer/__main__.py", 'float("nan")', 'float("inf")',
             "data.json is not valid JSON (Infinity is not JSON", "Infinity in data.json")
    for rel, old, new, expected, label in (
            ("explorer/page.py", '<select id="colour">', '<select id="color">',
             'explorer.html has no <select id="colour">', "no colour select"),
            ("explorer/page.py", '<select id="x">__COLUMN_OPTIONS__</select>',
             '<select id="x"></select>',
             '<select id="x"> has no <option value="GL">', "x select without options"),
            ("explorer/page.py", "'scattergl'", "'scatter'",
             "never mentions scattergl outside plotly.js itself", "2D without WebGL"),
            ("explorer/page.py", '"__PLOTLY__": get_plotlyjs(),',
             '"__PLOTLY__": "</script><script src=\\"https://cdn.plot.ly/plotly-3.0.0.min.js\\">",',
             "explorer.html loads a script from the internet", "plotly.js from a CDN"),
            ("explorer/data.py", "if table.n_rows <= max_points:", "if True:",
             "--max-points 500 wrote 4503 rows on data/pulsars.csv; it must write exactly 500",
             "no sampling"),
            ("explorer/__main__.py", "except (ExplorerError, OSError, ValueError) as err:",
             "except ZeroDivisionError as err:",
             "the run on a file that does not exist printed a Python traceback",
             "traceback on a missing file"),
            ("explorer/__main__.py", "for name in list(table.rows) + list(table.labels):",
             "for name in list(table.rows):",
             "the --list run on data/pulsars.csv does not print column JNAME",
             "--list without the label column")):
        mutation(repo, rel, old, new, expected, label)
    check(repo.git("status", "--porcelain", "--", "explorer") == "",
          "explorer/ back to the committed solution")
    repo.append("explorer/data.py", "# step 2 checked in the browser\n")
    repo.commit("Step 2", "explorer")
    repo.append("explorer/page.py", "# step 2, second look in the browser\n")
    repo.commit("Step 2: initial view", "explorer")
    repo.append("explorer/data.py", "# work in progress\n")
    refused(repo, "explorer/ has uncommitted changes: ask the agent to commit, then unlock",
            "uncommitted edit to explorer/data.py")
    repo.commit("Step 2: hover fix", "explorer")
    out = time_explore(repo, "data/pulsars.csv (PLAN.md)")
    check("n_read=4503 n_written=4503" in out, "make explore prints n_read and n_written")
    check(os.path.isfile(repo.path("out", "explorer.html"))
          and os.path.isfile(repo.path("out", "data.json")), "out/explorer.html and data.json")
    time_explore(repo, "data/dimuons.csv (DATA=)", "DATA=data/dimuons.csv")
    code, out, _ = repo.make("list")
    check(code == 0 and all(c in out for c in ("JNAME", "P0", "EDOT", "missing")),
          "make list prints the columns and missing counts")
    status = repo.run(["git", "status", "--porcelain"]).stdout.splitlines()
    check(not any(line[3:].startswith("out") for line in status), "out/ is ignored by git")
    timings.append(("gate check, level 1", "%.1f s" % passes(repo, "level 1")))
    prompt, hint = L1_PROMPTS["pulsars"]
    code, out = repo.gate("unlock", answers=[(prompt, "the moon")])
    check(code == 1 and "Not quite" in out and hint in flat(out) and repo.level() == 1,
          "wrong answer 'the moon' is rejected with the pulsar hint", flat(out)[-300:])
    check(repo.state()["levels"]["1"]["failed_attempts"] == 1, "failed attempt counted")
    head = repo.git("rev-parse", "HEAD")
    answer = "a slider for the colour range"
    code, out = repo.gate("unlock", answers=[(prompt, "The Sun"), ("would add:", answer)])
    check(code == 0 and "Level 2 unlocked" in out and repo.level() == 2,
          "'The Sun' opens level 2", flat(out)[-300:])
    check("TESTS.md" in out and os.path.isfile(repo.path("TESTS.md")), "TESTS.md arrived")
    check(repo.heads().get("2") == head, "records.heads['2'] recorded")
    brief_ok(repo)
    logged(repo, answer)


def level2(repo):
    section("Level 2: test")
    guard_probe(repo, denied=("PLAN.md", "PLAYBOOK.md"),
                allowed=("tests/test_x.py", "TESTS.md", "explorer/data.py"))
    refused(repo, 'TESTS.md has 0 items under "Our list"', "template TESTS.md")
    template = repo.text("TESTS.md")
    repo.write("TESTS.md", template.replace("-\n-\n-\n", "- a\n- b\n- c\n"))
    refused(repo, "TESTS.md has nothing under \"The agent's plan\" yet",
            "the agent's plan not written")
    repo.install(os.path.join(SOLUTION, "TESTS.md"), "TESTS.md")
    repo.install(os.path.join(SOLUTION, "tests_four", "test_explorer.py"),
                 os.path.join("tests", "test_explorer.py"))
    refused(repo, "pytest collected 4 tests; this level needs at least 5", "four tests")
    repo.install(os.path.join(SOLUTION, "tests"), "tests")
    repo.write("tests/test_zz_fails.py", "def test_fails():\n    assert 1 == 2\n")
    refused(repo, "make test: 1 of 16 tests fail: fix the code, not the tests",
            "a failing test")
    repo.write("tests/test_zz_fails.py", "def test_broken(:\n    pass\n")
    refused(repo, "make test could not collect or run the tests", "a collection error")
    os.remove(repo.path("tests", "test_zz_fails.py"))
    full = repo.text("tests/test_explorer.py")
    repo.write("tests/test_explorer.py", "".join(
        "def test_%d():\n    assert True\n\n\n" % i for i in range(5)))
    refused(repo, "no test module under tests/ imports explorer", "tests without explorer")
    repo.write("tests/test_explorer.py", full)
    refused(repo, "no commits since the last gate; this level needs at least 1: ask the agent to "
            "commit the tests and TESTS.md", "tests not committed")
    repo.commit("Tests", "tests", "TESTS.md")
    code, out, seconds = repo.make("test")
    match = re.search(r"(\d+) passed", out)
    check(code == 0 and match and int(match.group(1)) == 15,
          "make test: %s in %.1f s" % (match.group(0) if match else "?", seconds), out[-300:])
    timings.append(("make test (15 tests)", "%.1f s" % seconds))
    code, out, _ = repo.make("coverage")
    total = re.search(r"^TOTAL\s.*?(\d+%)\s*$", out, re.M)
    check(code == 0 and total is not None, "make coverage reports a total (%s)"
          % (total.group(1) if total else "?"), out[-300:])
    timings.append(("coverage of explorer/", total.group(1)))
    check(repo.git("status", "--porcelain", "--", "tests", "TESTS.md", "explorer") == "",
          "make test and make coverage leave the checked paths clean")
    repo.append("tests/test_explorer.py", "# more to come\n")
    refused(repo, "tests/ has uncommitted changes", "uncommitted edit to tests/")
    repo.revert("tests/test_explorer.py")
    passes(repo, "level 2")
    answer = "Claude tested the seed; we had not thought of it"
    code, out = repo.gate("unlock", answers=[("or the reverse?", answer)])
    check(code == 0 and "Level 3 unlocked" in out and os.path.isfile(repo.path("REVIEW.md")),
          "level 2 unlock opens level 3 with REVIEW.md", flat(out)[-300:])
    check("3" in repo.heads(), "records.heads['3'] recorded")
    brief_ok(repo)
    logged(repo, answer)


def level3(repo):
    section("Level 3: review")
    guard_probe(repo, denied=("PLAN.md", "TESTS.md", "PLAYBOOK.md"),
                allowed=("REVIEW.md", "tests/test_x.py", "explorer/page.py"))
    refused(repo, 'REVIEW.md has 0 guesses under "Our guesses"', "template REVIEW.md")
    sample = read(os.path.join(SOLUTION, "REVIEW.md"))
    repo.write("REVIEW.md", sample.replace("| ACCEPT |", "| LATER |"))
    refused(repo, "REVIEW.md has 2 triaged findings; this level needs at least 3",
            "two findings triaged")
    repo.write("REVIEW.md", sample)
    refused(repo, "no commits since the last gate; this level needs at least 1: ask the agent to "
            "commit each fix and REVIEW.md", "REVIEW.md not committed")
    repo.commit("Review triaged", "REVIEW.md")
    for sidecar, dataset in (("data/pulsars.columns.json", "data/pulsars.csv"),
                             ("data/dimuons.columns.json", "data/dimuons.csv")):
        meta = json.loads(repo.text(sidecar))
        meta["columns"]["FAKE"] = {"numeric": True, "unit": "", "description": "", "log": False}
        repo.write(sidecar, json.dumps(meta))
        try:
            if dataset == "data/pulsars.csv":
                refused(repo, "the default run on data/pulsars.csv: data.json has no column FAKE",
                        "level 3 runs the tool again on the group's dataset")
            else:
                passes(repo, "level 3 ignores the other dataset")
        finally:
            repo.revert(sidecar)
    seconds = passes(repo, "level 3 (pytest and the group's dataset)")
    timings.append(("gate check, level 3", "%.1f s" % seconds))
    answer = "the duplicate header bug"
    code, out = repo.gate("unlock", answers=[("tests didn't?", answer)])
    check(code == 0 and "Final level complete" in out and repo.state()["complete"],
          "level 3 unlock completes the exercise", flat(out)[-300:])
    check("PLAYBOOK.md is yours to take home" in out, "completion note points at PLAYBOOK.md")
    logged(repo, answer)


def reset(repo):
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and repo.level() == 0, "./gate reset back to level 0", flat(out)[-200:])
    for rel in ("BRIEF.md", "TESTS.md", "REVIEW.md", "out"):
        check(not os.path.exists(repo.path(rel)), "reset removed %s" % rel)
    repo.git("reset", "-q", "--hard", "start")
    repo.git("clean", "-fdq")
    check(repo.git("status", "--porcelain") == "" and repo.heads() == {},
          "git reset --hard start: clean tree, no commit records")


def dimuons(repo):
    section("Dimuon pass: reset, level 0 and level 1 on data/dimuons.csv")
    reset(repo)
    repo.install(os.path.join(SOLUTION, "PLAN.dimuons.md"), "PLAN.md")
    repo.commit("Plan (dimuons)", "PLAN.md")
    passes(repo, "level 0 (dimuons)")
    code, out = repo.gate("unlock", answers=[("and why:", "chose log axes for M and pt1")])
    check(code == 0 and repo.level() == 1, "level 0 unlock (dimuons)", flat(out)[-200:])
    install_solution(repo)
    repo.commit("Step 1", "explorer")
    repo.append("explorer/data.py", "# step 2\n")
    repo.commit("Step 2", "explorer")
    repo.append("explorer/page.py", "# step 2, second look\n")
    repo.commit("Step 2: initial view", "explorer")
    out = time_explore(repo, "data/dimuons.csv (PLAN.md)")
    check("n_read=60000 n_written=20000" in out, "dimuons sampled to 20,000 of 60,000")
    with open(repo.path("out", "data.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    check(data["labels"] == {} and len(data["columns"]) == 17,
          "dimuons: 17 numeric columns, no labels")
    passes(repo, "level 1 (dimuons)")
    prompt, hint = L1_PROMPTS["dimuons"]
    code, out = repo.gate("unlock", answers=[(prompt, "the moon")])
    check(code == 1 and "Not quite" in out and hint in flat(out) and repo.level() == 1,
          "dimuons: a wrong answer is rejected with the dimuon hint", flat(out)[-300:])
    code, out = repo.gate("unlock", answers=[(prompt, "The J/ψ(1S) meson"), ("would add:", "a mass cut")])
    check(code == 0 and "Level 2 unlocked" in out and repo.level() == 2,
          "'The J/ψ(1S) meson' opens level 2 (contains)", flat(out)[-300:])


def finale(repo, passfile):
    section("Facilitator commands, skip and reset")
    with open(passfile) as fh:
        passphrase = fh.read().strip()
    reset(repo)
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", "wrong-" + passphrase)])
    check(code == 1 and "not the master" in out, "gate skip: wrong passphrase rejected")
    code, out = repo.gate("skip", "--master", answers=[("passphrase:", passphrase),
                                                       ("Reason", "selftest")])
    check(code == 0 and repo.level() == 1 and os.path.exists(repo.path("BRIEF.md")),
          "./gate skip --master at level 0 opens level 1", flat(out)[-300:])
    check(repo.heads().get("1") == repo.git("rev-parse", "HEAD"),
          "the skip also records HEAD for the commit count")
    code, out = repo.gate("reset", answers=[("level 0?", "y")])
    check(code == 0 and "Removed unlocked files: BRIEF.md" in out, "reset removes the brief")
    repo.git("reset", "-q", "--hard", "start")
    repo.git("clean", "-fdq")
    for rel in ("out", ".coverage", ".pytest_cache"):
        path = repo.path(rel)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    check(repo.level() == 0 and repo.git("status", "--porcelain") == ""
          and not os.path.exists(repo.path("explorer", "__main__.py"))
          and os.path.exists(repo.venv), "repo left clean at level 0 with its .venv")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-passphrase-file", required=True)
    parser.add_argument("--dist", default=os.path.join(TOP, "dist", "explorer"))
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    started = time.time()
    repo = Repo(os.path.abspath(args.dist))
    try:
        if not args.skip_build:
            build(args)
        if not os.path.exists(repo.venv):
            raise Fail("no .venv in %s; run ./preflight --setup there first" % repo.root)
        preflight(repo)
        level0(repo, "PLAN.pulsars.md")
        level1_pulsars(repo)
        level2(repo)
        level3(repo)
        dimuons(repo)
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
