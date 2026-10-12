"""./tdd score: acceptance, mutants killed, false alarms."""

import concurrent.futures
import json
import os
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

from gatekit import packs, state as st
from tddtool import common as C

RUN_TIMEOUT = 120
WORKSPACE_INI = "[pytest]\ntestpaths = tests\npythonpath = src\naddopts = -p no:cacheprovider\n"


def _say(text=""):
    print(text)


def _copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".pytest_cache"))


def make_workspace(base, name, src_dir, tests_dir, binning_path=None):
    """Create <base>/<name> with src/ and tests/, optionally swapping binning.py."""
    ws = os.path.join(base, name)
    _copy_tree(src_dir, os.path.join(ws, "src"))
    if os.path.isdir(tests_dir):
        _copy_tree(tests_dir, os.path.join(ws, "tests"))
    else:
        os.makedirs(os.path.join(ws, "tests"))
    if binning_path:
        shutil.copy2(binning_path, os.path.join(ws, "src", "hzbin", "binning.py"))
    with open(os.path.join(ws, "pytest.ini"), "w", encoding="utf-8") as fh:
        fh.write(WORKSPACE_INI)
    return ws


def run_suite(python, workspace):
    """Run pytest in a workspace; return (outcomes dict, collection error, seconds)."""
    junit = os.path.join(workspace, "junit.xml")
    env = dict(os.environ, TDD_NO_LOG="1", PYTHONDONTWRITEBYTECODE="1")
    env.pop("TDD_RUN_ID", None)
    started = time.time()
    try:
        proc = subprocess.run([python, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                               "--junitxml", junit, "tests"], cwd=workspace,
                              capture_output=True, text=True, env=env,
                              timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {}, "timed out after %d s" % RUN_TIMEOUT, time.time() - started
    elapsed = time.time() - started
    outcomes = {}
    collection_error = None
    try:
        tree = ET.parse(junit)
    except (OSError, ET.ParseError):
        tail = (proc.stdout or proc.stderr).strip().splitlines()[-1:] or ["no output"]
        return {}, "pytest produced no report: %s" % tail[0], elapsed
    for case in tree.iter("testcase"):
        name = "%s::%s" % (case.get("classname", ""), case.get("name", ""))
        outcome = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                outcome = child.tag
                if "collection" in name or case.get("name") == "":
                    collection_error = (child.get("message") or "")[:200]
                break
            if child.tag == "skipped":
                outcome = "skipped"
                break
        outcomes[name] = outcome
    if proc.returncode in (2, 3, 4) and not outcomes:
        collection_error = collection_error or "pytest exit %d" % proc.returncode
    return outcomes, collection_error, elapsed


def score(root, state, quiet=False):
    """Run the three scoring jobs in parallel and return the result dict."""
    python = C.venv_python(root)
    keys = C.vault_keys(root)
    if "scoring" not in keys:
        raise C.TddError("no scoring secret in keys.bin")
    started = time.time()
    base = tempfile.mkdtemp(prefix="tdd-score-")
    try:
        hidden = os.path.join(base, "hidden")
        with open(os.path.join(root, ".vault", "scoring.pack"), "rb") as fh:
            packs.unpack_to(fh.read(), [bytes.fromhex(keys["scoring"])], hidden)
        with open(os.path.join(hidden, "mutants.json"), encoding="utf-8") as fh:
            mutants = json.load(fh)
        reference = os.path.join(hidden, "reference", "binning.py")
        src_dir = os.path.join(root, "src")
        tests_dir = os.path.join(root, "tests")
        jobs = {
            "acceptance": make_workspace(base, "acceptance", src_dir,
                                         os.path.join(hidden, "acceptance")),
            "reference": make_workspace(base, "reference", src_dir, tests_dir,
                                        reference),
        }
        for mid in sorted(mutants):
            jobs[mid] = make_workspace(base, mid, src_dir, tests_dir,
                                       os.path.join(hidden, "mutants", mid + ".py"))
        workers = min(8, max(2, os.cpu_count() or 2))
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_suite, python, ws): name
                       for name, ws in jobs.items()}
            for future in concurrent.futures.as_completed(futures):
                results[futures[future]] = future.result()
    finally:
        shutil.rmtree(base, ignore_errors=True)

    acc_outcomes, acc_err, _ = results["acceptance"]
    acceptance_total = len(acc_outcomes) if acc_outcomes else 12
    acceptance = sum(1 for o in acc_outcomes.values() if o == "passed")
    ref_outcomes, ref_err, suite_s = results["reference"]
    good_tests = sorted(n for n, o in ref_outcomes.items() if o == "passed")
    false_alarms = sorted(n for n, o in ref_outcomes.items() if o != "passed")
    survivors, attribution = [], {}
    for mid in sorted(mutants):
        m_outcomes, m_err, _ = results[mid]
        killed = any(m_outcomes.get(t) != "passed" for t in good_tests) or (
            bool(good_tests) and m_err is not None)
        if not killed:
            survivors.append(mid)
        for t in false_alarms:
            if m_outcomes.get(t) == "passed":
                attribution.setdefault(t, set()).add(mutants[mid]["spec"])
    result = {
        "ts": C.now_iso(), "level": state.get("level", 0),
        "acceptance": acceptance, "acceptance_total": acceptance_total,
        "acceptance_error": acc_err,
        "killed": len(mutants) - len(survivors), "mutants_total": len(mutants),
        "survivors": survivors,
        "survivor_specs": sorted({mutants[m]["spec"] for m in survivors}),
        "survivor_spec_list": [mutants[m]["spec"] for m in survivors],
        "false_alarms": false_alarms,
        "false_alarm_specs": {t: sorted(s) for t, s in attribution.items()},
        "collection_error": ref_err,
        "test_count": len(ref_outcomes),
        "suite_seconds": round(suite_s, 2),
        "score_seconds": round(time.time() - started, 1),
    }
    return result


