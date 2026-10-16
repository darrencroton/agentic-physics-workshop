"""Phase transitions: red, green, refactor, done, new-attempt."""

import datetime
import os
import shutil

from gatekit import tty
from tddtool import common as C

MIN_LEVEL_FOR_PHASES = 3
RESTORE_HINT = (" A new cycle needs a green suite and the agent cannot edit src/ or "
                "tests/ with no cycle open. In the gate terminal, restore the last "
                "good version (git log --oneline, then git checkout <commit> -- "
                "src tests and git commit -m restore) or delete the offending "
                "test file with git rm and commit.")


def _say(text=""):
    print(text)


def _require_level(state, command):
    level = state.get("level", 0)
    if level < MIN_LEVEL_FOR_PHASES:
        raise C.TddError("./tdd %s is available from Level 3. You are at "
                         "Level %d." % (command, level))
    return level


def _all_pass(root, label):
    _say("Running the test suite (%s)..." % label)
    code, record, _ = C.run_pytest(root)
    if record is None:
        raise C.TddError("pytest ran but no run record appeared in "
                         ".tdd/runs.jsonl. Is pytest.ini intact?")
    passed, failed, skipped, errors = C.summarise_run(record)
    hint = RESTORE_HINT if label.startswith("entry check for RED") else ""
    if errors:
        raise C.TddError("the suite does not even collect: %s.%s"
                         % (", ".join("%s (%s)" % (e["nodeid"], e["exc_type"])
                                      for e in errors), hint))
    if failed:
        raise C.TddError("%d test(s) fail: %s.%s" % (
            len(failed), ", ".join(sorted(failed)), hint))
    if skipped:
        raise C.TddError("%d test(s) are skipped. Skips count as failures "
                         "here: %s.%s" % (len(skipped), ", ".join(skipped), hint))
    if code not in (0, 5):
        raise C.TddError("pytest exited with code %d; the run did not complete "
                         "cleanly." % code)
    return passed, record


def cmd_red(root, args):
    state = C.load_state(root)
    level = _require_level(state, "red")
    behaviour = " ".join(args).strip()
    if not behaviour:
        raise C.TddError('usage: ./tdd red "<one behaviour>"')
    phase = C.read_phase(root)
    if phase != "none":
        raise C.TddError("a cycle is already open (phase %s). Finish it "
                         "with ./tdd done first." % phase.upper())
    passed, record = _all_pass(root, "entry check for RED")
    cycle = {"behaviour": behaviour, "level": level, "red_started": C.now_iso(),
             "red_commit": C.git_head(root), "baseline_passing": passed,
             "src_hash": C.tree_hash(root, "src")}
    C.write_cycle(root, cycle)
    C.write_phase(root, "red")
    _say("")
    _say("Phase RED: %s" % behaviour)
    _say("The agent writes ONE test for this behaviour. The expected value comes "
         "from a human. Commit the test, then run ./tdd green.")
    return 0


def cmd_green(root, args):
    state = C.load_state(root)
    _require_level(state, "green")
    if C.read_phase(root) != "red":
        raise C.TddError("green follows red. Start a cycle with ./tdd red.")
    cycle = C.read_cycle(root) or {}
    if cycle.get("src_hash") and cycle["src_hash"] != C.tree_hash(root, "src"):
        raise C.TddError("src/ changed during RED. Only the test changes in "
                         "RED; restore src/ (git checkout %s -- src, then commit) "
                         "and try again." % cycle.get("red_commit", "HEAD")[:8])
    dirty = C.dirty_paths(root, "tests")
    if dirty:
        raise C.TddError("tests/ has uncommitted changes (%s). Commit the "
                         "new test first: git add tests && git commit"
                         % ", ".join(dirty))
    new_tests = C.diff_names(root, cycle.get("red_commit", "HEAD"), "tests")
    if not new_tests:
        raise C.TddError("no change to tests/ has been committed since RED "
                         "began. Write and commit the test first.")
    _say("Running the test suite (entry check for GREEN)...")
    code, record, _ = C.run_pytest(root)
    if record is None:
        raise C.TddError("pytest ran but no run record appeared.")
    passed, failed, skipped, errors = C.summarise_run(record)
    if errors:
        raise C.TddError("red for the wrong reason: the suite fails to "
                         "collect (%s). An import or syntax error proves "
                         "nothing about behaviour." % ", ".join(
                             "%s: %s" % (e["exc_type"], e["nodeid"])
                             for e in errors))
    if not failed:
        raise C.TddError("nothing fails. A test that has never failed might "
                         "not be able to fail. Check the test and try again, "
                         "or close this cycle with ./tdd abort if the behaviour "
                         "is already implemented (keep the test).")
    bad = {n: t["exc_type"] for n, t in failed.items()
           if t["exc_type"] not in C.GOOD_FAILURES}
    if bad:
        raise C.TddError("red for the wrong reason: %s. Only AssertionError "
                         "or NotImplementedError count." % ", ".join(
                             "%s raises %s" % (n, e) for n, e in bad.items()))
    baseline = set(cycle.get("baseline_passing", []))
    regressions = sorted(baseline - set(passed))
    if regressions:
        raise C.TddError("previously passing tests now fail, skip or are gone: "
                         "%s. The new test must not break old ones."
                         % ", ".join(regressions))
    cycle.update({"green_started": C.now_iso(), "green_commit": C.git_head(root),
                  "red_observed": True, "new_tests": new_tests,
                  "failure_types": sorted({t["exc_type"] for t in failed.values()}),
                  "failing_tests": sorted(failed)})
    C.write_cycle(root, cycle)
    C.write_phase(root, "green")
    _say("")
    _say("Red observed for the right reason: %s" % ", ".join(sorted(failed)))
    _say("Phase GREEN: tests/ is frozen. The agent writes the minimum code to "
         "pass. Then commit and run ./tdd refactor or ./tdd done.")
    return 0


