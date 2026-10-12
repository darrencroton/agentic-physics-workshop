"""Generate the Speed Run catalogues, planted straddlers and golden counts.

Run with the exercise venv python (numpy) and clang on PATH:

    python make_data.py

Writes level0/data/mock_{2k,20k,200k}.npy, workshop/racetool/golden.json,
hidden/mock_hidden_200k.npy and hidden/golden_hidden.json. Deterministic.

Each catalogue is a Neyman-Scott mock in a 100 Mpc/h box (non-periodic) plus
planted pairs that sit exactly on, or within an ulp of, a bin edge:
  exact  r == edges[k] with s >= e*e (only the <= convention moves them)
  sumsq  r == edges[k] with s <  e*e (s < e*e without the sqrt moves them;
         every such pair is also exactly on the edge, since sqrt is monotonic)
  fma    clang's default FMA contraction puts the pair in a different bin
  rmax   one pair with r == edges[15] == 10.0 and s >= 100 (closed last edge)
where s = fl(dx*dx + dy*dy + dz*dz) and r = sqrt(s). Every planted pair is
checked again from the stored rows of the final, shuffled catalogue.
"""

import bisect
import ctypes
import json
import math
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "level0"))
sys.path.insert(0, str(ROOT / "hidden"))
from paircount import BOX, EDGES  # noqa: E402
from paircount.reference import count_pairs as reference_count  # noqa: E402
from calibration import count_pairs as calibration_count  # noqa: E402

CATALOGUES = {
    # name: (rows, planted pairs per kind, seed, output path)
    "mock_2k": (2000, 8, 20261012, ROOT / "level0/data/mock_2k.npy"),
    "mock_20k": (20000, 20, 20261013, ROOT / "level0/data/mock_20k.npy"),
    "mock_200k": (200000, 50, 20261014, ROOT / "level0/data/mock_200k.npy"),
    "hidden": (200000, 50, 20261015, ROOT / "hidden/mock_hidden_200k.npy"),
}
GOLDEN_PUBLIC = ROOT / "workshop/racetool/golden.json"
GOLDEN_HIDDEN = ROOT / "hidden/golden_hidden.json"
BRUTE_C = ROOT / "hidden/verify/brute.c"
CLUSTER_FRACTION = 0.7
SATELLITES_PER_PARENT = 70
CLUSTER_SIGMA = 1.5
FMA_JITTER_ULPS = 8
TOLERANCE = 0.1
MIN_BIN_COUNT = 400
VARIANTS = ("s<e*e", "<=", "histogram", "fma")
EDGE_ARR = np.array(EDGES, dtype=np.float64)
NBINS = len(EDGES) - 1
DBL = ctypes.POINTER(ctypes.c_double)


class Timer:
    """Print a step name and, on exit, how long it took."""

    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self.t0 = time.perf_counter()
        print(f"  {self.label} ...", flush=True)
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.t0
        print(f"  {self.label}: {self.seconds:.1f} s", flush=True)


def compile_brute(tmp):
    """Compile brute.c with clang's default contraction and with it off."""
    clang = shutil.which("clang")
    if clang is None:
        sys.exit(
            "ERROR: clang not found; the FMA straddlers need it. "
            "Install the Xcode command line tools."
        )
    libs = {}
    for name, flags in (("default", []), ("off", ["-ffp-contract=off"])):
        out = Path(tmp) / f"brute_{name}.so"
        cmd = [
            clang,
            "-O2",
            *flags,
            "-shared",
            "-fPIC",
            "-o",
            str(out),
            str(BRUTE_C),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"ERROR: {' '.join(cmd)} failed:\n{res.stderr}")
        lib = ctypes.CDLL(str(out))
        lib.count.argtypes = [
            DBL,
            ctypes.c_longlong,
            DBL,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_longlong),
        ]
        lib.pair_bins.argtypes = [
            DBL,
            DBL,
            ctypes.c_longlong,
            DBL,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
        ]
        libs[name] = lib
    return libs


def c_pair_bins(lib, a, b):
    """Bin index per row of a - b from the C helper (-1 below, NBINS above)."""
    a, b = np.ascontiguousarray(a), np.ascontiguousarray(b)
    out = np.empty(len(a), dtype=np.int32)
    lib.pair_bins(
        a.ctypes.data_as(DBL),
        b.ctypes.data_as(DBL),
        len(a),
        EDGE_ARR.ctypes.data_as(DBL),
        NBINS,
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
    )
    return out


