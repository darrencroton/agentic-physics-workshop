"""Verify the Speed Run data, goldens, solutions and wrong-semantics traps.

Run with the exercise venv python. Defaults are the source tree:

    python hidden/verify_assets.py
    python hidden/verify_assets.py --paircount DIR --data DIR \
        --golden FILE --hidden DIR

Checks: the golden counts reproduce (reference at 2k and 20k; calibration and
the level 3 C counter at 200k and hidden); the three solutions are exact (level
1 at 2k and 20k only: brute force at 200k takes minutes), with level 1 at 20k
under LEVEL1_MAX_SECONDS and LEVEL1_MAX_RSS_GB; each wrong-semantics variant
moves at least one bin on every catalogue (so exact fails) yet passes the
toleranced division at sigma_fraction 0.1 in every bin:
  (i)   s < e*e instead of sqrt(s) < e
  (ii)  the <= convention, edges[k] < r <= edges[k+1]
        (cKDTree when scipy imports, else a numpy emulation)
  (iii) np.histogram, whose last bin is closed
  (iv)  brute.c built with clang's default FMA contraction
Exits 0 only when every check passes.
"""

import argparse
import json
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
TOLERANCE = 0.1
LEVEL1_MAX_SECONDS = 10.0
LEVEL1_MAX_RSS_GB = 1.0
FAILURES = []


def check(cond, msg):
    """Record a failed check without stopping the run."""
    if not cond:
        FAILURES.append(msg)
        print(f"  CHECK FAILED: {msg}")
    return cond


def worker(pkg_parent, impl, npy, out):
    """Subprocess body: time paircount.<impl>.count_pairs on one catalogue."""
    sys.path.insert(0, pkg_parent)
    import importlib

    edges = np.array(importlib.import_module("paircount").EDGES)
    module = importlib.import_module(f"paircount.{impl}")
    pos = np.load(npy, allow_pickle=False)
    t0 = time.perf_counter()
    counts = module.count_pairs(pos, edges)
    seconds = time.perf_counter() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss *= 1 if sys.platform == "darwin" else 1024
    result = {"counts": [int(c) for c in counts], "seconds": seconds,
              "rss": rss}
    Path(out).write_text(json.dumps(result))


def run_impl(pkg_parent, impl, npy):
    """Run one implementation in a fresh interpreter; return its result."""
    with tempfile.NamedTemporaryFile(suffix=".json") as out:
        cmd = [sys.executable, "-B", __file__, "_worker", str(pkg_parent),
               impl, str(npy), out.name]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            check(False, f"{impl} on {Path(npy).name} crashed:\n"
                         f"{res.stderr[-2000:]}")
            return None
        return json.loads(Path(out.name).read_text())


def make_package(tmp, paircount_dir, label, files=()):
    """Copy the paircount package to tmp/label/paircount, overlaying files."""
    dst = Path(tmp) / label / "paircount"
    ignore = shutil.ignore_patterns("__pycache__", "*.so")
    shutil.copytree(paircount_dir, dst, ignore=ignore)
    for f in files:
        shutil.copyfile(f, dst / Path(f).name)
    return dst.parent


def compile_brute(hidden, tmp, flags):
    """Compile verify/brute.c with these flags; return a count() wrapper."""
    import ctypes

    clang = shutil.which("clang")
    if clang is None:
        sys.exit("ERROR: clang not found; install the command line tools")
    lib_path = Path(tmp) / f"brute{len(flags)}.so"
    cmd = [clang, "-O2", *flags, "-shared", "-fPIC", "-o", str(lib_path),
           str(hidden / "verify" / "brute.c")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"ERROR: {' '.join(cmd)} failed:\n{res.stderr}")
    lib = ctypes.CDLL(str(lib_path))
    dbl, i64 = ctypes.POINTER(ctypes.c_double), ctypes.c_longlong
    lib.count.argtypes = [dbl, i64, dbl, ctypes.c_int, ctypes.POINTER(i64)]

    def count(pos, edges):
        out = np.zeros(len(edges) - 1, dtype=np.int64)
        lib.count(pos.ctypes.data_as(dbl), len(pos), edges.ctypes.data_as(dbl),
                  len(edges) - 1, out.ctypes.data_as(ctypes.POINTER(i64)))
        return out

    return count


