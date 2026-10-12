"""Speed Run bench harness: bench | check | profile | fit.

Run through make (see the Makefile) with the exercise .venv python:

    harness.py bench   --impl fast|reference --n N [--catalogue NAME] [--no-record]
    harness.py check   --n N [--catalogue NAME] [--impl fast|reference]
    harness.py profile
    harness.py fit

Every run happens in a fresh worker process (`harness.py _worker <json>`),
one per repeat (3 runs if the first takes under 10 s, else 1; the reported
time is the median). Each worker imports numpy and loads the catalogue, then
times the import of the entry (`paircount.<impl>`, or the --impl-file
module) together with the `count_pairs` call, so work done at import time is
counted and nothing is carried between repeats. A C entry that compiles its
library on first import pays that cost once, in the first run ever; the
library is then cached under a name hashed from its source and flags.

The parent polls each worker's resident memory with `ps` every 0.1 s and
kills it above RACE_RSS_CAP_GB or after RACE_TIMEOUT_S per run (defaults and
ceilings 2.5 GB and 180 s; the environment can lower them, not raise them).
Peak memory is the largest over the repeats.

Correctness. A run over a whole public catalogue (2000, 20000 or 200000
rows) is compared with the golden counts in .gatekit/racetool/golden.json
under the division declared in race.toml. A run over the first n <= 4000
rows of a catalogue is compared with the frozen reference on the same rows
(for IMPL=reference that is the reference itself). Other prefixes are not
checked (pass is null).

Records. Each bench and profile run is appended to .workshop/race/bench.jsonl
as a JSON object signed with HMAC-SHA256 under the build pepper
(.gatekit/racetool/_pepper.py). Fields: ts, level, impl, catalogue, n,
repeats, seconds, seconds_all, peak_rss_bytes, division, sigma_fraction,
pass, diff, source_hash, toml_hash, head, error (null, or the plain-words
reason a run was killed or crashed), sqrt_calls (profile records only), sig.
source_hash is sha256 over paircount/ (sorted relative paths and bytes;
bytecode and compiled .so/.dylib/.o excluded); toml_hash is sha256 of
race.toml. Both are taken before the first worker starts and again after the
last; if either changed, the run is recorded with error "paircount/ or
race.toml changed during the run" and pass null, and the gates treat it as
stale.

Options used only by the race tool (`./race submit`), not by make:

    --catalogue PATH   a .npy file instead of a public catalogue name
    --golden PATH      a JSON file with the golden counts for that file
                       ({"counts": [...]} or {"<label>": [...]}, optional "edges")
    --label NAME       catalogue label for the output (default: file stem)
    --impl-file PATH   time count_pairs from this file instead of paircount
    --json-out PATH    write the unsigned result record to PATH as JSON

A bench run that uses any of these is never appended to the bench log
("not recorded (tool-only options)"). With --golden the per-bin diff is not
printed or written: only the number of failing bins and the largest
difference, so hidden golden counts never reach the output.

The exit status is 0 when the run passed (or was not checked), 1 when it
failed, was killed or crashed, and 2 when the harness refused to run.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".gatekit"))

REPEAT_BELOW_S = 10.0
POLL_S = 0.1
PROFILE_N = 1000
PROFILE_TOP = 15


class Refusal(Exception):
    """The harness will not run; the message says why."""


def _common():
    try:
        from racetool import common
    except ImportError as exc:
        raise Refusal("this repo is not built: the race tool is missing from "
                      ".gatekit (%s). Rebuild it with tools/build.py." % exc) from exc
    return common


# ------------------------------------------------------------------ worker

def worker(spec_json):
    """Child process: load data, then time importing the entry plus one call."""
    import resource

    spec = json.loads(spec_json)
    sys.path.insert(0, ROOT)
    result = {"counts": None, "seconds": None, "error": None}
    try:
        import numpy as np
        pos = _load_positions(np, spec["catalogue_path"], spec["n"])
        edges = np.array(spec["edges"], dtype=np.float64)
        nbins = len(edges) - 1
        start = time.perf_counter()
        fn = _load_count_pairs(spec, edges)
        if spec.get("profile"):
            result.update(_profiled(fn, pos, edges))
        else:
            counts = fn(pos, edges)
        result["seconds"] = time.perf_counter() - start
        if not spec.get("profile"):
            result["counts"] = _as_counts(np, counts, nbins)
        if spec.get("prefix_golden"):
            import paircount.reference as ref
            result["golden"] = _as_counts(np, ref.count_pairs(pos, edges), nbins)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["ru_maxrss_bytes"] = usage if sys.platform == "darwin" else usage * 1024
    tmp = spec["out"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    os.replace(tmp, spec["out"])
    return 0


def _load_positions(np, path, n):
    pos = np.load(path, allow_pickle=False)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError("catalogue %s has shape %s, expected (N, 3)"
                         % (os.path.basename(path), pos.shape))
    if n > pos.shape[0]:
        raise ValueError("asked for %d rows but the catalogue has %d" % (n, pos.shape[0]))
    return np.ascontiguousarray(pos[:n], dtype=np.float64)


def _load_count_pairs(spec, edges):
    import importlib
    if spec.get("impl_file"):
        import importlib.util
        mspec = importlib.util.spec_from_file_location("race_entry", spec["impl_file"])
        module = importlib.util.module_from_spec(mspec)
        mspec.loader.exec_module(module)
    else:
        package = importlib.import_module("paircount")
        theirs = tuple(float(e) for e in getattr(package, "EDGES", ()))
        if theirs != tuple(float(e) for e in edges):
            raise RuntimeError("paircount.EDGES no longer matches the golden "
                               "edges; restore paircount/__init__.py")
        module = importlib.import_module("paircount." + spec["impl"])
    fn = getattr(module, "count_pairs", None)
    if not callable(fn):
        raise RuntimeError("%s has no count_pairs(pos, edges) function"
                           % getattr(module, "__file__", "the entry"))
    return fn


def _as_counts(np, counts, nbins):
    arr = np.asarray(counts)
    if arr.shape != (nbins,):
        raise ValueError("count_pairs must return %d counts, got shape %s"
                         % (nbins, arr.shape))
    if not np.issubdtype(arr.dtype, np.integer):
        if not (np.issubdtype(arr.dtype, np.floating)
                and np.all(np.isfinite(arr)) and np.all(arr == np.round(arr))):
            raise ValueError("count_pairs must return whole-number counts "
                             "(got dtype %s)" % arr.dtype)
    return [int(c) for c in arr.tolist()]


def _profiled(fn, pos, edges):
    import cProfile
    import io
    import pstats
    import numpy as np
    prof = cProfile.Profile()
    prof.enable()
    counts = fn(pos, edges)
    prof.disable()
    stream = io.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("tottime").print_stats(PROFILE_TOP)
    sqrt_calls, sqrt_line = 0, None
    for (_, _, func), (_, nc, tt, _, _) in stats.stats.items():
        if "math.sqrt" in func:
            sqrt_calls += nc
            sqrt_line = "%10d calls  %8.3f s total  %s" % (nc, tt, func)
    return {"counts": _as_counts(np, counts, len(edges) - 1),
            "sqrt_calls": sqrt_calls,
            "profile_text": stream.getvalue(), "sqrt_line": sqrt_line}


# ------------------------------------------------------------------ parent

def _env_float(name, default, ceiling, unit):
    """A positive number from the environment, never above `ceiling`."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        raise Refusal("%s must be a number, not %r" % (name, raw)) from None
    if not value > 0 or not math.isfinite(value):
        raise Refusal("%s must be a positive number" % name)
    if value > ceiling:
        print("note: %s=%s is above the %g %s limit and is ignored; using %g %s."
              % (name, raw.strip(), ceiling, unit, ceiling, unit))
        return ceiling
    return value


