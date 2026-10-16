# Speed Run (Exercise B): Frozen Build Contract

Version 2, after the Codex gpt-6.1-sol brainstorm and the measurement probe (2026-10-12). This file is the contract every build task works from. `docs/02-speed-run.md` is the pedagogy; `BUILD-SPEC.md` the engineering spec; `exercises/tdd-ladder/` the worked example. Deviations from `docs/02` are listed in section 11 and go to `docs/DECISIONS.md`.

## 1. Measured facts (M1 Max, Python 3.13, numpy 2.3, Apple clang 21)

| Measurement | Value |
|---|---|
| Pure-Python double loop | ~110 ns per pair; N = 2000 in 0.22 s; exponent 2.0; **N = 200k ≈ 37 min** (not hours) |
| Pairs with r < 10 in a 100 box, N = 200k | 7.5 × 10⁷ (uniform, non-periodic); r < 20: 5.3 × 10⁸ |
| numpy cell list at 200k, side-10 cells | **11.5 s** at r_max = 10; 77 s at r_max = 20; 50k → 200k exponent 1.89 (the hidden calibration counter built later does it in ~4 s) |
| numpy brute force at 20k | full N×N: 9.4 s, **10.2 GB** peak; chunked (2000 rows): 2.7 s, 3.3 GB |
| C brute force at 200k | 24.6 s (either contraction setting) |
| FMA | Apple clang `-O2` default emits `fmadd` for `dx*dx+dy*dy+dz*dz`; 0.4 % of pairs within ±8 ulp of an edge change bin vs `-ffp-contract=off`; numpy equals the non-FMA build exactly |
| `sum(d*d) < e*e` (no sqrt) vs `sqrt(...) < e` | 1.2–1.7 % of near-edge pairs disagree. `r*r < e*e` after the sqrt: 0 disagreements |
| `np.histogram` | half-open interior bins; **closed last edge** only |
| `cKDTree.count_neighbors` | `≤ r` (cumulative); `(r_prev, r]` bins |

Consequences: r_max = 10 (15 log bins, 16 edges from 0.5 to 10); the toleranced division must be stated in counts, not `rtol = 1e-6`; the exponent gate is dropped; memory is enforced by the harness, not by hoping the laptop swaps.

## 2. Levels and timing (45 min = 1 start + 7 + 10 + 14 + 11 + 2 contingency)

| L | Title | Min | Persona | Machine check (crypto script reads the signed bench log) | Graded question (one) | Reflection (logged) |
|---|---|---|---|---|---|---|
| 0 | Measure before you touch anything | 7 | coach | ≥ 3 valid `reference` records with distinct N in [500, 4000], recorded at level 0; ≥ 1 `profile` record | "How many unique pairs, and so `math.sqrt` calls, does the reference evaluate at N = 1000?" numeric-log, 4 decimals, lo 499500, hi 500000 (about 499,402 to 500,092 accepted) | "From your fit, the reference's predicted runtime at N = 200,000 (in minutes), and how you got it:" |
| 1 | Vectorise, and survive the memory wall | 10 | coach | a `fast` record at `mock_20k`, recorded at level 1, pass in division **exact**, seconds < 10 (the untouched pure-Python entry does 20k in ~22 s), peak RSS < 1.5 GB, `source_hash` equal to the current `paircount/` tree | "How many gigabytes is ONE 200,000 × 200,000 float64 matrix?" numeric, decimals 0, accept 298–320 | "Your memory estimate before the 20k run, and what the harness measured:" |
| 2 | Reduce the work, defend the answer | 14 | coach | a `fast` record at `mock_200k`, recorded at level 2, pass in the declared division, seconds < 60, peak RSS < 1.5 GB, `source_hash` and `toml_hash` current | "Golden counts [100, 1000000]; yours [101, 1000010]; declared sigma_fraction 0.05. Which bins pass? (a) both, (b) the first only, (c) the second only, (d) neither. Your answer (a-d):" choice, accept c ("c - the second only" also resolves to c) | "Which division did you enter, and what evidence decided it?" |
| 3 | Open race | 11 | collaborator | `verified`, condition `race.submitted_ok`: ≥ 1 submission with pass = true at level 3 | — | "Your biggest wrong turn, and the evidence that showed it:" |

