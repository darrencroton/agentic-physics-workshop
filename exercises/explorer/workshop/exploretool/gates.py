"""Gate logic for Explorer: git evidence, the Markdown templates and tool runs.

The level checks (checks/levelN.py) call `run_check(root, level, out, err)`,
which calls `evaluate(root, level)` and prints `success_line(level)` and
nothing else on success; make_answers.py hashes the same text. On failure
the check prints one sentence naming the first problem and its fix.

Stdlib only and importable on Python 3.9. The checks themselves run under the
exercise .venv, so `sys.executable` there can run `python -m explorer` and
pytest, and plotly is importable.
"""

import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

DATASETS = ("data/pulsars.csv", "data/dimuons.csv")
MAX_POINTS = 20000
SAMPLED_POINTS = 500
RUN_TIMEOUT = 30
PYTEST_TIMEOUT = 120
MIN_TESTS = 5
MIN_HTML_BYTES = 1000000
REQUIRED_COMMITS = {0: 1, 1: 2, 2: 1, 3: 1}
CHECKED_PATHS = {
    0: ("PLAN.md",),
    1: ("explorer", "PLAN.md"),
    2: ("explorer", "tests", "TESTS.md"),
    3: ("explorer", "tests", "REVIEW.md"),
}
COMMIT_FIX = {
    0: "ask Claude to commit PLAN.md",
    1: "ask Claude to commit each step that works (two commits or more)",
    2: "ask Claude to commit the tests and TESTS.md",
    3: "ask Claude to commit each fix and REVIEW.md",
}
DECISIONS = (
    ("Values <= 0 on a log axis", ("log",)),
    ("Missing values in a selected column", ("missing",)),
    ("Initial selection when the page opens", ("initial",)),
    ("Sampling above --max-points", ("sampl", "max-points", "max points")),
)
PLAN_SECTIONS = (
    ("goal", "## Goal"),
    ("decisions", "## Decisions"),
    ("design", "## Design"),
    ("steps", "## Steps"),
    ("acceptance criteria", "## Acceptance criteria"),
    ("out of scope", "## Out of scope"),
)
SELECTS = ("x", "y", "z", "colour", "palette")
CHECKBOXES = ("logx", "logy", "logz", "logc")
VERDICTS = ("FIX", "ACCEPT", "REJECT")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?\S")
TOP_BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.)])(\s|$)")
MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])(?:\s+\[[ xX]\])?(\s+|$)")
DATASET_RE = re.compile(r"^Dataset:[ \t]*(.*?)\s*$", re.M)
SEPARATOR_RE = re.compile(r"^:?-{2,}:?$")
IMPORT_RE = re.compile(r"^\s*(?:from\s+explorer(?:\.[\w.]+)?\s+import\b|import\s+explorer\b)",
                       re.M)
EXTERNAL_SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']?\s*(?:https?:)?//",
                                re.I)


class CheckFailed(Exception):
    """One sentence naming the first thing that is wrong and how to fix it."""


def success_line(level):
    """The exact stdout of a passing level check."""
    return json.dumps({"level": level, "ok": True}, sort_keys=True) + "\n"


def _plural(count, word, plural=None):
    return "%d %s" % (count, word if count == 1 else (plural or word + "s"))


def _tail(text, limit=200):
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    last = lines[-1] if lines else "no output"
    return last if len(last) <= limit else last[:limit - 3] + "..."


# -------------------------------------------------------------------- git

def _git(root, *args):
    try:
        proc = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)
    except OSError as exc:
        raise CheckFailed("git could not run (%s): ask a facilitator" % exc)
    if proc.returncode != 0:
        raise CheckFailed("git %s failed (%s): ask a facilitator"
                          % (args[0], _tail(proc.stderr)))
    return proc.stdout


def _heads(root):
    path = os.path.join(root, ".workshop", "state.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        raise CheckFailed("the workshop state cannot be read: run ./gate status, "
                          "or ask a facilitator")
    return heads_from_state(state)


