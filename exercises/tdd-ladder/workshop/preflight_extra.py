#!/usr/bin/env python3
"""Exercise-specific preflight checks for the TDD Ladder (run in .venv)."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
failures = 0


def report(ok, label, detail=""):
    global failures
    failures += 0 if ok else 1
    print("[%s] %s%s" % ("ok  " if ok else "FAIL", label,
                         (": " + detail) if detail else ""))


def main():
    try:
        import numpy  # noqa: F401
        import matplotlib  # noqa: F401
        import pytest  # noqa: F401
        report(True, "numpy, matplotlib and pytest import in .venv")
    except ImportError as exc:
        report(False, "exercise packages import", str(exc))
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "--co",
                           "-p", "no:cacheprovider"], cwd=ROOT,
                          capture_output=True, text=True,
                          env=dict(os.environ, TDD_NO_LOG="1"))
    report(proc.returncode in (0, 5), "pytest collects with the tddlog plugin",
           "" if proc.returncode in (0, 5) else proc.stdout[-300:])
    tdd = os.path.join(ROOT, "tdd")
    proc = subprocess.run([tdd, "status"], cwd=ROOT, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)
    report(proc.returncode == 0, "./tdd status runs", proc.stderr.strip())
    proc = subprocess.run([tdd, "green"], cwd=ROOT, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)
    report(proc.returncode == 3, "./tdd green refuses without a terminal")
    for rel in (".vault/scoring.pack", ".vault/keys.bin", "data/hz_mock.csv",
                "src/hzbin/binning.py"):
        report(os.path.exists(os.path.join(ROOT, rel)), "%s present" % rel)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
