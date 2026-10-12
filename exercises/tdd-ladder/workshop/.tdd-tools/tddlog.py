"""pytest plugin: append one record per session to .tdd/runs.jsonl.

Loaded through pytest.ini (`-p tddlog`).  Records the phase, git HEAD,
every test outcome and the exception type of each failure, so `./tdd`
can tell whether red was ever observed and whether a failure was an
assertion rather than an import or name error.  Set TDD_NO_LOG=1 to
disable (scoring runs do this).
"""

import datetime
import json
import os
import subprocess
import time

import pytest

_results = {}
_collection_errors = []
_started = time.time()


def _root(config):
    return str(config.rootpath)


def _exception_name(longrepr):
    try:
        message = longrepr.reprcrash.message
    except AttributeError:
        message = str(longrepr)
    head = message.strip().splitlines()[0] if message.strip() else ""
    name = head.split(":", 1)[0].strip()
    return name.split()[-1] if name else "UnknownError"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    entry = _results.setdefault(item.nodeid, {"outcome": "passed",
                                              "exc_type": None,
                                              "duration": 0.0})
    entry["duration"] += report.duration
    if report.skipped:
        entry["outcome"] = "skipped"
    if report.failed:
        entry["outcome"] = "failed" if report.when == "call" else "error"
        if call.excinfo is not None:
            entry["exc_type"] = call.excinfo.typename
        else:
            entry["exc_type"] = _exception_name(report.longrepr)


def pytest_collectreport(report):
    if report.failed:
        _collection_errors.append({"nodeid": report.nodeid,
                                   "exc_type": _exception_name(report.longrepr)})


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("TDD_NO_LOG"):
        return
    root = _root(session.config)
    tdd_dir = os.path.join(root, ".tdd")
    try:
        os.makedirs(tdd_dir, exist_ok=True)
    except OSError:
        return
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        head = ""
    try:
        with open(os.path.join(tdd_dir, "phase"), encoding="utf-8") as fh:
            phase = fh.read().strip() or "none"
    except OSError:
        phase = "none"
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).replace(
            microsecond=0).isoformat(),
        "run_id": os.environ.get("TDD_RUN_ID", ""),
        "head": head,
        "phase": phase,
        "exit_status": int(exitstatus),
        "duration": round(time.time() - _started, 3),
        "tests": _results,
        "collection_errors": _collection_errors,
    }
    try:
        with open(os.path.join(tdd_dir, "runs.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass
