"""Shared helpers for the race tool and the bench harness.

Stdlib only and importable on Python 3.9. `tomllib` is imported lazily: the
full race.toml validation runs only under the exercise .venv (3.11+).

Used by:
- bench/harness.py (venv): division validation, comparison, the diff table,
  source and toml hashes, signing and appending bench records;
- racetool (any python3): reading and verifying the signed bench log, state,
  the vault keys and the scoring pack.
"""

import datetime
import hashlib
import hmac
import importlib.util
import json
import math
from fractions import Fraction
import os
import re
import subprocess

from gatekit import crypto, packs, state as st

EXERCISE = "speed-run"
NBINS = 15
GB = 1e9
PASS_RSS_BYTES = 1.5 * GB
DEFAULT_RSS_CAP_GB = 2.5
DEFAULT_TIMEOUT_S = 180.0
MAX_RSS_CAP_GB = 2.5
MAX_TIMEOUT_S = 180.0
REFERENCE_MAX_N = 4000
SECONDS_PER_PAIR = 110e-9
TARGET_N = 200000
CATALOGUES = ("mock_2k", "mock_20k", "mock_200k")
DIVISIONS = ("exact", "toleranced")
SIGMA_MAX = 0.2
JUSTIFICATION_MIN = 80
BUILD_ARTEFACTS = (".so", ".dylib", ".o")
CHANGED_DURING_RUN = "paircount/ or race.toml changed during the run"


class RaceError(Exception):
    """A user-facing refusal with an explanation."""


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


# ------------------------------------------------------------------ paths

def race_dir(root):
    return os.path.join(root, ".workshop", "race")


def bench_log_path(root):
    return os.path.join(race_dir(root), "bench.jsonl")


def tool_dir(root):
    return os.path.join(root, ".gatekit", "racetool")


def golden_path(root):
    return os.path.join(tool_dir(root), "golden.json")


def toml_path(root):
    return os.path.join(root, "race.toml")


def harness_path(root):
    return os.path.join(root, "bench", "harness.py")


def venv_python(root):
    path = os.path.join(root, ".venv", "bin", "python")
    if not os.path.exists(path):
        raise RaceError("no .venv found. Run ./preflight (it sets up .venv).")
    return path


def catalogue_for_n(n):
    """The public catalogue the harness uses for a given n."""
    if n <= 2000:
        return "mock_2k"
    if n <= 20000:
        return "mock_20k"
    return "mock_200k"


def pairs(n):
    return n * (n - 1) // 2


# ---------------------------------------------------------------- signing