def _ps_rss_bytes(pid):
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)],
                             capture_output=True, text=True).stdout.strip()
        return int(out) * 1024 if out else 0
    except (OSError, ValueError):
        return 0


def run_worker(spec, cap_gb, timeout_s):
    """Run the worker with the memory and time watchdog; return its result."""
    common = _common()
    fd, out = tempfile.mkstemp(prefix="race-worker-", suffix=".json")
    os.close(fd)
    os.unlink(out)
    spec = dict(spec, out=out)
    cap = cap_gb * common.GB
    peak, killed = 0, None
    start = time.monotonic()
    proc = subprocess.Popen([sys.executable, os.path.realpath(__file__),
                             "_worker", json.dumps(spec)], cwd=ROOT)
    try:
        while proc.poll() is None:
            rss = _ps_rss_bytes(proc.pid)
            peak = max(peak, rss)
            if rss > cap:
                killed = ("killed: resident memory passed %g GB; estimate "
                          "before you run" % cap_gb)
            elif time.monotonic() - start > timeout_s:
                killed = ("killed: still running after %d s, the time limit "
                          "for one run" % timeout_s)
            if killed:
                proc.kill()
                proc.wait()
                break
            time.sleep(POLL_S)
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        raise
    result = {"counts": None, "seconds": None, "error": killed}
    if not killed:
        try:
            with open(out, encoding="utf-8") as fh:
                result = json.load(fh)
        except (OSError, ValueError):
            result["error"] = ("the worker stopped without a result (exit "
                               "status %s)" % proc.returncode)
    try:
        os.unlink(out)
    except OSError:
        pass
    peak = max(peak, int(result.get("ru_maxrss_bytes") or 0))
    if not result.get("error") and peak > cap:
        result["error"] = ("resident memory passed %g GB between polls; "
                           "estimate before you run" % cap_gb)
    result["peak_rss_bytes"] = peak
    return result