_NOTED = set()


def _note_once(message):
    """Print a message the first time it is given."""
    if message not in _NOTED:
        _NOTED.add(message)
        print(message)


def variant_counts(calibration, pos, edges):
    """Counts under the reference and variants (i)-(iii) from one pass.

    Reuses calibration's cell traversal by swapping in a binner that receives
    every candidate s = dx*dx + dy*dy + dz*dz.
    """
    nb = len(edges) - 1
    e2 = edges * edges
    s_lo, s_hi = 0.99 * e2[0], 1.01 * e2[-1]
    acc = {v: np.zeros(nb, dtype=np.int64) for v in ("ref", "i", "ii", "iii")}

    def binner(counts, s, edges_):
        s = s[(s >= s_lo) & (s <= s_hi)]
        r = np.sqrt(s)
        for v, k in (
            ("ref", np.searchsorted(edges, r, side="right") - 1),
            ("i", np.searchsorted(e2, s, side="right") - 1),
            ("ii", np.searchsorted(edges, r, side="left") - 1),
        ):
            acc[v] += np.bincount(k[(k >= 0) & (k < nb)], minlength=nb)
        acc["iii"] += np.histogram(r, bins=edges)[0]

    original = calibration._bin_into
    calibration._bin_into = binner
    try:
        calibration.count_pairs(pos, edges)
    finally:
        calibration._bin_into = original
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        _note_once("    scipy absent: (ii) uses a numpy emulation of <=")
    else:
        tree = cKDTree(pos)
        per = tree.count_neighbors(tree, edges, cumulative=False)
        acc["ii"] = np.asarray(per[1:], dtype=np.int64) // 2
        _note_once("    scipy present: (ii) uses cKDTree.count_neighbors")
    return acc


def static_checks(args, hidden, edges, golden_hidden, cats):
    """Edges agree everywhere; fast.py and level 2 are copies; shapes."""
    print("== static checks")
    sys.path.insert(0, str(args.paircount.resolve().parent))
    import paircount

    def body(path, skip):
        return path.read_text().splitlines()[skip:]

    cal, l2 = hidden / "calibration.py", hidden / "solutions/level2/fast.py"
    split = "\nimport numpy"
    for ok, msg in (
        (np.array_equal(paircount.EDGES, edges), "EDGES != golden edges"),
        (np.array_equal(golden_hidden["edges"], edges), "hidden edges"),
        (np.array_equal(edges, np.geomspace(0.5, 10, 16)), "not geomspace"),
        (body(args.paircount / "reference.py", 1)
         == body(args.paircount / "fast.py", 1), "fast.py != reference.py"),
        (cal.read_text().split(split)[1] == l2.read_text().split(split)[1],
         "solutions/level2/fast.py is not a copy of calibration.py"),
    ):
        check(ok, msg)
    for name, path in cats.items():
        pos = np.load(path, allow_pickle=False)
        n = {"mock_2k": 2000, "mock_20k": 20000}.get(name, 200000)
        check(pos.shape == (n, 3) and pos.dtype == np.float64
              and pos.flags.c_contiguous, f"{name}: bad shape or dtype")


def check_solutions(tmp, args, hidden, golden, cats, timings):
    """Reference and solutions reproduce golden; level 1 time and RSS."""
    print("== golden counts and solutions")
    sol = hidden / "solutions"
    files = {"reference": [], "level1": [sol / "level1/fast.py"],
             "level2": [sol / "level2/fast.py"],
             "level3": [sol / "level3/fast.py", sol / "level3/pairs.c"]}
    pkgs = {k: make_package(tmp, args.paircount, k, f)
            for k, f in files.items()}
    for name, path in cats.items():
        g = golden[name]
        small = name in ("mock_2k", "mock_20k")
        for label in ["level2", "level3"] + small * ["reference", "level1"]:
            impl = "reference" if label == "reference" else "fast"
            res = run_impl(pkgs[label], impl, path)
            if res is None:
                continue
            ok, sec, gb = res["counts"] == g, res["seconds"], res["rss"] / 1e9
            timings.append((name, label, sec, gb))
            print(f"  {name:9s} {label:9s} {'exact' if ok else 'WRONG'}  "
                  f"{sec:7.2f} s  peak RSS {gb:.2f} GB")
            check(ok, f"{label} does not reproduce golden on {name}")
            if label == "level1" and name == "mock_20k":
                check(sec < LEVEL1_MAX_SECONDS, f"level1 20k: {sec:.1f} s")
                check(gb < LEVEL1_MAX_RSS_GB, f"level1 20k: {gb:.2f} GB")