Level 3 is the last level, so its verified gate needs no secret. Levels 0–2 are `crypto`; the check scripts live in `.gatekit/racetool/checks/levelN.py` (unreadable by Claude), print diagnostics to stderr and exit 1 on failure, and on success print exactly `{"level": N, "ok": true}` (sorted keys, no spaces beyond JSON default of `json.dumps(obj, sort_keys=True)`). Because that output is fixed, the slot secret is effectively the human answer; this is the documented honest limit.

## 3. Repo layout (`dist/speed-run/`)

```text
README.md  CLAUDE.md  LOG.md  Makefile  requirements.txt  race.toml  .gitignore
gate  race  preflight
paircount/__init__.py       EDGES (16 float64 literals), BOX = 100.0, load_catalogue(name) -> (N,3) float64
paircount/reference.py      count_pairs(pos, edges) -> np.ndarray[int64]; pure Python; frozen
paircount/fast.py           starts as a byte-identical copy of reference.py (apart from the docstring title); editable from Level 1
bench/harness.py            bench | check | profile | fit  (frozen; run by make; spawns a worker; writes the signed log)
data/mock_2k.npy  mock_20k.npy  mock_200k.npy   (exactly 2000 / 20000 / 200000 rows, float64, C-order)
.claude/  .gatekit/  .vault/  .workshop/         as in the TDD Ladder
.gatekit/racetool/          tool package (below), golden.json (public catalogues), checks/levelN.py, _pepper.py (build)
.vault/scoring.pack         hidden/: mock_hidden_200k.npy, golden_hidden.json, calibration.py, solutions/
```

`results/` is not used. `xi/`, randoms and the 50k catalogue are cut.

## 4. Interfaces (frozen)

### 4.1 `paircount`

```python
# paircount/__init__.py
BOX = 100.0
EDGES = (0.5, ..., 10.0)          # 16 float64 literals written by make_data.py (repr), never recomputed
def load_catalogue(name): ...      # name in {"mock_2k", "mock_20k", "mock_200k"} or a path; returns np.ndarray (N, 3) float64
```

`count_pairs(pos, edges)`: `pos` is an `(N, 3)` float64 array, `edges` a 1-D ascending float64 array (length 16). Returns an int64 array of length 15: the number of unique pairs `i < j` with `edges[k] <= r < edges[k+1]`, where `r = math.sqrt(dx*dx + dy*dy + dz*dz)` in float64 and `d = pos[i] - pos[j]`. Non-periodic. The reference computes `r` (one `math.sqrt` per unique pair, before any range test, so N = 1000 gives exactly 499,500 calls), then `k = bisect.bisect_right(edges, r) - 1` and counts only `0 <= k < 15`. It iterates over `pos.tolist()` rows.

### 4.2 `race.toml` (humans edit; frozen for Claude at every level)

```toml
# What "correct" means for your entry. Humans edit this file; Claude never does.
# exact: every bin identical to the golden counts.
# toleranced: a bin passes when |count - golden| <= sigma_fraction * sqrt(golden).
#   sigma_fraction must be > 0 and <= 0.2, and justification must be a real paragraph.
[division]
name = "exact"
sigma_fraction = 0.0
justification = ""
```

Validation (harness and tool, shared code): `name` in {exact, toleranced}; toleranced needs `0 < sigma_fraction <= 0.2` and `len(justification.strip()) >= 80`; an invalid file is a refusal with the reason, never a silent fallback. Parsed with `tomllib` **inside the venv worker only** (the tool package must import on Python 3.9).

### 4.3 Bench log: `.workshop/race/bench.jsonl`

One JSON object per line, written only by `bench/harness.py` (and `race submit` for submissions, see 4.5). Fields:

| Field | Meaning |
|---|---|
| `ts` | ISO-8601 UTC |
| `level` | state level when recorded |
| `impl` | `reference`, `fast` or `profile` |
| `catalogue` | `mock_2k`, `mock_20k`, `mock_200k`, `hidden` |
| `n` | rows used (`--n` takes the first n rows of the catalogue; `reference` is refused for n > 4000 with a message that quotes the extrapolated time) |
| `repeats`, `seconds`, `seconds_all` | median and the list (repeat policy: 3 runs if the first run < 10 s, else 1) |
| `peak_rss_bytes` | max(worker `ru_maxrss`, polled `ps` RSS) |
| `division`, `sigma_fraction` | from `race.toml` at run time |
| `pass` | bool; comparison against golden under the division |
| `diff` | list of `[bin, golden, got]` for bins that differ (all of them; ≤ 15) |
| `sqrt_calls` | profile records only: `math.sqrt` ncalls from cProfile |
| `source_hash` | sha256 over the `paircount/` tree (sorted relative paths + bytes; `__pycache__`, `*.so`, `*.dylib`, `*.o` excluded; `.c` included). Taken before and after the run; a change marks the record `error` and `pass: null`. |
| `toml_hash` | sha256 of `race.toml` bytes |
| `head` | `git rev-parse HEAD` or null |
| `sig` | hex HMAC-SHA256(pepper, canonical JSON of all other fields) |

Canonical JSON = `json.dumps(obj, sort_keys=True, separators=(",", ":"))`. The pepper is `.gatekit/racetool/_pepper.py` (written by the build; the same mechanism tddtool uses). Records with a bad signature are ignored by checks and flagged by `./race log`. Runs made with tool-only options (`--golden`, `--label`, `--impl-file`, `--json-out`, a catalogue path) are never recorded.

### 4.4 Harness (`bench/harness.py`, runs under `.venv/bin/python`)

```text
harness.py bench   --impl fast|reference --n N [--catalogue mock_2k|mock_20k|mock_200k] [--no-record]
harness.py check   --n N [--catalogue ...]               correctness only, prints the diff table
harness.py profile                                       reference at N = 1000 under cProfile; prints top 15 by tottime and the math.sqrt line; records sqrt_calls
harness.py fit                                           least-squares exponent of log t vs log N over the reference records; prints alpha and the extrapolated time at 200k in minutes
```

Execution: the parent spawns a **worker** (`harness.py _worker <json-args>`) under the same interpreter; each repeat runs in a fresh worker that loads the catalogue, then times the import of `paircount.<impl>` plus the `count_pairs` call (`time.perf_counter`), and writes `{counts, seconds, ru_maxrss_bytes}` to a temp file. The parent polls `ps -o rss= -p <pid>` every 0.1 s, kills the worker above `RACE_RSS_CAP_GB` (default 2.5, cannot be raised) or after `RACE_TIMEOUT_S` (default 180, cannot be raised), and reports which limit was hit in plain words ("killed: resident memory passed 2.5 GB; estimate before you run"). Peak RSS is reported in GB with one decimal. Every bench run also checks correctness (no separate check needed). The catalogue is always the matching file for `--n` unless `--catalogue` is given: n ≤ 2000 → `mock_2k`, ≤ 20000 → `mock_20k`, else `mock_200k`. Output after a run: one line per field that matters, then the diff table when counts differ (bin, edges, golden, yours, difference, allowed), then `recorded as ... (level N)`.

`Makefile`: `bench` (`N=2000 IMPL=fast`), `check` (`N=2000`), `profile`, `fit`, `log` (`./race log`), `status`. `PY ?= .venv/bin/python`.

### 4.5 `race` tool (`racetool/`, stdlib only at import time, Python 3.9-safe; numerical work in venv subprocesses)