def _median(values):
    values = sorted(values)
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else 0.5 * (values[mid - 1] + values[mid])


def _read_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        raise Refusal("%s is missing (%s); this repo is not fully built"
                      % (what, os.path.relpath(path, ROOT))) from None
    except ValueError as exc:
        raise Refusal("%s is not valid JSON: %s" % (what, exc)) from exc


def _golden_entry(data, key):
    """(counts, edges) from a golden file, tolerating the documented layouts."""
    edges = data.get("edges") if isinstance(data, dict) else None
    entry = data
    if isinstance(data, dict):
        if key in data:
            entry = data[key]
        elif "counts" in data:
            entry = data["counts"]
        else:
            lists = [v for k, v in data.items() if k != "edges" and isinstance(v, list)]
            entry = lists[0] if len(lists) == 1 else None
    if isinstance(entry, dict):
        edges = entry.get("edges", edges)
        entry = entry.get("counts")
    if not isinstance(entry, list) or not all(isinstance(c, int) for c in entry):
        return None, edges
    return entry, edges


def _catalogue(args, common):
    """(path, label, rows or None, golden counts or None, edges)."""
    public = _read_json(common.golden_path(ROOT), "the golden counts")
    _, public_edges = _golden_entry(public, "edges")
    if _is_path(args.catalogue):
        path = os.path.abspath(args.catalogue)
        label = args.label or os.path.splitext(os.path.basename(path))[0]
        counts, edges = None, public_edges
        if args.golden:
            counts, own_edges = _golden_entry(
                _read_json(args.golden, "the golden file"), label)
            edges = own_edges or edges
            if counts is None:
                raise Refusal("no golden counts for %s in %s" % (label, args.golden))
    else:
        label = args.catalogue or common.catalogue_for_n(args.n)
        if label not in common.CATALOGUES:
            raise Refusal("unknown catalogue %r; use one of %s"
                          % (label, ", ".join(common.CATALOGUES)))
        path = os.path.join(ROOT, "data", label + ".npy")
        counts, edges = _golden_entry(public, label)
        if counts is None:
            raise Refusal("no golden counts for %s in .gatekit/racetool/golden.json" % label)
    if not os.path.exists(path):
        raise Refusal("catalogue file %s is missing" % path)
    if not edges or len(edges) != common.NBINS + 1:
        raise Refusal("the golden file has no list of %d bin edges" % (common.NBINS + 1))
    return path, label, _rows(path), counts, [float(e) for e in edges]


def _is_path(catalogue):
    return bool(catalogue) and (os.sep in catalogue or catalogue.endswith(".npy"))


def _rows(path):
    """Row count from the .npy header without loading the data."""
    try:
        import numpy as np
        return int(np.load(path, mmap_mode="r", allow_pickle=False).shape[0])
    except Exception as exc:
        raise Refusal("cannot read %s: %s" % (path, exc)) from exc


def _state_level(common):
    from gatekit import state as st
    try:
        return st.load_state(ROOT)["level"]
    except st.StateError as exc:
        raise Refusal("%s" % exc) from exc


def _reference_refusal(common):
    pep = common.pepper(ROOT)
    fit = common.fit_reference(common.valid_records(ROOT, pep))
    target = common.TARGET_N
    if fit:
        seconds = common.predict_seconds(fit, target)
        how = "from your fit, alpha = %.2f" % fit["alpha"]
    else:
        seconds = common.SECONDS_PER_PAIR * common.pairs(target)
        how = "at about 110 ns per pair, %s pairs" % format(common.pairs(target), ",")
    return ("refused: the pure-Python reference is the slow baseline and is capped at "
            "N <= %d here; at N = %s it would take about %s (%s). Use make fit to "
            "extrapolate." % (common.REFERENCE_MAX_N, format(target, ","),
                              common.format_seconds(seconds), how))


def measure(args, common, impl, profile=False, repeat=True):
    """Run one measurement; return (record, extras) with the unsigned record."""
    hashes_before = (common.source_hash(ROOT), common.toml_hash(ROOT))
    division = common.read_division(ROOT)
    path, label, rows, golden, edges = _catalogue(args, common)
    n = rows if args.n is None else args.n
    if n < 2:
        raise Refusal("N must be at least 2")
    if n > rows:
        raise Refusal("%s has %s rows; N = %s is too many" % (label, format(rows, ","),
                                                              format(n, ",")))
    whole = n == rows
    if whole and golden is not None:
        golden_source = "golden"
    elif not whole and n <= common.REFERENCE_MAX_N and not args.golden:
        golden_source = "reference"
    else:
        golden, golden_source = None, None
    is_reference = impl in ("reference", "profile")
    spec = {"catalogue_path": path, "n": n, "edges": edges, "profile": profile,
            "prefix_golden": golden_source == "reference" and not is_reference}
    if getattr(args, "impl_file", None):
        spec["impl_file"] = os.path.abspath(args.impl_file)
    else:
        spec["impl"] = "reference" if is_reference else impl
    cap_gb = _env_float("RACE_RSS_CAP_GB", common.DEFAULT_RSS_CAP_GB,
                        common.MAX_RSS_CAP_GB, "GB")
    timeout_s = _env_float("RACE_TIMEOUT_S", common.DEFAULT_TIMEOUT_S,
                           common.MAX_TIMEOUT_S, "s")
    first, seconds_all, peak, error = None, [], 0, None
    while True:
        result = run_worker(spec, cap_gb, timeout_s)
        peak = max(peak, int(result["peak_rss_bytes"]))
        error = result.get("error")
        if error:
            break
        seconds_all.append(round(result["seconds"], 4))
        if first is None:
            first = result
        elif result.get("counts") != first.get("counts"):
            error = ("count_pairs gave different counts on repeated runs of "
                     "the same data")
            break
        if not repeat or len(seconds_all) >= 3 or seconds_all[0] >= REPEAT_BELOW_S:
            break
        spec = dict(spec, prefix_golden=False)
    first = first or {}
    counts = first.get("counts")
    if golden_source == "reference":
        golden = counts if is_reference else first.get("golden")
    if not error and hashes_before != (common.source_hash(ROOT), common.toml_hash(ROOT)):
        error = common.CHANGED_DURING_RUN
    record = {
        "ts": common.now_iso(), "impl": impl, "catalogue": label, "n": n,
        "repeats": len(seconds_all),
        "seconds": round(_median(seconds_all), 4) if seconds_all and not error else None,
        "seconds_all": seconds_all,
        "peak_rss_bytes": peak,
        "division": division["name"], "sigma_fraction": division["sigma_fraction"],
        "pass": None, "diff": [], "error": error,
    }
    if error == common.CHANGED_DURING_RUN:
        record["pass"] = None
    elif error or counts is None:
        record["pass"] = False
    elif golden is not None:
        record["pass"], record["diff"] = common.compare(
            golden, counts, division["name"], division["sigma_fraction"])
    if args.golden:
        diff = record.pop("diff")
        record["diff_bins"] = len(diff)
        record["fail_bins"] = sum(
            1 for _, g, c in diff if abs(c - g) > common.allowed_shift(
                g, division["name"], division["sigma_fraction"]))
        record["diff_max"] = max((abs(c - g) for _, g, c in diff), default=0)
    if profile:
        record["sqrt_calls"] = first.get("sqrt_calls")
    record["source_hash"], record["toml_hash"] = hashes_before
    record["head"] = common.git_head(ROOT)
    extras = {"rows": rows, "edges": edges, "golden_source": golden_source,
              "cap_gb": cap_gb, "profile_text": first.get("profile_text"),
              "sqrt_line": first.get("sqrt_line"), "hidden": bool(args.golden)}
    return record, extras