def c_count(lib, pos):
    """Brute-force counts from the C library."""
    pos = np.ascontiguousarray(pos, dtype=np.float64)
    out = np.zeros(NBINS, dtype=np.int64)
    lib.count(
        pos.ctypes.data_as(DBL),
        len(pos),
        EDGE_ARR.ctypes.data_as(DBL),
        NBINS,
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_longlong)),
    )
    return out


def ref_pair(p, q):
    """Return (s, r) for one pair exactly as the reference computes them."""
    dx, dy, dz = p[0] - q[0], p[1] - q[1], p[2] - q[2]
    s = dx * dx + dy * dy + dz * dz
    return s, math.sqrt(s)


def ref_bin(r):
    """Reference bin of r with the same convention as pair_bins."""
    if r < EDGES[0]:
        return -1
    if r >= EDGES[-1]:
        return NBINS
    k = 0
    while r >= EDGES[k + 1]:
        k += 1
    return k


def classify(kind, k, p, q, libs):
    """True when the stored pair (p, q) is a valid straddler of this kind."""
    e = EDGES[k]
    s, r = ref_pair(p, q)
    if kind in ("exact", "rmax"):
        return r == e and s >= e * e
    if kind == "sumsq":
        return r == e and s < e * e
    a, b = np.array([p]), np.array([q])
    off = int(c_pair_bins(libs["off"], a, b)[0])
    default = int(c_pair_bins(libs["default"], a, b)[0])
    return off == ref_bin(r) and default != off


def sumsq_possible(e):
    """True when some s < fl(e*e) still has sqrt(s) == e."""
    return math.sqrt(float(np.nextafter(e * e, 0.0))) == e


def search(rng, kind, k, libs, stats):
    """Draw random pairs near edge k until one is a straddler: (a, b)."""
    e = EDGES[k]
    while True:
        b = rng.uniform(0.0, BOX, (4096, 3))
        u = rng.normal(size=(4096, 3))
        u /= np.linalg.norm(u, axis=1)[:, None]
        length = np.full(4096, e)
        if kind == "fma":
            jitter = rng.integers(-FMA_JITTER_ULPS, FMA_JITTER_ULPS + 1, 4096)
            length = e + jitter * np.spacing(e)
        a = b + length[:, None] * u
        inside = np.all((a >= 0.0) & (a < BOX), axis=1)
        a, b = a[inside], b[inside]
        if kind == "fma":
            hit = c_pair_bins(libs["default"], a, b) != c_pair_bins(
                libs["off"], a, b
            )
        else:
            d = a - b
            s = d[:, 0] * d[:, 0] + d[:, 1] * d[:, 1] + d[:, 2] * d[:, 2]
            hit = np.sqrt(s) == e
        for i in np.flatnonzero(hit):
            if classify(kind, k, a[i].tolist(), b[i].tolist(), libs):
                stats["tried"] += i + 1
                stats["found"] += 1
                return a[i], b[i]
        stats["tried"] += len(a)


def pair_bins_all(p, q, libs):
    """Bin of one pair (-1 below, NBINS above): reference and each variant."""
    s, r = ref_pair(p, q)
    hist = ref_bin(r)
    if r == EDGES[-1]:
        hist = NBINS - 1
    fma = c_pair_bins(libs["default"], np.array([p]), np.array([q]))[0]
    return {
        "reference": ref_bin(r),
        "s<e*e": bisect.bisect_right([e * e for e in EDGES], s) - 1,
        "<=": bisect.bisect_left(EDGES, r) - 1,
        "histogram": hist,
        "fma": int(fma),
    }


def movements(bins):
    """Per-bin count change of each variant relative to the reference."""

    def hist(ks):
        return np.bincount([k for k in ks if 0 <= k < NBINS], minlength=NBINS)

    ref = hist([b["reference"] for b in bins])
    return {v: hist([b[v] for b in bins]) - ref for v in VARIANTS}


def edge_cycle(rng, candidates, count):
    """count edge indices cycling through shuffled copies of candidates."""
    out = []
    while len(out) < count:
        out.extend(rng.permutation(candidates).tolist())
    return out[:count]