def heads_from_state(state):
    """records.heads from a state dict: {level string: commit}."""
    heads = ((state or {}).get("records") or {}).get("heads") or {}
    return heads if isinstance(heads, dict) else {}


def base_ref(heads, level):
    """The commit a level's count starts from: its recorded HEAD, else `start`."""
    return heads.get(str(level)) or "start"


def commits_since(root, level, heads=None):
    """Commits on HEAD since the level's base (`git rev-list --count`)."""
    base = base_ref(_heads(root) if heads is None else heads, level)
    probe = subprocess.run(["git", "rev-parse", "--verify", "-q", base + "^{commit}"],
                           cwd=root, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
    if probe.returncode != 0:
        what = "the git tag 'start'" if base == "start" else "commit %s" % base[:7]
        raise CheckFailed("%s is missing from this repo: ask a facilitator" % what)
    return int(_git(root, "rev-list", "--count", "%s..HEAD" % base).strip())


def dirty(root, paths):
    """Changed or untracked paths under `paths` (`git status --porcelain`)."""
    out = _git(root, "status", "--porcelain", "-z", "--", *paths)
    entries = out.split("\0")
    changed = []
    skip_next = False
    for entry in entries:
        if skip_next:
            skip_next = False
            continue
        if len(entry) < 4:
            continue
        changed.append(entry[3:])
        skip_next = "R" in entry[:2] or "C" in entry[:2]
    return changed


def _label(root, changed, paths):
    for path in paths:
        if changed == path or changed.startswith(path + "/"):
            return path + "/" if os.path.isdir(os.path.join(root, path)) else path
    return changed


def git_evidence(root, level, heads=None):
    """Raise CheckFailed unless the level has its commits and a clean tree."""
    count = commits_since(root, level, heads)
    need = REQUIRED_COMMITS[level]
    if count < need:
        if level == 0 and count == 0:
            raise CheckFailed("no commit since start: %s (this level needs at least 1)"
                              % COMMIT_FIX[0])
        since = "since start" if level == 0 else "since the last gate"
        counted = "no commits" if count == 0 else _plural(count, "commit")
        raise CheckFailed("%s %s; this level needs at least %d: %s"
                          % (counted, since, need, COMMIT_FIX[level]))
    paths = CHECKED_PATHS[level]
    changed = dirty(root, paths)
    if changed:
        raise CheckFailed("%s has uncommitted changes: ask Claude to commit, then unlock"
                          % _label(root, changed[0], paths))


def record_head(root, state, manifest, new_level):
    """post_unlock: remember HEAD so the next gate counts commits from here."""
    try:
        head = _git(root, "rev-parse", "HEAD").strip()
    except CheckFailed as exc:
        return ("Could not record the current commit (%s). The next gate counts "
                "commits from the start tag instead." % exc)
    records = state.setdefault("records", {})
    heads = records.get("heads")
    if not isinstance(heads, dict):
        heads = records["heads"] = {}
    heads[str(new_level)] = head
    return ("Recorded commit %s: the next gate counts your commits from here."
            % head[:7])


# --------------------------------------------------------------- Markdown

def _read(root, name, arrived=None):
    path = os.path.join(root, name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        if arrived is not None:
            raise CheckFailed("%s is missing; it arrived with Level %d: ask a facilitator "
                              "to restore it" % (name, arrived))
        raise CheckFailed("%s is missing: ask a facilitator to restore it" % name)
    except (OSError, UnicodeDecodeError) as exc:
        raise CheckFailed("%s cannot be read (%s)" % (name, exc))


def _plain(line):
    """Line text without list marker, emphasis or code ticks, lower-cased."""
    text = MARKER_RE.sub("", line, count=1)
    text = re.sub(r"[*_`]", "", text).replace("\u2019", "'")
    return " ".join(text.split()).lower()


def _key(title):
    return re.sub(r"^\d+[.)]?\s*", "", _plain(title))


def sections(text):
    """[(heading text, [lines])] for each level-2 heading; comments removed."""
    found = []
    current = None
    for line in COMMENT_RE.sub("", text).splitlines():
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) <= 2:
            current = (match.group(2), []) if len(match.group(1)) == 2 else None
            if current is not None:
                found.append(current)
            continue
        if current is not None:
            current[1].append(line)
    return found


def find_section(found, key):
    """Lines of the first section whose heading starts with `key`, else None."""
    for title, lines in found:
        if _key(title).startswith(key):
            return lines
    return None


def _meaningful(lines, template=()):
    skip = {_plain(t) for t in template}
    return [line for line in lines if _plain(line) and _plain(line) not in skip]


def _bullets(lines):
    return [line for line in lines if BULLET_RE.match(line)]


def _steps(lines):
    """Level-3 headings if there are any, else list items at the shallowest indent."""
    matches = (HEADING_RE.match(line) for line in lines)
    headings = [m.group(0) for m in matches if m and len(m.group(1)) == 3]
    if headings:
        return headings
    items = [line for line in lines if BULLET_RE.match(line)]
    if not items:
        return []
    indent = min(len(line) - len(line.lstrip()) for line in items)
    return [line for line in items if len(line) - len(line.lstrip()) == indent]


def _decision_answer(lines, name, keys):
    """None if no line names the decision, else its answer text ('' if blank)."""
    for index, line in enumerate(lines):
        text = _plain(line)
        label, colon, answer = text.partition(":")
        if not any(k in label for k in keys):
            continue
        if not colon:
            return "" if text == _plain(name) else text
        answer = answer.strip()
        if answer:
            return answer
        for follow in lines[index + 1:]:
            if TOP_BULLET_RE.match(follow) or HEADING_RE.match(follow):
                break
            if _plain(follow):
                return _plain(follow)
        return ""
    return None


def plan_dataset(root):
    """The dataset named on PLAN.md's Dataset: line, validated."""
    values = DATASET_RE.findall(_read(root, "PLAN.md"))
    if not values:
        raise CheckFailed("PLAN.md has no Dataset: line: put back \"Dataset: "
                          "data/pulsars.csv\" or \"Dataset: data/dimuons.csv\"")
    if len(values) > 1:
        raise CheckFailed("PLAN.md has %d Dataset: lines; keep exactly one (the "
                          "Makefile reads it)" % len(values))
    if values[0] not in DATASETS:
        raise CheckFailed("PLAN.md says \"Dataset: %s\"; it must be exactly "
                          "data/pulsars.csv or data/dimuons.csv (the Makefile reads "
                          "this line)" % values[0][:80])
    return values[0]


def _check_plan(root):
    text = _read(root, "PLAN.md")
    found = sections(text)
    template = [label + ":" for label, _ in DECISIONS]
    if not any(_meaningful(lines, template) for _, lines in found):
        raise CheckFailed("PLAN.md is still the template: in plan mode, ask Claude to "
                          "propose a plan, change it together, then have Claude save it "
                          "as PLAN.md and commit it")
    plan_dataset(root)
    for key, heading in PLAN_SECTIONS:
        lines = find_section(found, key)
        if lines is None:
            raise CheckFailed("PLAN.md has no \"%s\" section: keep the template's "
                              "headings" % heading)
        if not _meaningful(lines, template):
            raise CheckFailed("PLAN.md section \"%s\" is empty: fill it in with the "
                              "group's own words" % heading)
    decisions = find_section(found, "decisions")
    for label, keys in DECISIONS:
        answer = _decision_answer(decisions, label, keys)
        if answer is None:
            raise CheckFailed("PLAN.md Decisions has no \"%s:\" line: keep all four "
                              "decision lines and write the group's answer after each "
                              "colon" % label)
        if not answer:
            raise CheckFailed("PLAN.md decision \"%s\" is blank: write what the group "
                              "decided after the colon" % label)
    criteria = _bullets(find_section(found, "acceptance criteria"))
    if len(criteria) < 3:
        raise CheckFailed("PLAN.md lists %s; it needs at least 3, each something you "
                          "can check by eye or by test"
                          % _plural(len(criteria), "acceptance criterion",
                                    "acceptance criteria"))
    steps = _steps(find_section(found, "steps"))
    if not steps and _meaningful(find_section(found, "steps"), template):
        raise CheckFailed("PLAN.md's Steps section has no list: write the two steps as "
                          "a numbered list")
    if len(steps) < 2:
        raise CheckFailed("PLAN.md lists %s; it needs two, each ending in something you "
                          "can run and look at" % _plural(len(steps), "step"))
    if len(steps) > 2:
        raise CheckFailed("PLAN.md lists %s; merge them into two, each ending in "
                          "something you can run and look at: the command line and "
                          "data.json, then the page" % _plural(len(steps), "step"))


def plan_complete(root):
    """(ok, sentence): is PLAN.md filled in as the Level 0 gate requires?"""
    try:
        _check_plan(root)
    except CheckFailed as exc:
        return False, str(exc)
    return True, "PLAN.md is complete"


def _check_tests_md(root):
    found = sections(_read(root, "TESTS.md", arrived=2))
    ours = find_section(found, "our list")
    if ours is None:
        raise CheckFailed("TESTS.md has no \"## Our list\" section: keep the template's "
                          "headings")
    items = [line for line in _bullets(ours) if _plain(line)]
    if len(items) < 3:
        raise CheckFailed("TESTS.md has %s under \"Our list\": write at least 3 things "
                          "that must not break, before asking Claude"
                          % _plural(len(items), "item"))
    plan = find_section(found, "claude's plan")
    if plan is None:
        raise CheckFailed("TESTS.md has no \"## Claude's plan\" section: keep the "
                          "template's headings")
    if not _meaningful(plan, ["(Claude writes it here)"]):
        raise CheckFailed("TESTS.md has nothing under \"Claude's plan\" yet: ask Claude "
                          "for a plan of five to eight tests (what each checks, the "
                          "coverage, what it won't cover) and to write it there")


def _cells(line):
    text = line.strip()
    if not text.startswith("|"):
        return None
    text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", text)]


def _verdict(cell):
    raw = re.sub(r"[^A-Za-z]", "", cell).upper()
    if sum(v in raw for v in VERDICTS) > 1:
        return raw[:20]
    return next((v for v in VERDICTS if raw.startswith(v)), raw[:20])


def _check_review_md(root):
    found = sections(_read(root, "REVIEW.md", arrived=3))
    guesses = find_section(found, "our guesses")
    if guesses is None:
        raise CheckFailed("REVIEW.md has no \"## Our guesses\" section: keep the "
                          "template's headings")
    items = [line for line in _bullets(guesses) if _plain(line)]
    if len(items) < 2:
        raise CheckFailed("REVIEW.md has %s under \"Our guesses\": write at least 2 "
                          "things you think a reviewer will find, before asking"
                          % _plural(len(items), "guess", "guesses"))
    findings = find_section(found, "findings")
    if findings is None:
        raise CheckFailed("REVIEW.md has no \"## Findings\" section: keep the template's "
                          "headings")
    rows = [c for c in (_cells(line) for line in findings) if c is not None]
    decision_at, reason_at = 3, 4
    if rows and not all(SEPARATOR_RE.match(c) for c in rows[0] if c):
        header = [_plain(c) for c in rows[0]]
        for index, name in enumerate(header):
            if "decision" in name:
                decision_at = index
            elif "reason" in name:
                reason_at = index
        rows = rows[1:]
    rows = [r for r in rows if not all(SEPARATOR_RE.match(c) or not c for c in r)]
    triaged, problem = 0, ""
    for number, row in enumerate(rows, 1):
        decision = _verdict(row[decision_at]) if decision_at < len(row) else ""
        reason = row[reason_at] if reason_at < len(row) else ""
        reason = re.sub(r"[-\u2013\u2014*_`\s]", "", reason)
        if decision in VERDICTS and reason:
            triaged += 1
        elif not problem and any(row):
            if decision in VERDICTS:
                problem = "finding %d has no reason" % number
            elif decision:
                problem = "finding %d has decision '%s'" % (number, decision)
            else:
                problem = "finding %d has no decision" % number
    if triaged < 3:
        raise CheckFailed("REVIEW.md has %s; this level needs at least 3, each marked "
                          "FIX, ACCEPT or REJECT with a one-line reason%s"
                          % (_plural(triaged, "triaged finding"),
                             " (%s)" % problem if problem else ""))


# ------------------------------------------------------------------ tests

def run_pytest(root):
    """Raise CheckFailed unless pytest collects >= MIN_TESTS and all pass."""
    work = tempfile.mkdtemp(prefix="explore-pytest-")
    report = os.path.join(work, "report.xml")
    try:
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                                   "no:cacheprovider", "--junitxml", report],
                                  cwd=root, capture_output=True, text=True,
                                  timeout=PYTEST_TIMEOUT, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            raise CheckFailed("make test took over %d s: ask Claude why the tests are "
                              "so slow" % PYTEST_TIMEOUT)
        if proc.returncode == 5:
            raise CheckFailed("pytest found no tests: ask Claude to write them in tests/, "
                              "in files named test_*.py")
        try:
            suite = ET.parse(report).getroot()
        except (OSError, ET.ParseError):
            raise CheckFailed("make test did not run (exit %d: %s)"
                              % (proc.returncode, _tail(proc.stdout + proc.stderr)))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if suite.tag == "testsuites":
        suites = list(suite.iter("testsuite"))
    else:
        suites = [suite]
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for item in suites:
        for key in totals:
            totals[key] += int(item.get(key, 0) or 0)
    failed = totals["failures"] + totals["errors"]
    if proc.returncode in (2, 3, 4) or (failed and failed >= totals["tests"]
                                         and totals["errors"]):
        raise CheckFailed("make test could not collect or run the tests (exit %d: %s): "
                          "run make test and show Claude the error"
                          % (proc.returncode, _tail(proc.stdout + proc.stderr)))
    if failed or proc.returncode != 0:
        if failed:
            raise CheckFailed("make test: %d of %s fail: fix the code, not the tests, "
                              "then commit" % (failed, _plural(totals["tests"], "test")))
        raise CheckFailed("make test exited %d: %s"
                          % (proc.returncode, _tail(proc.stdout + proc.stderr)))
    if totals["tests"] < MIN_TESTS:
        raise CheckFailed("pytest collected %s; this level needs at least %d, all "
                          "passing: ask Claude for the tests you agreed in TESTS.md"
                          % (_plural(totals["tests"], "test"), MIN_TESTS))
    passed = totals["tests"] - totals["skipped"]
    if passed < MIN_TESTS:
        raise CheckFailed("only %d of %s pass (%d skipped); this level needs at least "
                          "%d passing" % (passed, _plural(totals["tests"], "test"),
                                          totals["skipped"], MIN_TESTS))


