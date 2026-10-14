"""Verify the TDD-ladder hidden assets and the self-test sample suites.

Run with the exercise venv python:  python hidden/verify_assets.py

A mutant counts as killed only by a test that passes on the reference.
Checks that the reference passes all acceptance tests, every mutant fails at
least one, and that each sample suite lands inside its expected score band.
Exits non-zero if any assertion fails.
"""
import concurrent.futures as cf
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIDDEN = ROOT / "hidden"
SRC = ROOT / "level0" / "src"
SAMPLES = ROOT / "selftest" / "samples"
REFERENCE = HIDDEN / "reference" / "binning.py"
ACCEPTANCE = HIDDEN / "acceptance"
MUTANTS = sorted((HIDDEN / "mutants").glob("M*.py"))
N_ACCEPT = 12
FAILURES = []


def check(cond, msg):
    """Record a failed assertion without stopping the run."""
    if not cond:
        FAILURES.append(msg)
        print(f"  ASSERTION FAILED: {msg}")


def run_suite(binning, tests_dir):
    """Run tests_dir against binning.py in a temp workspace.

    Returns (outcomes, seconds, returncode, stderr_tail), where outcomes maps
    test name to 'passed', 'failed', 'error' or 'skipped'.
    """
    with tempfile.TemporaryDirectory(prefix="tddverify-") as tmp:
        tmp = Path(tmp)
        shutil.copytree(SRC, tmp / "src")
        shutil.copyfile(binning, tmp / "src" / "hzbin" / "binning.py")
        shutil.copytree(tests_dir, tmp / "tests",
                        ignore=shutil.ignore_patterns("__pycache__"))
        xml = tmp / "junit.xml"
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             f"--junitxml={xml}", "tests"],
            cwd=tmp, env={"PYTHONPATH": str(tmp / "src"),
                          "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin"},
            capture_output=True, text=True, timeout=300)
        secs = time.perf_counter() - t0
        outcomes = {}
        if xml.exists():
            for case in ET.parse(xml).getroot().iter("testcase"):
                name = case.get("name")
                if case.find("failure") is not None:
                    outcomes[name] = "failed"
                elif case.find("error") is not None:
                    outcomes[name] = "error"
                elif case.find("skipped") is not None:
                    outcomes[name] = "skipped"
                else:
                    outcomes[name] = "passed"
        return outcomes, secs, proc.returncode, proc.stdout[-600:]


def bad(outcomes):
    """Names of tests that failed or errored."""
    return sorted(n for n, o in outcomes.items() if o in ("failed", "error"))


def merged_tests(dirs):
    """Copy several tests dirs into one temp dir; return the Path."""
    out = Path(tempfile.mkdtemp(prefix="tddtests-"))
    (out / "__init__.py").touch()
    for d in dirs:
        for f in Path(d).glob("*.py"):
            if f.name != "__init__.py":
                shutil.copyfile(f, out / f.name)
    return out


def suite_scores(pool, name, binning, tests):
    """Return dict of acceptance, kills, false alarms and runtime for a suite."""
    jobs = {"acc": pool.submit(run_suite, binning, ACCEPTANCE),
            "ref": pool.submit(run_suite, REFERENCE, tests)}
    for m in MUTANTS:
        jobs[m.stem] = pool.submit(run_suite, m, tests)
    res = {k: f.result() for k, f in jobs.items()}
    acc_out = res["acc"][0]
    passed = sum(1 for o in acc_out.values() if o == "passed")
    ref_bad = set(bad(res["ref"][0]))
    killed = [m.stem for m in MUTANTS
              if set(bad(res[m.stem][0])) - ref_bad]
    return {"name": name, "acc": passed, "killed": killed,
            "false_alarms": bad(res["ref"][0]), "ref_collect": res["ref"][2],
            "ref_secs": res["ref"][1]}