def print_block(record, extras, common, title):
    say = print
    impl = "reference (profiled)" if record["impl"] == "profile" else record["impl"]
    say("%s: %s on %s, N = %s (%s of %s rows)" % (
        title, impl, record["catalogue"], format(record["n"], ","),
        "all" if record["n"] == extras["rows"] else "first " + format(record["n"], ","),
        format(extras["rows"], ",")))
    if record["error"] == common.CHANGED_DURING_RUN:
        say("  STOPPED       %s; run it again" % record["error"])
    elif record["error"]:
        say("  STOPPED       %s" % record["error"])
    else:
        times = record["seconds_all"]
        detail = ("median of %d runs, each in a fresh process: %s" % (
            len(times), ", ".join(common.format_seconds(t) for t in times))
                  if len(times) > 1 else "1 run")
        say("  time (import + count)  %s  (%s)" % (
            common.format_seconds(record["seconds"]), detail))
    say("  peak memory   %s  (a level needs < %s; the harness kills at %g GB)" % (
        common.format_gb(record["peak_rss_bytes"]),
        common.format_gb(common.PASS_RSS_BYTES), extras["cap_gb"]))
    division = record["division"]
    if division == "toleranced":
        division += " (sigma_fraction %g)" % record["sigma_fraction"]
    say("  division      %s" % division)
    if record["error"]:
        say("  correct       not checked (the run did not finish cleanly)")
    elif extras["hidden"]:
        against = ("the hidden golden counts" if record["catalogue"] == "hidden"
                   else "the counts in the --golden file")
        if record["pass"] and not record["diff_bins"]:
            say("  correct       yes: all %d bins match %s" % (common.NBINS, against))
        elif record["pass"]:
            say("  correct       yes, within the toleranced division: %d of %d bins "
                "differ from %s" % (record["diff_bins"], common.NBINS, against))
        else:
            say("  correct       NO: %d of %d bins fail against %s (largest "
                "difference %d counts)" % (record["fail_bins"], common.NBINS, against,
                                           record["diff_max"]))
            say("                per-bin diagnostics are available on the public "
                "catalogue: make check N=200000")
    elif record["pass"] is None:
        say("  correct       not checked: golden counts exist for the whole "
            "catalogues (N = 2000, 20000, 200000) and for N <= %d" % common.REFERENCE_MAX_N)
    else:
        against = ("the golden counts" if extras["golden_source"] == "golden"
                   else "the reference on the same %s rows" % format(record["n"], ","))
        diff = record["diff"]
        if record["pass"] and not diff:
            say("  correct       yes: all %d bins match %s" % (common.NBINS, against))
        elif record["pass"]:
            say("  correct       yes, within the toleranced division: %d of %d bins "
                "differ from %s" % (len(diff), common.NBINS, against))
        else:
            say("  correct       NO: %d of %d bins differ from %s" % (
                len(diff), common.NBINS, against))
        if diff:
            say("")
            say(common.diff_table(extras["edges"], diff, record["division"],
                                  record["sigma_fraction"]))
    if record.get("sqrt_calls") is not None:
        say("  math.sqrt     %s calls" % format(record["sqrt_calls"], ","))


def _tool_only(args):
    """True when a bench run uses options reserved for the race tool."""
    if args.golden or args.label or args.impl_file or args.json_out:
        return True
    catalogue = getattr(args, "catalogue", None)
    return catalogue is not None and catalogue not in ("mock_2k", "mock_20k", "mock_200k")


def _record(record, common, args):
    if _tool_only(args):
        if not args.json_out:
            print("not recorded (tool-only options)")
        return
    if args.no_record:
        print("not recorded (--no-record)")
        return
    level = _state_level(common)
    record = dict(record, level=level)
    index = common.append_record(ROOT, record)
    print("recorded as run %d: %s, %s, N = %d (level %d)" % (
        index, record["impl"], record["catalogue"], record["n"], level))


def _exit_code(record):
    return 1 if record["error"] or record["pass"] is False else 0


# ---------------------------------------------------------------- commands

def cmd_bench(args):
    common = _common()
    if not args.impl_file and args.impl not in ("fast", "reference"):
        raise Refusal("IMPL must be fast or reference, not %r" % args.impl)
    if not args.no_record and not _tool_only(args):
        common.pepper(ROOT)
        level = _state_level(common)
        if level == 0 and args.impl == "fast":
            print("note: Level 0 measures the reference; use IMPL=reference "
                  "(fast.py is still the same code at this level).")
    if args.impl == "reference" and (args.n or 0) > common.REFERENCE_MAX_N:
        raise Refusal(_reference_refusal(common))
    impl = "calibration" if args.impl_file else args.impl
    record, extras = measure(args, common, impl)
    print_block(record, extras, common, "bench")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(record, fh, sort_keys=True)
    _record(record, common, args)
    return _exit_code(record)