def _check_imports(root):
    tests = os.path.join(root, "tests")
    for folder, dirs, files in os.walk(tests):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            try:
                with open(os.path.join(folder, name), "r", encoding="utf-8") as fh:
                    if IMPORT_RE.search(fh.read()):
                        return
            except (OSError, UnicodeDecodeError):
                continue
    raise CheckFailed("no test module under tests/ imports explorer: the tests must "
                      "exercise the tool's own code")


# -------------------------------------------------------------- tool runs

_BUNDLE = []


def _plotly_bundle():
    if not _BUNDLE:
        try:
            from plotly.offline import get_plotlyjs
            _BUNDLE.append(get_plotlyjs())
        except Exception:
            _BUNDLE.append("")
    return _BUNDLE[0]


def _sidecar(root, dataset):
    path = os.path.join(root, os.path.splitext(dataset)[0] + ".columns.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            columns = json.load(fh)["columns"]
        if not isinstance(columns, dict):
            raise ValueError("columns is not an object")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CheckFailed("the column file for %s cannot be read (%s): ask a "
                          "facilitator" % (dataset, exc))
    numeric = [name for name, meta in columns.items()
               if isinstance(meta, dict) and meta.get("numeric")]
    return list(columns), numeric


def _csv_header(root, dataset):
    try:
        with open(os.path.join(root, dataset), "r", encoding="utf-8", newline="") as fh:
            return next(csv.reader(fh))
    except (OSError, StopIteration, csv.Error) as exc:
        raise CheckFailed("%s cannot be read (%s): ask a facilitator" % (dataset, exc))


def _run(root, args, what):
    argv = [sys.executable, "-m", "explorer"] + args
    try:
        return subprocess.run(argv, cwd=root, capture_output=True, text=True,
                              timeout=RUN_TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise CheckFailed("%s took over %d s: it should take a few seconds"
                          % (what, RUN_TIMEOUT))


def _require_ok(proc, what):
    if proc.returncode != 0:
        raise CheckFailed("%s exited %d: %s"
                          % (what, proc.returncode, _tail(proc.stderr or proc.stdout)))


def _reject_constant(name):
    raise ValueError("constant:" + name)


def _load_data_json(folder, what):
    path = os.path.join(folder, "data.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        raise CheckFailed("%s wrote no data.json in its --out directory" % what)
    except (OSError, UnicodeDecodeError) as exc:
        raise CheckFailed("%s: data.json cannot be read (%s)" % (what, exc))
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("constant:"):
            name = message.split(":", 1)[1]
            raise CheckFailed("%s: data.json is not valid JSON (%s is not JSON; write "
                              "it with allow_nan=False)" % (what, name))
        raise CheckFailed("%s: data.json is not valid JSON (%s)" % (what, message))


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_data(data, what, header, numeric, max_points):
    """Raise CheckFailed unless `data` has the data.json structure."""
    def fail(text):
        raise CheckFailed("%s: data.json %s" % (what, text))

    if not isinstance(data, dict):
        fail("is not a JSON object")
    for key in ("source", "n_read", "n_written", "columns", "rows", "labels"):
        if key not in data:
            fail("has no \"%s\" key (see the interface in README.md)" % key)
    if not isinstance(data["source"], str):
        fail("\"source\" is not a string")
    for key in ("n_read", "n_written"):
        if not isinstance(data[key], int) or isinstance(data[key], bool):
            fail("\"%s\" is not a whole number" % key)
    count = data["n_written"]
    if not 1 <= count <= max_points:
        fail("has n_written = %d; it must be between 1 and %d" % (count, max_points))
    columns, rows, labels = data["columns"], data["rows"], data["labels"]
    if not isinstance(columns, list):
        fail("\"columns\" is not a list")
    if not isinstance(rows, dict) or not isinstance(labels, dict):
        fail("\"rows\" and \"labels\" must be objects")
    names = []
    for index, column in enumerate(columns):
        if not isinstance(column, dict):
            fail("columns[%d] is not an object" % index)
        for key, kind in (("name", str), ("unit", str), ("description", str),
                          ("log", bool)):
            if not isinstance(column.get(key), kind):
                fail("columns[%d] has no %s \"%s\" (each column needs name, unit, "
                     "description and log)" % (index, kind.__name__, key))
        names.append(column["name"])
    if names != list(rows):
        fail("\"columns\" names must be exactly the keys of \"rows\", in the same "
             "order")
    for name in numeric:
        if name not in rows:
            fail("has no column %s, which the column file marks numeric" % name)
    positions = [header.index(n) if n in header else -1 for n in names]
    if -1 in positions:
        fail("column %s is not in the CSV header" % names[positions.index(-1)])
    if positions != sorted(positions):
        fail("\"columns\" are not in CSV order")
    for name, values in rows.items():
        if not isinstance(values, list) or len(values) != count:
            fail("rows[\"%s\"] has %s; n_written is %d"
                 % (name, _plural(len(values) if isinstance(values, list) else 0,
                                  "value"), count))
        for value in values:
            if value is None:
                continue
            if not _is_number(value):
                fail("rows[\"%s\"] holds %r; numeric columns hold numbers or null"
                     % (name, value))
            if isinstance(value, float) and not math.isfinite(value):
                fail("rows[\"%s\"] holds a non-finite number (%r); write missing "
                     "values as null" % (name, value))
    for name, values in labels.items():
        if not isinstance(values, list) or len(values) != count:
            fail("labels[\"%s\"] has %s; n_written is %d"
                 % (name, _plural(len(values) if isinstance(values, list) else 0,
                                  "value"), count))
    return names


class _Controls(HTMLParser):
    """Collect <select id=...> options and <input id=...> types."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.selects = {}
        self.inputs = {}
        self._select = None
        self._option = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select":
            self._select = attrs.get("id")
            if self._select is not None:
                self.selects.setdefault(self._select, [])
        elif tag == "option" and self._select is not None:
            self._close_option()
            self._option = [attrs.get("value"), ""]
        elif tag == "input" and attrs.get("id") is not None:
            self.inputs[attrs["id"]] = (attrs.get("type") or "text").lower()

    def handle_data(self, data):
        if self._option is not None:
            self._option[1] += data

    def handle_endtag(self, tag):
        if tag == "option":
            self._close_option()
        elif tag == "select":
            self._close_option()
            self._select = None

    def _close_option(self):
        if self._option is not None and self._select is not None:
            value, text = self._option
            self.selects[self._select].append(value if value is not None
                                              else text.strip())
        self._option = None


def _check_html(folder, what, names):
    path = os.path.join(folder, "explorer.html")
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except FileNotFoundError:
        raise CheckFailed("%s wrote no explorer.html in its --out directory" % what)
    text = raw.decode("utf-8", "replace")

    def fail(message):
        raise CheckFailed("%s: explorer.html %s" % (what, message))

    if EXTERNAL_SCRIPT_RE.search(text):
        fail("loads a script from the internet (<script src=\"http...\">): embed "
             "plotly.js inline so the page works offline")
    has_plotly = ("plotly.js v" in text or "Plotly.newPlot" in text
                  or "Plotly.react" in text)
    if len(raw) <= MIN_HTML_BYTES or not has_plotly:
        fail("is %d KB and has no inline plotly.js: embed "
             "plotly.offline.get_plotlyjs() in a <script>" % (len(raw) // 1024))
    parser = _Controls()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        fail("cannot be parsed as HTML (%s)" % exc)
    for sid in SELECTS:
        if sid not in parser.selects:
            fail("has no <select id=\"%s\"> (write the controls as plain HTML; the "
                 "check reads the file and does not run JavaScript)" % sid)
    for sid in ("x", "y", "z", "colour"):
        options = parser.selects[sid]
        for name in names:
            if name not in options:
                fail("<select id=\"%s\"> has no <option value=\"%s\">: every numeric "
                     "column must be an <option> written in the HTML (the check does "
                     "not run JavaScript)" % (sid, name))
    for sid in ("z", "colour"):
        if "none" not in parser.selects[sid]:
            fail("<select id=\"%s\"> has no <option value=\"none\">" % sid)
    palettes = len(parser.selects["palette"])
    if palettes < 3:
        fail("<select id=\"palette\"> has %s; it needs at least three colour scales"
             % _plural(palettes, "option"))
    for cid in CHECKBOXES:
        kind = parser.inputs.get(cid)
        if kind is None:
            fail("has no checkbox id=\"%s\" (a plain <input type=\"checkbox\"> in the "
                 "HTML)" % cid)
        if kind != "checkbox":
            fail("id=\"%s\" is not a checkbox (<input type=\"checkbox\" id=\"%s\">)"
                 % (cid, cid))
    bundle = _plotly_bundle()
    own = text.replace(bundle, "") if bundle and bundle in text else text
    for trace, use in (("scattergl", "2D plots must use WebGL scattergl traces"),
                       ("scatter3d", "3D plots must use scatter3d traces")):
        if trace not in own:
            fail("never mentions %s outside plotly.js itself: %s" % (trace, use))


def _tool_checks(root, dataset):
    if not os.path.isfile(os.path.join(root, "explorer", "__main__.py")):
        raise CheckFailed("there is no explorer/__main__.py yet: ask Claude to add the "
                          "command line")
    all_columns, numeric = _sidecar(root, dataset)
    header = _csv_header(root, dataset)
    work = tempfile.mkdtemp(prefix="explore-check-")
    try:
        what = "the default run on %s" % dataset
        out_a = os.path.join(work, "a")
        _require_ok(_run(root, [dataset, "--out", out_a], what), what)
        data = _load_data_json(out_a, what)
        names = _check_data(data, what, header, numeric, MAX_POINTS)
        _check_html(out_a, what, names)

        what = "the --max-points %d run on %s" % (SAMPLED_POINTS, dataset)
        out_b = os.path.join(work, "b")
        _require_ok(_run(root, [dataset, "--out", out_b, "--max-points",
                                str(SAMPLED_POINTS)], what), what)
        sampled = _load_data_json(out_b, what)
        _check_data(sampled, what, header, numeric, MAX_POINTS)
        if sampled["n_written"] != SAMPLED_POINTS:
            raise CheckFailed("--max-points %d wrote %s on %s; it must write exactly %d"
                              % (SAMPLED_POINTS, _plural(sampled["n_written"], "row"),
                                 dataset, SAMPLED_POINTS))
        if sampled["n_read"] != data["n_read"]:
            raise CheckFailed("%s reports n_read = %d, but the default run read %d: "
                              "n_read counts the rows in the file"
                              % (what, sampled["n_read"], data["n_read"]))

        what = "the --list run on %s" % dataset
        proc = _run(root, [dataset, "--list"], what)
        _require_ok(proc, what)
        for name in all_columns:
            if not re.search(r"(?<![\w])%s(?![\w])" % re.escape(name), proc.stdout):
                raise CheckFailed("%s does not print column %s: --list prints every "
                                  "column with its unit, description and missing count"
                                  % (what, name))

        what = "the run on a file that does not exist"
        proc = _run(root, [os.path.join(work, "does-not-exist.csv"), "--out",
                           os.path.join(work, "c")], what)
        if proc.returncode == 0:
            raise CheckFailed("%s exited 0: a missing file must give a message and a "
                              "non-zero exit" % what)
        if "Traceback" in proc.stdout + proc.stderr:
            raise CheckFailed("%s printed a Python traceback: catch the error and print "
                              "a one-line message instead" % what)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_tool_checks(root, dataset):
    """(ok, sentence): the four interface runs of the tool on `dataset`."""
    try:
        _tool_checks(root, dataset)
    except CheckFailed as exc:
        return False, str(exc)
    return True, "the tool runs on %s" % dataset


def _require_tool(root, dataset):
    ok, sentence = run_tool_checks(root, dataset)
    if not ok:
        raise CheckFailed(sentence)


# ----------------------------------------------------------- level checks

def evaluate(root, level):
    """(ok, sentence) for the gate that leaves `level`."""
    try:
        heads = _heads(root)
        if level == 0:
            _check_plan(root)
            summary = "PLAN.md is complete and committed"
        elif level == 1:
            dataset = plan_dataset(root)
            _require_tool(root, dataset)
            summary = "the tool runs on %s" % dataset
        elif level == 2:
            _check_tests_md(root)
            run_pytest(root)
            _check_imports(root)
            summary = "TESTS.md is filled in and the tests pass"
        elif level == 3:
            _check_review_md(root)
            run_pytest(root)
            dataset = plan_dataset(root)
            _require_tool(root, dataset)
            summary = "REVIEW.md is triaged, the tests pass and the tool runs on %s" % dataset
        else:
            return False, "there is no check for level %d" % level
        git_evidence(root, level, heads)
    except CheckFailed as exc:
        return False, str(exc)
    return True, summary


def run_check(root, level, out, err):
    """Entry point for checks/levelN.py; returns the exit status."""
    try:
        ok, sentence = evaluate(root, level)
    except Exception as exc:
        err.write("the check could not run: %s\n" % exc)
        return 1
    if not ok:
        err.write(sentence.rstrip(".") + ".\n")
        return 1
    out.write(success_line(level))
    return 0
