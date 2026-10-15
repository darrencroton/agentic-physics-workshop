#!/usr/bin/env python3
"""Exercise-specific preflight checks for Explorer (run in .venv).

The tool itself (`python -m explorer`) is not checked: Claude builds it.
"""

import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
MIN_PLOTLYJS_BYTES = 1000000
DATASETS = ("data/pulsars.csv", "data/dimuons.csv")
failures = 0


def report(ok, label, detail=""):
    global failures
    failures += 0 if ok else 1
    print("[%s] %s%s" % ("ok  " if ok else "FAIL", label,
                         (": " + detail) if detail else ""))


def check_packages():
    for name in ("numpy", "plotly", "pytest", "pytest_cov"):
        try:
            module = __import__(name)
            version = getattr(module, "__version__", "")
            report(True, "%s %s imports in .venv" % (name, version))
        except ImportError as exc:
            report(False, "%s imports in .venv" % name, "%s; run ./preflight --setup" % exc)


def check_plotlyjs():
    try:
        from plotly.offline import get_plotlyjs
        size = len(get_plotlyjs().encode("utf-8"))
    except Exception as exc:
        report(False, "plotly.js is bundled with plotly", str(exc))
        return
    report(size > MIN_PLOTLYJS_BYTES, "plotly.js is bundled for offline pages (%.1f MB)"
           % (size / 1e6), "" if size > MIN_PLOTLYJS_BYTES else "too small; reinstall plotly")


def check_files():
    for rel in DATASETS + ("data/pulsars.columns.json", "data/dimuons.columns.json",
                           "data/README.md", "PLAN.md", "PLAYBOOK.md",
                           "explorer/__init__.py", "tests/__init__.py",
                           ".claude/agents/reviewer.md",
                           ".claude/skills/plan-code/SKILL.md",
                           ".claude/skills/review-code/SKILL.md",
                           ".claude/skills/style-code/SKILL.md",
                           ".claude/skills/test-code/SKILL.md"):
        report(os.path.isfile(os.path.join(ROOT, rel)), "%s present" % rel)


def check_make():
    make = shutil.which("make")
    if not make:
        report(False, "make present", "install the Xcode command line tools "
               "(xcode-select --install)")
        return
    proc = subprocess.run([make, "-n", "explore"], cwd=ROOT, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    match = re.search(r"-m explorer (\S+) --out ", line)
    dataset = match.group(1) if match else ""
    report(proc.returncode == 0 and dataset in DATASETS,
           "make explore reads the Dataset: line in PLAN.md (%s)" % (dataset or "none"),
           "" if dataset in DATASETS else
           (proc.stderr.strip().splitlines() or ["make -n explore printed nothing"])[-1]
           if proc.returncode != 0 else "PLAN.md needs \"Dataset: data/pulsars.csv\" "
           "or \"Dataset: data/dimuons.csv\"")


def check_ignored():
    proc = subprocess.run(["git", "check-ignore", "-q", "out/explorer.html"], cwd=ROOT,
                          capture_output=True, text=True, stdin=subprocess.DEVNULL)
    report(proc.returncode == 0, "out/ is ignored by git")


def main():
    check_packages()
    check_plotlyjs()
    check_files()
    check_make()
    check_ignored()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