def neyman_scott(rng, n):
    """n points: satellites of Poisson parents plus a uniform background."""
    n_parents = rng.poisson(n / 100)
    parents = rng.uniform(0.0, BOX, (n_parents, 3))
    per_parent = rng.poisson(SATELLITES_PER_PARENT, n_parents)
    sats = np.repeat(parents, per_parent, axis=0)
    sats = sats + rng.normal(0.0, CLUSTER_SIGMA, sats.shape)
    outside = ~np.all((sats >= 0.0) & (sats < BOX), axis=1)
    while outside.any():
        centre = np.repeat(parents, per_parent, axis=0)[outside]
        sats[outside] = centre + rng.normal(0.0, CLUSTER_SIGMA, centre.shape)
        outside = ~np.all((sats >= 0.0) & (sats < BOX), axis=1)
    n_clustered = min(len(sats), int(round(CLUSTER_FRACTION * n)))
    sats = sats[rng.permutation(len(sats))[:n_clustered]]
    background = rng.uniform(0.0, BOX, (n - n_clustered, 3))
    return np.concatenate([sats, background]), n_parents


def plant(rng, name, n_pairs, base_counts, libs):
    """Choose edges, find straddlers and check the predicted variant movements.

    An edge is used only when the bins either side hold at least MIN_BIN_COUNT
    base pairs, so a move of one or two pairs stays inside sigma_fraction 0.1.
    The plan is redrawn until every variant moves at least one bin and every
    predicted move is within TOLERANCE * sqrt(base count).
    """
    ok = [
        k
        for k in range(NBINS + 1)
        if all(
            base_counts[b] >= MIN_BIN_COUNT
            for b in (k - 1, k)
            if 0 <= b < NBINS
        )
    ]
    sumsq = [k for k in ok if k < NBINS and sumsq_possible(EDGES[k])]
    exact = [k for k in ok if k < NBINS]
    print(f"    edges used: exact {exact}, sumsq {sumsq}, fma {ok}")
    allowed = TOLERANCE * np.sqrt(base_counts)
    for attempt in range(1, 51):
        plan = [("exact", k) for k in edge_cycle(rng, exact, n_pairs)]
        plan += [("sumsq", k) for k in edge_cycle(rng, sumsq, n_pairs)]
        plan += [("fma", k) for k in edge_cycle(rng, ok, n_pairs)]
        plan.append(("rmax", NBINS))
        stats = {
            kind: {"tried": 0, "found": 0}
            for kind in ("exact", "sumsq", "fma", "rmax")
        }
        pairs = [search(rng, kind, k, libs, stats[kind]) for kind, k in plan]
        moved = movements(
            [pair_bins_all(a.tolist(), b.tolist(), libs) for a, b in pairs]
        )
        if all(
            np.any(m != 0) and np.all(np.abs(m) <= allowed)
            for m in moved.values()
        ):
            break
        print(
            f"    attempt {attempt}: a predicted move is too large or empty; "
            "redrawing"
        )
    else:
        sys.exit(f"ERROR: {name}: no straddler plan passed in 50 attempts")
    for kind, st in stats.items():
        print(
            f"    {kind:5s}: {st['found']:3d} kept from "
            f"{st['tried']:7d} candidates "
            f"(yield {st['found'] / st['tried']:.2e})"
        )
    for v, m in moved.items():
        print(
            f"    predicted {v:9s}: {int(np.count_nonzero(m))} bins move, "
            f"max |d| {int(np.abs(m).max())}, d = {m.tolist()}"
        )
    return plan, pairs


def build_catalogue(name, libs):
    """Return (pos, planted); planted lists (kind, k, i, j) per pair."""
    n, n_pairs, seed, _ = CATALOGUES[name]
    rng = np.random.default_rng(seed)
    n_base = n - 2 * (3 * n_pairs + 1)
    with Timer(f"{name}: Neyman-Scott base of {n_base} points"):
        base, n_parents = neyman_scott(rng, n_base)
        base_counts = calibration_count(base, EDGE_ARR)
    print(
        f"    {n_parents} parents, "
        f"{SATELLITES_PER_PARENT} satellites each on average"
    )
    with Timer(f"{name}: search {3 * n_pairs + 1} straddler pairs"):
        plan, pairs = plant(rng, name, n_pairs, base_counts, libs)
    planted = np.array([pt for pair in pairs for pt in pair])
    pos = np.concatenate([base, planted])
    order = rng.permutation(n)
    pos = np.ascontiguousarray(pos[order])
    where = np.empty(n, dtype=np.int64)
    where[order] = np.arange(n)
    rows = [
        (kind, k, int(where[n_base + 2 * m]), int(where[n_base + 2 * m + 1]))
        for m, (kind, k) in enumerate(plan)
    ]
    return pos, rows