| Command | TTY | Behaviour |
|---|---|---|
| `status` | No | Level, division, last three records, submissions |
| `log` | No | The bench log as a table; bad signatures flagged |
| `board` | No | Submissions: score, division, seconds, commit, time |
| `submit` | Yes | Refuses unless `paircount/**` and `race.toml` are committed (`git status --porcelain -- paircount race.toml` empty) and `race.toml` is valid. Decrypts `scoring.pack` to a temp dir (deleted afterwards, even on error). Runs the entrant on the hidden catalogue through the harness worker (same limits: 1.5 GB ceiling to pass, 2.5 GB cap, 180 s timeout), then the calibration counter (re-timed on every submit, with the repeat policy). Score = calibration seconds / entrant seconds, 2 decimals; the calibration is re-timed on every submit. A failing entry scores 0 and prints only the number of failing bins and the largest absolute difference (never the hidden golden values), pointing at `make check N=200000` for the public per-bin table. Appends a submission record to `state.records.submissions` (`ts, level, commit, division, sigma_fraction, pass, seconds, calibration_seconds, score, peak_rss_bytes, reason`) and a `submission` line to the bench log. Prints the board line to copy to the whiteboard. |
| `install-solution <level>` | Yes + master passphrase | Copies `hidden/solutions/level<N>/` over `paircount/` (fast.py and any `.c`), prints what it did, logs to `LOG.md`. Facilitator fallback for a stuck group. |

Exports from `racetool/__init__.py` as gatekit expects: `conditions = {"submitted_ok": ...}`, `status_lines`, `teacher_context_extra` (one line: current division and the last bench result), `on_reset` (removes `.workshop/race/`). No `validators`, `post_unlock` or `level_secret` are needed. `teacher_context_extra` must be cheap and never raise.

### 4.6 Manifest

```json
{
  "exercise": "speed-run", "title": "Speed Run", "tool": "racetool",
  "models": {"default": "haiku", "allowed": ["haiku"]},
  "human_only": {"race": ["submit", "install-solution"]},
  "levels": [
    {"id": 0, "title": "Measure before you touch anything", "persona": "coach", "target_minutes": 7,
     "gate": {"type": "crypto", "check": ".gatekit/racetool/checks/level0.py", "python": "venv", "timeout": 120,
              "questions": [{"id": "pairs", "kind": "numeric-log", "decimals": 4, "lo": 499500, "hi": 500000,
                             "prompt": "How many unique pairs, and so math.sqrt calls, does the reference evaluate at N = 1000?"}],
              "reflection": "From your fit, the reference's predicted runtime at N = 200,000 (in minutes), and how you got it:"}},
    {"id": 1, "title": "Vectorise, and survive the memory wall", "persona": "coach", "target_minutes": 10,
     "gate": {"type": "crypto", "check": ".gatekit/racetool/checks/level1.py", "python": "venv", "timeout": 120,
              "questions": [{"id": "matrix_gb", "kind": "numeric", "decimals": 0, "lo": 298, "hi": 320,
                             "prompt": "How many gigabytes is ONE 200,000 x 200,000 float64 matrix?"}],
              "reflection": "Your memory estimate before the 20k run, and what the harness measured:"}},
    {"id": 2, "title": "Reduce the work, defend the answer", "persona": "coach", "target_minutes": 14,
     "gate": {"type": "crypto", "check": ".gatekit/racetool/checks/level2.py", "python": "venv", "timeout": 120,
              "questions": [{"id": "perbin", "kind": "choice", "accept": ["c"],
                             "prompt": "Golden counts [100, 1000000]; yours [101, 1000010]; declared sigma_fraction 0.05. Which bins pass? (a) both, (b) the first only, (c) the second only, (d) neither. Your answer (a-d):"}],
              "reflection": "Which division did you enter, and what evidence decided it?"}},
    {"id": 3, "title": "Open race", "persona": "collaborator", "target_minutes": 11,
     "gate": {"type": "verified", "condition": "race.submitted_ok",
              "reflection": "Your biggest wrong turn, and the evidence that showed it:"}}
  ]
}
```

`answers.json` holds the token for levels 0, 1, 2: `sha256` of the canonical check output (`gatekit.crypto.canonical_token` applied to `json.dumps({"level": N, "ok": True}, sort_keys=True) + "\n"`; confirm the exact canonicalisation in `crypto.py` and generate the file with a script, `make_answers.py`, rather than by hand).

### 4.7 Guards

| Level | `editable` | `frozen` |
|---|---|---|
| 0 | `LOG.md` | `paircount/**`, `race.toml`, `bench/**` |
| 1–3 | `paircount/**`, `LOG.md` | `paircount/reference.py`, `paircount/__init__.py`, `race.toml`, `bench/**` |

Global (gatekit): `data/` and the launchers are frozen; `.vault`, `.workshop`, `.gatekit`, `.claude`, `.git` are secret. `race` is added to `FROZEN_FILES`. Human-only `race` subcommands come from the manifest (`human_only`) for both the guard regex and the rendered `settings.json` deny list; the hard-coded `tdd` list stays as the fallback when a manifest has no `human_only` field.

## 5. Data and traps (`make_data.py`, committed, seeded, deterministic)

- **Base mock (per catalogue, independent seeds; hidden catalogue uses its own seed):** Neyman–Scott in a 100 Mpc/h box, non-periodic. Parents: Poisson(mean = N/100) uniform in the box. Satellites: for each parent Poisson(mean 70 × N/200000 … choose so that clustered points ≈ 0.7 N), Gaussian σ = 1.5 Mpc/h, redrawn until inside the box. Background: uniform, to make up the total. Base points = N − 2 × (number of planted pairs), so every catalogue has exactly N rows after planting. Rows shuffled.
- **Planted pairs** (`n_pairs` per kind: 2k → 8, 20k → 20, 200k and hidden → 50), each pair's two points at a random base position in the box, oriented so the pair is inside the box; kept only after verifying the complete stored-coordinate calculation:
  1. **exact-edge:** `r == edges[k]` exactly under the reference computation, for k spread over the edges, plus **one pair with `r == edges[15]` (r_max)** per catalogue. (Search: random axis-aligned or generic directions and bases until `math.sqrt(fl(dx*dx+dy*dy+dz*dz)) == e`; report the yield.)
  2. **sum-of-squares:** `sqrt(s) < e` disagrees with `s < e*e` where `s = fl(dx*dx+dy*dy+dz*dz)`.
  3. **FMA:** the C computation with clang default contraction disagrees with `-ffp-contract=off` (build a tiny helper with ctypes during generation; if clang is missing, fail loudly).
- **Golden counts:** `reference.count_pairs` directly at 2k and 20k (≈ 25 s). At 200k and hidden: the strict numpy cell list (`hidden/calibration.py`), which must equal the reference at 2k and 20k bit for bit, **cross-checked** by an independent C brute-force counter compiled with `-ffp-contract=off` (`hidden/verify/brute.c`, ≈ 25 s per 200k catalogue). Public goldens go to `workshop/racetool/golden.json` (`{"mock_2k": [...], ...}` with `edges` repeated), hidden to `hidden/golden_hidden.json`.
- **Verification (`hidden/verify_assets.py`, run by the self-test):** for every catalogue, the reference (2k, 20k) or both fast counters (200k, hidden) reproduce golden; each wrong-semantics variant changes ≥ 1 bin in aggregate (exact fails): (i) `s < e*e`, (ii) `≤` convention (`cKDTree.count_neighbors` with `cumulative=False`, and an emulation without scipy), (iii) `np.histogram` of all `r` (closed last edge), (iv) C default contraction; and each of (i)–(iv) passes the toleranced division at `sigma_fraction = 0.1` in every bin on every catalogue. Prints a table of per-bin movements. If (iv) cannot be made to fire on this clang, say so loudly; do not fake it.

## 6. Hidden assets (`hidden/` → `scoring.pack`)

`mock_hidden_200k.npy`, `golden_hidden.json`, `calibration.py` (strict numpy cell list; also the Level 2 solution), `solutions/level1/fast.py` (chunked numpy, exact, < 1.5 GB), `solutions/level2/fast.py` (= calibration), `solutions/level3/fast.py` + `pairs.c` (cell list in C compiled on first import with `clang -O2 -ffp-contract=off -shared` to `paircount/_pairs_<hash>.so` (hash of flags and source), loaded with ctypes, int64 counters), `verify/brute.c`.

## 7. Self-test (`selftest/run.py`, pty-driven like the TDD one; `--skip-build`, `--dist`)

1. Build; `./preflight` passes (venv present).
2. `hidden/verify_assets.py` passes (section 5) and prints the straddler table and timings.
3. L0: `gate unlock` refused with "no bench runs"; `make bench N=500/1000/2000 IMPL=reference`; `make profile`; `make fit` prints an exponent in [1.8, 2.2]; wrong answer (N(N+1)/2 = 500500) rejected; "N(N-1)/2 = 499,500" unlocks.
4. L1: install `samples/l1_naive_matrix/fast.py`; `make bench N=20000` is killed by the cap (run with `RACE_RSS_CAP_GB=2.5`) and the record says so; install `samples/l1_chunked/fast.py`; passes exact, < 10 s, < 1.5 GB; stale-evidence check: edit `fast.py` after the run → unlock refused ("fast.py changed since that run"); restore; wrong GB rejected; 320 unlocks.
5. L2: `samples/l2_sumsq/fast.py` (cell list comparing `s < e*e`) → exact fails with a diff table; set `race.toml` toleranced with sigma 0.1 and a justification → passes; an invalid toml (sigma 0.5) is refused; `samples/l2_celllist/fast.py` (= the solution) → exact passes in < 60 s; answer (c) unlocks (wrong letter rejected first).
6. L3: `submit` refuses on a dirty `paircount/`; commit; `samples/l3_c_default/` (C with default contraction) → fails exact on the hidden catalogue, scores 0, board shows it; `samples/l3_c_off/` → passes, score > 1; `gate unlock` completes.
7. `install-solution 2 --master` works; `skip --master` works at some level; `gate reset` + `git reset --hard start` leaves a clean level 0. Report timings: bench at 200k with the cell list, submit wall time.

## 8. Personas and briefs: the verbosity rule

Every `persona.txt` (coach at 0–2, collaborator at 3) keeps the TDD-style rules (show the command and output; never invent numbers; never change a check or tolerance; never edit frozen files; never run human-only commands; never read secret dirs; never install) and adds:

> Explain as you go. Before each experiment or code change, say in two or three sentences what you are about to do, why, and what the result will tell us. After a run, say in one or two sentences what the number means for the next step. Define a term the first time you use it (RSS, ulp, cell list, scaling exponent). Keep it short: no essays, and no menus of options unless asked.

Level-specific lines: L0 "measurement only; do not edit `fast.py` (the guard will refuse)"; L1 "state the memory estimate with the arithmetic before any run at N ≥ 20000; the group confirms it first"; L2 "when counts differ from golden, show the diff table and stop; the humans decide the division in `race.toml`; never suggest a tolerance value"; L3 "propose and implement freely, run the harness after every change, commit only verified improvements, one process only (the harness measures one process)".

Each `BRIEF.md` opens with **Where we are** (what the last level showed, why this level exists, the lesson), explains terms on first use, then the numbered steps, "what to watch for", and "opening the gate". Under ~450 words. `README.md` (Level 0) carries the story, the correctness contract, roles, two windows, Level 0 steps and the command table. Level 3's brief includes the race rules, the ctypes ABI sketch (`void count(const double* pos, long n, const double* edges, int nbins, long long* out)`, `-O2 -shared -ffp-contract=off`) as an optional route, and a note that `cKDTree` is allowed but has its own convention.

## 9. Hints (three tiers per level: 0, 5, 10 min)

L0: nudge "what does the profile say the loop is spending its time on?"; direction "N(N−1)/2 pairs; count them for N = 1000"; near "499,500; the fit's exponent is 2, so 200k is (200000/2000)² × t(2000)". L1: "estimate memory before running"; "20000² × 8 bytes per temporary; how many temporaries?"; "process rows in chunks of a few hundred (2000-row chunks peak at 3.3 GB at 20k); one 200k matrix is 200000² × 8 = 320 GB". L2: "the largest r you need is 10 in a 100 box: most pairs can be skipped before any distance"; "grid the box into cells of side ≥ 10; compare only neighbouring cells; or cKDTree (read its ≤ convention)"; "the diff table shows a few counts moving between adjacent bins: pairs within an ulp of an edge; match the reference arithmetic (sqrt then compare) or declare toleranced with a Poisson-error justification". L3: "C via ctypes: the arithmetic contracts to FMA by default; compare with -ffp-contract=off"; "commit before every submit"; "the calibration is a numpy cell list that does 200k in a few seconds; beating it clearly means compiled code (C cell list ≈ 1.5 s)".

## 10. Build tasks (disjoint file sets)

| Task | Files | Model |
|---|---|---|
| A gatekit | `gatekit/gatekit/hooklib.py`, `templates/.claude/hooks/guard.py`, `templates/.claude/settings.json`, `tools/build.py`, `gatekit/tests/*`, `gatekit/README.md` | sonnet |
| B data & numerics | `exercises/speed-run/make_data.py`, `level0/paircount/*`, `level0/data/*`, `workshop/racetool/golden.json`, `hidden/**` | opus |
| C harness & tool | `level0/bench/harness.py`, `level0/Makefile`, `level0/race.toml`, `level0/requirements.txt`, `level0/.gitignore` additions, `workshop/race`, `workshop/racetool/*.py`, `workshop/racetool/checks/*`, `workshop/preflight_extra.py`, `make_answers.py`, `answers.json` | opus |
| D content | `manifest.json`, `level0/README.md`, `level0/LOG.md`, `levels/0..3/*`, `workshop/CLAUDE.workshop.md`, `FACILITATOR-WALKTHROUGH.md` | sonnet |
| E self-test | `selftest/run.py`, `selftest/samples/**` | after A–D |

## 11. Deviations from `docs/02` (to `docs/DECISIONS.md`)

1. Four levels, not five: baseline and profile merged (gate overhead; 45-minute budget with contingency).
2. r_max = 10 Mpc/h, 15 log bins from 0.5 (measured: numpy cell list 11.5 s vs 77 s at r_max = 20).
3. Toleranced division is `|Δ| ≤ sigma_fraction × sqrt(golden)` per bin, sigma ≤ 0.2 (the doc's `rtol ≤ 1e-6` cannot pass a one-count shift unless the bin holds ≥ 10⁶ counts; integer counts need an absolute criterion with a physical basis: the Poisson error).
4. Level 2 graded question is the per-bin tolerance question, not the scaling exponent (a cell list at fixed box and r_max is still ~N²; measured 1.89).
5. Level 1 is exact-only; divisions are introduced at Level 2.
6. Golden counts are tool-private (`.gatekit/racetool/golden.json`), not in `data/` (otherwise readable and returnable).
7. `./race submit` benchmarks on a hidden 200k catalogue (same recipe, different seed); hard-coded answers score 0.
8. Memory wall enforced by the harness (1.5 GB ceiling to pass; 2.5 GB hard kill), not by the laptop.
9. ξ(r), randoms, the 50k catalogue and the "fastest per line changed" prize are cut; multiprocessing is out of the supported race (single-process measurement).
10. Bench records carry source and declaration fingerprints; gates reject stale evidence.
11. Facilitator fallback is `./race install-solution <level>` (master passphrase).
12. Pure-Python baseline at 200k is ~40 minutes on Apple silicon, not hours; briefs say "about an hour on a laptop" and the reflection asks for the group's own extrapolation.