def cmd_check(args):
    common = _common()
    if args.impl == "reference" and args.n > common.REFERENCE_MAX_N:
        raise Refusal(_reference_refusal(common))
    record, extras = measure(args, common, args.impl, repeat=False)
    print_block(record, extras, common, "check")
    print("(correctness check only; not recorded. Use make bench to record a run.)")
    return _exit_code(record)


def cmd_profile(args):
    common = _common()
    common.pepper(ROOT)
    args.n, args.catalogue = PROFILE_N, "mock_2k"
    record, extras = measure(args, common, "profile", profile=True, repeat=False)
    if extras["profile_text"]:
        print("cProfile of the reference at N = %d, top %d functions by own time "
              "(tottime):" % (PROFILE_N, PROFILE_TOP))
        print(extras["profile_text"].replace(ROOT + os.sep, "").rstrip())
        print("")
    if extras["sqrt_line"]:
        print("math.sqrt: %s" % extras["sqrt_line"].strip())
        print("")
    print_block(record, extras, common, "profile")
    _record(record, common, args)
    return _exit_code(record)


def cmd_fit(args):
    common = _common()
    fit = common.fit_reference(common.valid_records(ROOT))
    if fit is None:
        raise Refusal("the fit needs reference runs at two or more different N; "
                      "run make bench N=500 IMPL=reference, then N=1000 and N=2000")
    n = common.TARGET_N
    print("Fit of log t against log N over reference runs at N = %s (median time per N):"
          % ", ".join(str(x) for x in fit["ns"]))
    print("  t = %.3g s x N^alpha" % math.exp(fit["log_a"]))
    print("  alpha (scaling exponent)  %.2f" % fit["alpha"])
    print("  time per pair             %.0f ns  (time / (N(N-1)/2), median over N)"
          % (fit["per_pair_s"] * 1e9))
    print("  predicted at N = %-9s %.1f minutes" % (
        format(n, ","), common.predict_seconds(fit, n) / 60.0))
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="bench/harness.py",
                                     description="Speed Run bench harness")
    sub = parser.add_subparsers(dest="command")
    bench = sub.add_parser("bench", help="time an implementation and check it")
    bench.add_argument("--impl", default="fast")
    bench.add_argument("--n", type=int)
    bench.add_argument("--catalogue")
    bench.add_argument("--no-record", action="store_true")
    bench.add_argument("--golden", help=argparse.SUPPRESS)
    bench.add_argument("--label", help=argparse.SUPPRESS)
    bench.add_argument("--impl-file", help=argparse.SUPPRESS)
    bench.add_argument("--json-out", help=argparse.SUPPRESS)
    check = sub.add_parser("check", help="correctness only, not recorded")
    check.add_argument("--impl", default="fast", choices=("fast", "reference"))
    check.add_argument("--n", type=int, default=2000)
    check.add_argument("--catalogue")
    sub.add_parser("profile", help="cProfile of the reference at N = 1000")
    sub.add_parser("fit", help="scaling exponent from the reference runs")
    args = parser.parse_args(argv)
    for name in ("no_record", "golden", "label", "impl_file", "json_out", "catalogue"):
        if not hasattr(args, name):
            setattr(args, name, False if name == "no_record" else None)
    if args.golden and not args.catalogue:
        parser.error("--golden needs --catalogue PATH")
    if getattr(args, "n", 0) is None and not _is_path(getattr(args, "catalogue", None)):
        args.n = 2000
    if args.command is None:
        parser.print_help()
        sys.exit(2)
    return args


def main(argv):
    if argv[:1] == ["_worker"]:
        return worker(argv[1])
    args = parse_args(argv)
    commands = {"bench": cmd_bench, "check": cmd_check, "profile": cmd_profile,
                "fit": cmd_fit}
    try:
        return commands[args.command](args)
    except Refusal as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted; the run was stopped and not recorded.\n")
        return 130
    except Exception as exc:
        common = sys.modules.get("racetool.common")
        if common is not None and isinstance(exc, common.RaceError):
            sys.stderr.write("refused: %s\n" % exc)
            return 2
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