def format_score(result, mutants_spec=None):
    lines = []
    lines.append("ACCEPTANCE      %d/%d client tests pass on your implementation"
                 % (result["acceptance"], result["acceptance_total"]))
    if result.get("acceptance_error"):
        lines.append("  (%s)" % result["acceptance_error"])
    lines.append("MUTANTS KILLED  %d/%d" % (result["killed"], result["mutants_total"]))
    if result["survivors"]:
        lines.append("  surviving mutants violate: %s"
                     % ", ".join(_spec_counts(result)))
    lines.append("FALSE ALARMS    %d of your %d tests fail on a correct implementation"
                 % (len(result["false_alarms"]), result["test_count"]))
    if result.get("collection_error") and not result["test_count"]:
        lines.append("  your suite did not run on a correct implementation: %s"
                     % result["collection_error"])
    for name in result["false_alarms"]:
        specs = result["false_alarm_specs"].get(name) or []
        short = name.split("::")[-1]
        lines.append("  %-40s (conflicts with %s)"
                     % (short, ", ".join(specs) if specs else "unknown"))
    lines.append("SUITE RUNTIME   %.2f s on the correct implementation"
                 % result["suite_seconds"])
    lines.append("(score took %.1f s)" % result["score_seconds"])
    return "\n".join(lines)


def _spec_counts(result):
    counts = {}
    for spec in result.get("survivor_spec_list") or result["survivor_specs"]:
        counts[spec] = counts.get(spec, 0) + 1
    return ["%s (x%d)" % (s, n) if n > 1 else s for s, n in sorted(counts.items())]


def cmd_score(root, args):
    state = C.load_state(root)
    _say("Scoring: acceptance, 16 mutants and a false-alarm run, in parallel...")
    result = score(root, state)
    _say("")
    _say(format_score(result))
    C.records(state)["scores"].append(result)
    C.save_state(root, state)
    st.append_log(root, "Score at level %d" % state.get("level", 0),
                  "```\n%s\n```" % format_score(result))
    return 0


def cmd_ladder(root, args):
    state = C.load_state(root)
    scores = C.records(state).get("scores", [])
    if not scores:
        _say("No scores recorded yet.")
        return 0
    _say("%-6s %-12s %-14s %-12s %s" % ("Level", "Acceptance", "Mutants killed",
                                        "False alarms", "When"))
    for s in scores:
        _say("%-6d %-12s %-14s %-12d %s" % (
            s["level"], "%d/%d" % (s["acceptance"], s["acceptance_total"]),
            "%d/%d" % (s["killed"], s["mutants_total"]),
            len(s["false_alarms"]), s["ts"]))
    return 0