def _tests_frozen_check(root, cycle):
    changed = C.tests_changed_since(root, cycle.get("green_commit", "HEAD"))
    if changed:
        raise C.TddError("tests/ changed since GREEN began (%s). Tests are "
                         "frozen. Restore them (git checkout %s -- tests) or "
                         "decide as a group to return to RED."
                         % (", ".join(changed), cycle.get("green_commit", "HEAD")[:8]))


def cmd_refactor(root, args):
    state = C.load_state(root)
    _require_level(state, "refactor")
    if C.read_phase(root) != "green":
        raise C.TddError("refactor follows green.")
    cycle = C.read_cycle(root) or {}
    _tests_frozen_check(root, cycle)
    _all_pass(root, "entry check for REFACTOR")
    cycle["refactor_started"] = C.now_iso()
    C.write_cycle(root, cycle)
    C.write_phase(root, "refactor")
    _say("")
    _say("Phase REFACTOR: tests/ stays frozen. Improve the code; run the "
         "tests often. Then commit and run ./tdd done.")
    return 0


def cmd_done(root, args):
    state = C.load_state(root)
    level = _require_level(state, "done")
    phase = C.read_phase(root)
    if phase not in ("green", "refactor"):
        raise C.TddError("done follows green or refactor.")
    cycle = C.read_cycle(root) or {}
    _tests_frozen_check(root, cycle)
    _all_pass(root, "exit check for DONE")
    dirty = C.dirty_paths(root, "src", "tests")
    if dirty:
        raise C.TddError("uncommitted changes in %s. Commit at green: "
                         "git add src tests && git commit" % ", ".join(dirty))
    cycle.update({"done": C.now_iso(), "done_commit": C.git_head(root),
                  "valid": bool(cycle.get("red_observed")), "level": level})
    C.append_jsonl(root, "cycles.jsonl", cycle)
    C.clear_cycle(root)
    C.write_phase(root, "none")
    count = len(C.valid_cycles(root, level))
    _say("")
    _say("Cycle closed: %s" % cycle.get("behaviour", "?"))
    _say("Valid cycles at this level: %d" % count)
    return 0


def cmd_abort(root, args):
    state = C.load_state(root)
    _require_level(state, "abort")
    phase = C.read_phase(root)
    if phase == "none":
        raise C.TddError("no cycle is open.")
    cycle = C.read_cycle(root) or {}
    reason = " ".join(args).strip() or "aborted by the group"
    red_commit = cycle.get("red_commit")
    keep = tty.confirm("Keep the test(s) written in this cycle? (No restores "
                       "tests/ to how it was when RED began)")
    restored = False
    if not keep and red_commit:
        tests_dir = os.path.join(root, "tests")
        shutil.rmtree(tests_dir, ignore_errors=True)
        C.git(root, "checkout", red_commit, "--", "tests")
        C.git(root, "add", "-A", "--", "tests")
        if C.dirty_paths(root, "tests"):
            C.git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m",
                  "Abort cycle: restore tests (%s)" % reason, "--", "tests")
        restored = True
    cycle.update({"aborted": C.now_iso(), "abort_reason": reason, "valid": False,
                  "tests_restored": restored, "level": state.get("level", 0)})
    C.append_jsonl(root, "cycles.jsonl", cycle)
    C.clear_cycle(root)
    C.write_phase(root, "none")
    _say("Cycle closed without credit (%s)." % reason)
    if restored:
        _say("tests/ restored to the state at RED (%s). Start again with "
             "./tdd red." % red_commit[:8])
    else:
        _say("Tests kept. The next ./tdd red needs every test passing; if one "
             "still fails, restore with git checkout %s -- tests and commit."
             % (red_commit or "HEAD")[:8])
    return 0


def new_attempt(root, state, reason):
    """Branch off the current work and restore the stub and empty tests."""
    level = state.get("level", 0)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")  # noqa: DTZ005
    branch = "attempt-L%d-%s" % (level, stamp)
    if C.dirty_paths(root, "."):
        C.git(root, "add", "-A")
        C.git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m",
              "Work in progress before %s" % reason)
    C.git(root, "branch", "-f", branch, "HEAD")
    tests_dir = os.path.join(root, "tests")
    shutil.rmtree(tests_dir, ignore_errors=True)
    C.git(root, "checkout", "start", "--", *C.STUB_FILES)
    C.git(root, "add", "-A", "--", *C.STUB_FILES)
    if C.dirty_paths(root, *C.STUB_FILES):
        C.git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m",
              "Level %d: fresh attempt from the stub" % level)
    C.write_phase(root, "none")
    C.clear_cycle(root)
    C.records(state)["new_attempts"].append(
        {"ts": C.now_iso(), "level": level, "branch": branch})
    C.save_state(root, state)
    return branch


def cmd_new_attempt(root, args):
    state = C.load_state(root)
    if C.read_phase(root) != "none":
        raise C.TddError("close the open cycle first (./tdd done).")
    branch = new_attempt(root, state, "new attempt")
    _say("Previous work saved on branch %s." % branch)
    _say("src/hzbin/binning.py and tests/ are back to the starting stub.")
    return 0
