#!/usr/bin/env python3
"""Exercise-specific preflight checks for the Speed Run (run in .venv)."""

import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BENCH_LIMIT_S = 10.0
failures = 0

TINY_C = """
long long add_pairs(const double *x, long n) {
    long long total = 0;
    for (long i = 0; i < n; i++) total += (long long)x[i];
    return total;
}
"""


def report(ok, label, detail=""):
    global failures
    failures += 0 if ok else 1
    print("[%s] %s%s" % ("ok  " if ok else "FAIL", label,
                         (": " + detail) if detail else ""))


def check_packages():
    try:
        import numpy
        report(True, "numpy %s imports in .venv" % numpy.__version__)
    except ImportError as exc:
        report(False, "numpy imports in .venv", "%s; run ./preflight --setup (it reinstalls .venv packages)" % exc)
    try:
        import scipy
        report(True, "scipy %s imports in .venv" % scipy.__version__)
    except ImportError as exc:
        report(False, "scipy imports in .venv", "%s; run ./preflight --setup (it reinstalls .venv packages)" % exc)


def check_clang():
    clang = shutil.which("clang")
    if not clang:
        report(False, "clang present", "install the Xcode command line tools "
               "(xcode-select --install)")
        return
    work = tempfile.mkdtemp(prefix="race-preflight-")
    try:
        src = os.path.join(work, "tiny.c")
        lib = os.path.join(work, "libtiny.so")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(TINY_C)
        proc = subprocess.run([clang, "-O2", "-ffp-contract=off", "-shared", "-fPIC",
                               "-o", lib, src], capture_output=True, text=True)
        if proc.returncode != 0:
            report(False, "clang builds a shared library",
                   (proc.stderr.strip().splitlines() or ["no output"])[-1])
            return
        import ctypes
        handle = ctypes.CDLL(lib)
        handle.add_pairs.restype = ctypes.c_longlong
        handle.add_pairs.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_long]
        values = (ctypes.c_double * 3)(1.0, 2.0, 3.0)
        got = handle.add_pairs(values, 3)
        report(got == 6, "clang builds a shared library that loads with ctypes",
               "" if got == 6 else "returned %r, expected 6" % got)
    except OSError as exc:
        report(False, "clang builds a shared library that loads with ctypes", str(exc))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def check_bench():
    started = time.time()
    try:
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "bench", "harness.py"),
                               "bench", "--impl", "reference", "--n", "500",
                               "--no-record"], cwd=ROOT, capture_output=True,
                              text=True, timeout=60)
    except subprocess.TimeoutExpired:
        report(False, "bench harness: reference at N = 500", "took over 60 s")
        return
    elapsed = time.time() - started
    tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["no output"]
    report(proc.returncode == 0, "bench harness: reference at N = 500 runs and passes",
           "" if proc.returncode == 0 else tail[0])
    report(elapsed < BENCH_LIMIT_S, "bench harness finished in %.1f s (limit %d s)"
           % (elapsed, BENCH_LIMIT_S))


def check_race():
    race = os.path.join(ROOT, "race")
    proc = subprocess.run([race, "status"], cwd=ROOT, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)
    report(proc.returncode == 0, "./race status runs", proc.stderr.strip())
    proc = subprocess.run([race, "submit"], cwd=ROOT, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)
    report(proc.returncode == 3, "./race submit refuses without a terminal",
           "" if proc.returncode == 3 else "exit %d" % proc.returncode)


def check_files():
    for rel in (".vault/scoring.pack", ".gatekit/racetool/golden.json",
                "data/mock_2k.npy", "data/mock_20k.npy", "data/mock_200k.npy"):
        report(os.path.exists(os.path.join(ROOT, rel)), "%s present" % rel)


def main():
    check_packages()
    check_clang()
    check_files()
    check_bench()
    check_race()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