def main():
    """Run all verification stages and print the report."""
    t_start = time.perf_counter()
    meta = json.loads((HIDDEN / "mutants.json").read_text())
    check(len(MUTANTS) == 16, f"expected 16 mutants, found {len(MUTANTS)}")
    check(sorted(meta) == [m.stem for m in MUTANTS],
          "mutants.json keys do not match mutant files")

    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        print("== (a) Reference vs acceptance suite ==")
        out, _, rc, tail = run_suite(REFERENCE, ACCEPTANCE)
        n_pass = sum(1 for o in out.values() if o == "passed")
        print(f"  {n_pass}/{len(out)} passed (pytest exit code {rc})")
        check(n_pass == N_ACCEPT and len(out) == N_ACCEPT,
              f"reference passes {n_pass}/{len(out)}, expected {N_ACCEPT}")

        print("\n== (b) Mutants vs acceptance suite ==")
        futs = {m.stem: pool.submit(run_suite, m, ACCEPTANCE)
                for m in MUTANTS}
        for k, f in futs.items():
            failing = bad(f.result()[0])
            spec = meta.get(k, {}).get("spec", "?")
            short = ", ".join(n.replace("test_", "") for n in failing)
            print(f"  {k} ({spec:5s}) fails {len(failing):2d}: {short}")
            check(failing, f"{k} fails no acceptance test")

        print("\n== (c) Sample suites ==")
        samples = []
        for d in ("l0_naive", "l1_tests_after"):
            samples.append((d, SAMPLES / d / "binning.py",
                            SAMPLES / d / "tests"))
        for d in ("rung4", ):
            samples.append(("l3_cycles/rung4",
                            SAMPLES / "l3_cycles" / d / "binning.py",
                            SAMPLES / "l3_cycles" / d / "tests"))
        samples.append(("l4_rung5", SAMPLES / "l4_rung5" / "binning.py",
                        SAMPLES / "l4_rung5" / "tests"))
        cycle_dirs = [SAMPLES / "l3_cycles" / f"cycle{i}" for i in range(1, 6)]
        for i, cd in enumerate(cycle_dirs, 1):
            samples.append((f"l3_cycles/cycle{i} (cumulative)",
                            cd / "binning.py",
                            merged_tests([c / "tests" for c in
                                          cycle_dirs[:i]])))
        scores = {}
        for name, binning, tests in samples:
            scores[name] = suite_scores(pool, name, binning, tests)

        print(f"  {'sample':34s} {'acc':>6s} {'kills':>6s} {'FA':>3s} "
              f"{'ref s':>6s}")
        for name, s in scores.items():
            print(f"  {name:34s} {s['acc']:>3d}/12 {len(s['killed']):>3d}/16 "
                  f"{len(s['false_alarms']):>3d} {s['ref_secs']:>6.2f}")
            if s["false_alarms"]:
                print(f"      false alarms: {s['false_alarms']}")
            surv = [m.stem for m in MUTANTS if m.stem not in s["killed"]]
            print(f"      survivors: {', '.join(surv) or 'none'}")

        n = scores["l0_naive"]
        check(4 <= n["acc"] <= 9, f"l0_naive acceptance {n['acc']} not 4-9")
        check(len(n["killed"]) <= 6, "l0_naive kills > 6")
        n = scores["l1_tests_after"]
        check(6 <= n["acc"] <= 10, f"l1 acceptance {n['acc']} not 6-10")
        check(len(n["killed"]) <= 8, "l1 kills > 8")
        n = scores["l3_cycles/rung4"]
        check(len(n["killed"]) >= 9, f"rung4 kills {len(n['killed'])} < 9")
        check(not n["false_alarms"], "rung4 has false alarms")
        n = scores["l4_rung5"]
        check(len(n["killed"]) >= 14, f"rung5 kills {len(n['killed'])} < 14")
        check(not n["false_alarms"], "rung5 has false alarms")
        for i in range(1, 6):
            n = scores[f"l3_cycles/cycle{i} (cumulative)"]
            check(not n["false_alarms"] and n["ref_collect"] == 0,
                  f"cycle{i} cumulative tests fail on the reference")

    print("\n== Cycle red/green checks ==")
    for i in range(1, 6):
        own = merged_tests([c / "tests" for c in cycle_dirs[:i]])
        out, _, _, _ = run_suite(cycle_dirs[i - 1] / "binning.py", own)
        check(out and not bad(out), f"cycle{i} binning fails its own tests")
        prev = (cycle_dirs[i - 2] / "binning.py" if i > 1
                else SRC / "hzbin" / "binning.py")
        out, _, _, _ = run_suite(prev, merged_tests(
            [c / "tests" for c in cycle_dirs[:i]]))
        check(bad(out), f"cycle{i} new test is not red on the previous code")
        line = (cycle_dirs[i - 1] / "behaviour.txt").read_text().strip()
        check(line and "\n" not in line, f"cycle{i} behaviour.txt not one line")
        print(f"  cycle{i}: green on own code, red on previous: "
              f"{len(bad(out))} failing | {line}")

    out, _, _, _ = run_suite(REFERENCE, SAMPLES / "l3_cycles" / "bad_import"
                             / "tests")
    print(f"\n== bad_import: outcomes on reference: {out}")
    check(bad(out), "bad_import suite does not fail")
    txt = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         str(SAMPLES / "l3_cycles" / "bad_import" / "tests")],
        capture_output=True, text=True,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin",
             "PYTHONDONTWRITEBYTECODE": "1"}).stdout
    check("ImportError" in txt, "bad_import does not fail with ImportError")

    spec = (SAMPLES / "l2" / "SPEC.md").read_text()
    nums = re.findall(r"^\s*(\d+)\.\s", spec, re.M)
    print(f"\n== l2/SPEC.md numbered decisions: {nums}")
    check(nums == [str(i) for i in range(1, 8)], "SPEC.md needs items 1-7")

    print("\n== Rung-5 timing (serial, reference) ==")
    _, secs, _, _ = run_suite(REFERENCE, SAMPLES / "l4_rung5" / "tests")
    print(f"  {secs:.2f} s")
    check(secs < 10, "rung5 suite takes >= 10 s")

    print(f"\nTotal wall time: {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} assertion(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