def check_variants(tmp, hidden, calibration, edges, golden, cats, timings):
    """Each variant moves >= 1 bin (exact fails) but passes toleranced."""
    print("== wrong-semantics variants "
          "(d = variant - golden; allowed = 0.1 sqrt(golden))")
    brute_default = compile_brute(hidden, tmp, [])
    names = {"i": "(i) s<e*e", "ii": "(ii) <=", "iii": "(iii) histogram",
             "iv": "(iv) C FMA"}
    for name, path in cats.items():
        pos = np.load(path, allow_pickle=False)
        g = np.array(golden[name], dtype=np.int64)
        t0 = time.perf_counter()
        acc = variant_counts(calibration, pos, edges)
        t1 = time.perf_counter()
        acc["iv"] = brute_default(pos, edges)
        timings.append((name, "variants i-iii", t1 - t0, None))
        timings.append((name, "brute.c default", time.perf_counter() - t1,
                        None))
        check(np.array_equal(acc.pop("ref"), g), f"{name}: ref != golden")
        allowed = TOLERANCE * np.sqrt(g)
        print(f"  [{name}]\n  {'bin':>3} {'edges':>15} {'golden':>9} "
              + " ".join(f"{names[v]:>15}" for v in names)
              + f" {'allowed':>8}")
        for b in range(len(g)):
            cells = " ".join(f"{int(acc[v][b] - g[b]):>+15d}" for v in names)
            print(f"  {b:>3} {edges[b]:6.3f}-{edges[b + 1]:<6.3f}  "
                  f"{g[b]:>9d} {cells} {allowed[b]:8.2f}")
        for v, label in names.items():
            d = np.abs(acc[v] - g)
            moved = int(np.count_nonzero(d))
            within = bool(np.all(d <= allowed))
            print(f"    {label:16s} bins moved {moved:2d}, max |d| {d.max()}, "
                  f"sum |d| {d.sum()}, toleranced 0.1 "
                  f"{'passes' if within else 'FAILS'}")
            if v == "iv" and moved == 0:
                print(f"  !!! (iv) DID NOT FIRE on {name}: clang's default "
                      "contraction gives the golden counts here. Not faked.")
            check(moved > 0, f"{name}: {label} moves no bin")
            check(within, f"{name}: {label} fails toleranced 0.1")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", action="store_true",
                    help="use the source tree (the default)")
    ap.add_argument("--paircount", type=Path,
                    default=ROOT / "level0" / "paircount")
    ap.add_argument("--data", type=Path, default=ROOT / "level0" / "data")
    ap.add_argument("--golden", type=Path,
                    default=ROOT / "workshop" / "racetool" / "golden.json")
    ap.add_argument("--hidden", type=Path, default=ROOT / "hidden")
    args = ap.parse_args()
    hidden = args.hidden.resolve()
    sys.path.insert(0, str(hidden))
    import calibration

    golden = json.loads(args.golden.read_text())
    golden_hidden = json.loads((hidden / "golden_hidden.json").read_text())
    golden["hidden"] = golden_hidden["hidden"]
    edges = np.array(golden["edges"], dtype=np.float64)
    cats = {n: args.data / f"{n}.npy"
            for n in ("mock_2k", "mock_20k", "mock_200k")}
    cats["hidden"] = hidden / "mock_hidden_200k.npy"
    timings = []
    static_checks(args, hidden, edges, golden_hidden, cats)
    with tempfile.TemporaryDirectory(prefix="speedrun-verify-") as tmp:
        check_solutions(tmp, args, hidden, golden, cats, timings)
        check_variants(tmp, hidden, calibration, edges, golden, cats,
                       timings)
    print("== timings")
    for name, label, sec, gb in timings:
        rss = f"  {gb:.2f} GB" if gb else ""
        print(f"  {name:9s} {label:16s} {sec:7.2f} s{rss}")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "_worker":
        worker(*sys.argv[2:6])
    else:
        sys.exit(main())