def pepper(root):
    """The build-time pepper from .gatekit/racetool/_pepper.py, loaded by path."""
    path = os.path.join(tool_dir(root), "_pepper.py")
    if not os.path.exists(path):
        raise RaceError("this repo is not built: .gatekit/racetool/_pepper.py is "
                        "missing, so bench runs cannot be signed. Rebuild it with "
                        "tools/build.py.")
    try:
        spec = importlib.util.spec_from_file_location("racetool_pepper", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        value = module.PEPPER
    except Exception as exc:
        raise RaceError("cannot read the build pepper: %s" % exc) from exc
    if not isinstance(value, str) or not value:
        raise RaceError("the build pepper is empty; rebuild the repo")
    return value


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def signature(record, pep):
    body = {k: v for k, v in record.items() if k != "sig"}
    return hmac.new(pep.encode("utf-8"), canonical(body).encode("utf-8"),
                    hashlib.sha256).hexdigest()


def sign(record, pep):
    record = dict(record)
    record.pop("sig", None)
    record["sig"] = signature(record, pep)
    return record


def verify(record, pep):
    sig = record.get("sig")
    if not isinstance(sig, str):
        return False
    return hmac.compare_digest(sig, signature(record, pep))


def append_record(root, record, pep=None):
    """Sign and append one record to the bench log; returns its 1-based index."""
    pep = pep or pepper(root)
    os.makedirs(race_dir(root), exist_ok=True)
    count = len(read_log(root, pep))
    line = json.dumps(sign(record, pep), sort_keys=True)
    with open(bench_log_path(root), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return count + 1


def read_log(root, pep=None):
    """All bench log lines as (record or None, valid) pairs, in order.

    A line that is not a JSON object gives (None, False). With no pepper
    every record is reported invalid.
    """
    out = []
    try:
        with open(bench_log_path(root), encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            out.append((None, False))
            continue
        if not isinstance(rec, dict):
            out.append((None, False))
            continue
        out.append((rec, bool(pep) and verify(rec, pep)))
    return out


def valid_records(root, pep=None):
    pep = pep or pepper(root)
    return [rec for rec, ok in read_log(root, pep) if ok]


def bad_record_count(root, pep):
    return sum(1 for _, ok in read_log(root, pep) if not ok)


# ----------------------------------------------------------------- hashes

def _tree_files(base):
    files = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames
                             if d != "__pycache__" and not d.endswith(".dSYM"))
        files += [os.path.join(dirpath, f) for f in sorted(filenames)
                  if not f.endswith(".pyc") and not f.endswith(BUILD_ARTEFACTS)
                  and f != ".DS_Store"]
    return sorted(files)


def source_hash(root):
    """sha256 over paircount/: sorted relative paths and bytes.

    Bytecode (__pycache__, .pyc), compiled artefacts (.so, .dylib, .o) and
    .dSYM folders are excluded: they are built from the hashed sources, and a C entry
    builds its library during the run.
    """
    digest = hashlib.sha256()
    base = os.path.join(root, "paircount")
    for path in _tree_files(base):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        digest.update(rel.encode("utf-8") + b"\0")
        with open(path, "rb") as fh:
            digest.update(fh.read())
        digest.update(b"\0")
    return digest.hexdigest()


def toml_hash(root):
    try:
        with open(toml_path(root), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def git(root, *args):
    proc = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                          text=True)
    return proc.returncode, proc.stdout, proc.stderr


def git_head(root):
    try:
        code, out, _ = git(root, "rev-parse", "HEAD")
    except OSError:
        return None
    return out.strip() if code == 0 and out.strip() else None


# --------------------------------------------------------------- division

def validate_division(data):
    """Validate parsed race.toml; return {name, sigma_fraction, justification}.

    Raises RaceError with the reason; never falls back silently.
    """
    if not isinstance(data, dict) or not isinstance(data.get("division"), dict):
        raise RaceError("race.toml needs a [division] table")
    div = data["division"]
    name = div.get("name")
    if name not in DIVISIONS:
        raise RaceError("race.toml: division name must be \"exact\" or "
                        "\"toleranced\", not %r" % (name,))
    sigma = div.get("sigma_fraction", 0.0)
    if isinstance(sigma, bool) or not isinstance(sigma, (int, float)) \
            or not math.isfinite(sigma):
        raise RaceError("race.toml: sigma_fraction must be a number")
    justification = div.get("justification", "")
    if not isinstance(justification, str):
        raise RaceError("race.toml: justification must be a string")
    if name == "exact":
        if sigma != 0:
            raise RaceError("race.toml: the exact division takes "
                            "sigma_fraction = 0.0 (found %r)" % sigma)
    else:
        if not 0 < sigma <= SIGMA_MAX:
            raise RaceError("race.toml: the toleranced division needs "
                            "0 < sigma_fraction <= %.1f (found %r)" % (SIGMA_MAX, sigma))
        if len(justification.strip()) < JUSTIFICATION_MIN:
            raise RaceError("race.toml: the toleranced division needs a "
                            "justification of at least %d characters (a real "
                            "paragraph); found %d" % (JUSTIFICATION_MIN,
                                                       len(justification.strip())))
    return {"name": name, "sigma_fraction": float(sigma),
            "justification": justification}


def read_division(root):
    """Parse and validate race.toml (needs tomllib, Python 3.11+)."""
    try:
        import tomllib
    except ImportError:
        raise RaceError("reading race.toml needs Python 3.11+; run this from "
                        "the .venv (run ./preflight to set it up)") from None
    try:
        with open(toml_path(root), "rb") as fh:
            data = tomllib.load(fh)
    except OSError:
        raise RaceError("race.toml is missing") from None
    except tomllib.TOMLDecodeError as exc:
        raise RaceError("race.toml is not valid TOML: %s" % exc) from exc
    return validate_division(data)


def division_summary(root):
    """One-line description of race.toml for status output; never raises."""
    try:
        try:
            div = read_division(root)
        except RaceError as exc:
            if "Python 3.11" not in str(exc):
                return "INVALID (%s)" % exc
            div = _division_by_regex(root)
        if div["name"] == "exact":
            return "exact"
        return "toleranced (sigma_fraction %g)" % div["sigma_fraction"]
    except Exception:
        return "unknown (race.toml unreadable)"


def _division_by_regex(root):
    """Display-only fallback for Python < 3.11; not used for validation."""
    with open(toml_path(root), encoding="utf-8") as fh:
        text = fh.read()
    name = re.search(r'^\s*name\s*=\s*"([^"]*)"', text, re.MULTILINE)
    sigma = re.search(r"^\s*sigma_fraction\s*=\s*([0-9.eE+-]+)", text, re.MULTILINE)
    return {"name": name.group(1) if name else "?",
            "sigma_fraction": float(sigma.group(1)) if sigma else 0.0}


# ------------------------------------------------------------- comparison

def allowed_shift(golden, division, sigma):
    """Largest |count - golden| that passes a bin."""
    if division == "exact":
        return 0
    shift = sigma * math.sqrt(golden)
    nearest = int(round(shift))
    # sigma^2 * golden is an exact square: the float product may land just below it.
    if Fraction(nearest * nearest) == Fraction(repr(float(sigma))) ** 2 * int(golden):
        return nearest
    return int(math.floor(shift))


def compare(golden, got, division, sigma):
    """Return (pass, diff) where diff lists [bin, golden, got] for differing bins."""
    diff = [[k, int(g), int(c)] for k, (g, c) in enumerate(zip(golden, got)) if g != c]
    ok = len(golden) == len(got) and all(
        abs(c - g) <= allowed_shift(g, division, sigma) for _, g, c in diff)
    return ok, diff


def diff_table(edges, diff, division, sigma):
    """Text table of the bins that differ."""
    lines = ["  %3s  %8s  %8s  %13s  %13s  %10s  %8s" % (
        "bin", "lo edge", "hi edge", "golden", "yours", "difference", "allowed")]
    for k, g, c in diff:
        allowed = allowed_shift(g, division, sigma)
        lo = "%.4f" % edges[k] if edges and k < len(edges) else "?"
        hi = "%.4f" % edges[k + 1] if edges and k + 1 < len(edges) else "?"
        lines.append("  %3d  %8s  %8s  %13d  %13d  %+10d  %8d%s" % (
            k, lo, hi, g, c, c - g, allowed,
            "" if abs(c - g) <= allowed else "  <- fails"))
    return "\n".join(lines)


def format_seconds(seconds):
    if seconds is None:
        return "-"
    if seconds < 1:
        return "%.3f s" % seconds
    if seconds < 100:
        return "%.2f s" % seconds
    if seconds < 3600:
        return "%.1f min" % (seconds / 60.0)
    return "%.1f h" % (seconds / 3600.0)


def format_score(score, passed=True):
    """Score with 2 decimals; a passing score is never shown as 0.00."""
    if not isinstance(score, (int, float)) or not passed:
        return "0.00"
    if score < 0.005:
        return "<0.01"
    return "%.2f" % score


def format_gb(nbytes):
    if nbytes is None:
        return "-"
    if nbytes < 0.05 * GB:
        return "<0.1 GB"
    return "%.1f GB" % (nbytes / GB)


# --------------------------------------------------------------- reference fit

def fit_reference(records):
    """Least-squares fit of log t against log N over valid reference runs.

    Uses the median time per distinct N. Returns None with fewer than two
    distinct N, else a dict with alpha, log_a, ns, per_pair_s.
    """
    by_n = {}
    for rec in records:
        if rec.get("impl") != "reference" or rec.get("error"):
            continue
        n, t = rec.get("n"), rec.get("seconds")
        if isinstance(n, int) and n >= 2 and isinstance(t, (int, float)) and t > 0:
            by_n.setdefault(n, []).append(float(t))
    if len(by_n) < 2:
        return None
    ns = sorted(by_n)
    xs = [math.log(n) for n in ns]
    ys = [math.log(_median(by_n[n])) for n in ns]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    alpha = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    log_a = my - alpha * mx
    per_pair = _median([_median(by_n[n]) / pairs(n) for n in ns])
    return {"alpha": alpha, "log_a": log_a, "ns": ns, "per_pair_s": per_pair}


def predict_seconds(fit, n):
    return math.exp(fit["log_a"] + fit["alpha"] * math.log(n))


def _median(values):
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return 0.5 * (values[mid - 1] + values[mid])


# ------------------------------------------------------------------ state

def load_state(root):
    return st.load_state(root)


def save_state(root, state):
    st.save_state(root, state)


def records(state):
    """The race entries in state.records (the submissions list)."""
    recs = state.setdefault("records", {})
    recs.setdefault("submissions", [])
    return recs


# ------------------------------------------------------------- vault keys

def vault_keys(root):
    """Secrets from .vault/keys.bin (obfuscated with the pepper)."""
    key = crypto.obfuscation_key(EXERCISE, pepper(root))
    try:
        with open(os.path.join(root, ".vault", "keys.bin"), "rb") as fh:
            return packs.unseal_json(fh.read(), key)
    except (OSError, crypto.PackError) as exc:
        raise RaceError("cannot read .vault/keys.bin: %s" % exc) from exc


def open_scoring_pack(root, secret, destination):
    """Decrypt .vault/scoring.pack into `destination`."""
    try:
        with open(os.path.join(root, ".vault", "scoring.pack"), "rb") as fh:
            packs.unpack_to(fh.read(), [secret], destination)
    except OSError as exc:
        raise RaceError("cannot read .vault/scoring.pack: %s" % exc) from exc
    except crypto.PackError as exc:
        raise RaceError("cannot open .vault/scoring.pack: %s" % exc) from exc


def find_file(directory, name):
    """Path of `name` at the top of `directory`, else the first match below it."""
    direct = os.path.join(directory, name)
    if os.path.exists(direct):
        return direct
    for dirpath, _, filenames in os.walk(directory):
        if name in filenames:
            return os.path.join(dirpath, name)
    return None


# ----------------------------------------------------------- record views

def record_line(rec):
    """One-line summary of a bench record."""
    if rec.get("impl") == "submission":
        return "submission  %s  score %s  %s  %s" % (
            rec.get("division", "?"),
            format_score(rec.get("score"), rec.get("pass") is True),
            format_seconds(rec.get("seconds")), _verdict(rec))
    return "%-9s %-9s N=%-6s %9s  %6s  %s" % (
        rec.get("impl", "?"), rec.get("catalogue", "?"), rec.get("n", "?"),
        format_seconds(rec.get("seconds")), format_gb(rec.get("peak_rss_bytes")),
        _verdict(rec))


def _verdict(rec):
    if rec.get("error"):
        return "STOPPED: %s" % rec["error"]
    if rec.get("pass") is True:
        return "pass (%s)" % rec.get("division", "?")
    if rec.get("pass") is False:
        return "FAIL (%s, %d bin(s) differ)" % (
            rec.get("division", "?"),
            rec.get("fail_bins", len(rec.get("diff") or [])))
    return "not checked"