def check_planted(name, pos, planted, libs):
    """Re-verify every planted pair from the final catalogue's stored rows."""
    i = np.array([min(r[2], r[3]) for r in planted])
    j = np.array([max(r[2], r[3]) for r in planted])
    d = pos[i] - pos[j]
    r_numpy = np.sqrt(
        d[:, 0] * d[:, 0] + d[:, 1] * d[:, 1] + d[:, 2] * d[:, 2]
    )
    rows = pos.tolist()
    for m, (kind, k, _, _) in enumerate(planted):
        p, q = rows[i[m]], rows[j[m]]
        if not classify(kind, k, p, q, libs):
            sys.exit(
                f"ERROR: {name}: planted {kind} pair at edge {k} "
                "fails from stored rows"
            )
        if r_numpy[m] != ref_pair(p, q)[1]:
            sys.exit(
                f"ERROR: {name}: numpy elementwise r differs from math.sqrt"
            )
    assert pos.shape == (CATALOGUES[name][0], 3) and pos.dtype == np.float64
    assert pos.flags.c_contiguous and np.all((pos >= 0.0) & (pos < BOX))
    print(
        f"  {name}: all {len(planted)} planted pairs verified from stored "
        "rows; "
        f"numpy elementwise r equals math.sqrt bit for bit on all of them"
    )


def golden_counts(name, pos, libs):
    """Golden: reference at 2k/20k, calibration at 200k; cross-checked."""
    results = {}
    if len(pos) <= 20000:
        with Timer(f"{name}: reference (pure Python)"):
            results["reference"] = reference_count(pos, EDGE_ARR)
    with Timer(f"{name}: calibration (numpy cell list)"):
        results["calibration"] = calibration_count(pos, EDGE_ARR)
    with Timer(f"{name}: C brute force, -ffp-contract=off"):
        results["brute_off"] = c_count(libs["off"], pos)
    golden = results.get("reference", results["calibration"])
    for label, counts in results.items():
        if not np.array_equal(counts, golden):
            sys.exit(
                f"ERROR: {name}: {label} disagrees with golden\n"
                f"{counts}\n{golden}"
            )
    print(
        f"  {name}: {' = '.join(results)}; "
        f"total pairs in range {int(golden.sum())}"
    )
    print(f"    golden: {golden.tolist()}")
    return [int(c) for c in golden]


def main():
    if not np.array_equal(EDGE_ARR, np.geomspace(0.5, 10.0, 16)):
        sys.exit(
            "ERROR: paircount.EDGES are not the np.geomspace(0.5, 10.0, 16) "
            "floats"
        )
    t_all = time.perf_counter()
    golden = {"edges": list(EDGES)}
    with tempfile.TemporaryDirectory(prefix="speedrun-data-") as tmp:
        with Timer(
            "compile brute.c (default contraction and -ffp-contract=off)"
        ):
            libs = compile_brute(tmp)
        for name, (_, _, _, path) in CATALOGUES.items():
            print(f"[{name}]")
            pos, planted = build_catalogue(name, libs)
            check_planted(name, pos, planted, libs)
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, pos, allow_pickle=False)
            print(f"  wrote {path.relative_to(ROOT)} {pos.shape}")
            golden[name] = golden_counts(name, pos, libs)
    public = {
        k: golden[k] for k in ("edges", "mock_2k", "mock_20k", "mock_200k")
    }
    GOLDEN_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PUBLIC.write_text(json.dumps(public, indent=1) + "\n")
    GOLDEN_HIDDEN.write_text(
        json.dumps(
            {"edges": golden["edges"], "hidden": golden["hidden"]}, indent=1
        )
        + "\n"
    )
    print(
        f"wrote {GOLDEN_PUBLIC.relative_to(ROOT)} and "
        f"{GOLDEN_HIDDEN.relative_to(ROOT)}"
    )
    print(f"total {time.perf_counter() - t_all:.1f} s")


if __name__ == "__main__":
    main()
