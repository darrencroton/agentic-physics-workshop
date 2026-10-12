# Level 3: Open race

**Target time:** 11 minutes. **Persona in force:** `collaborator`.

## Where we are

At Level 2 you cut the work with a cell list or a tree, and you declared what "correct" means. The race is now about how much faster you can go without losing that. Claude becomes a normal, evidence-first collaborator: it proposes and implements freely, runs the harness after every change, and commits only verified improvements.

## Race rules

- **Commit before every submit.** `./race submit` refuses if `paircount/` or `race.toml` has uncommitted changes, so every score maps to a commit. Humans commit `race.toml`.
- `./race submit` runs your entry on a **hidden** 200,000-point catalogue (same recipe as the one you have, different seed), then runs a calibration entry on the same machine. **Score = calibration time / your time**, to two decimals. The calibration entry is a numpy cell list, so about 1.0 means you matched it. `./race submit` re-times the calibration entry on every submission, so the score is fair even if the machine was busy earlier. It takes about 20 s.
- The limits are as before: 1.5 GB to pass, 2.5 GB kills, 180 s timeout.
- A failing entry **scores 0** and is logged. For a failed hidden submission the per-bin numbers are withheld: it prints only how many bins failed and the largest absolute difference. Use `make check N=200000` for the per-bin table on the public catalogue. A hard-coded answer scores 0: the hidden catalogue is different, so copying the public counts fails.
- **One process.** The harness measures one process, so no `multiprocessing`.
- No new packages. Do not edit `reference.py` or anything in `bench/`.
- `./race submit` is typed by a human in the gate terminal. Write each score on the whiteboard.

## Prizes

**Fastest Exact.** **Fastest Toleranced.** **Best "caught it" story**: the moment someone saw a wrong or untested claim, and the evidence that showed it.

## An optional route: C

Compiled code is where beating the calibration by a large factor happens. Claude can write a C function and call it from Python with `ctypes`. A suggested shape:

```c
void count(const double* pos, long n, const double* edges, int nbins, long long* out);
```

compiled with `clang -O2 -shared -ffp-contract=off` into `paircount/`. Use 64-bit integer counters. Commit `pairs.c` and `fast.py`. The compiled `.so` is rebuilt from the source, is gitignored, and does not block `./race submit`. The harness times the import of your entry plus the call, in a fresh process for each repeat, so compile once and reuse the library (rebuild only when the source or flags change); a module that recompiles on every import pays for it in every timed run.

`cKDTree` is also allowed, but it has its own `<=` convention.

## What to watch for

- A C entry that "should" be exact but fails `exact`. Show the diff table. Apple's `clang` may fuse `dx*dx + dy*dy + dz*dz` into fused multiply-adds by default, which changes rounding. `-ffp-contract=off` switches that off; or declare `toleranced`, honestly.
- A speed-up with no `make bench` output.
- Running `./race submit` with an uncommitted change, or switching division at the last minute without writing down why.
- Two Claude processes or background jobs distorting a measurement.

## Opening the gate

In the gate terminal, run `./gate unlock`. It needs at least one submission that passed at this level. There is no graded question. The reflection (logged): your biggest wrong turn, and the evidence that showed it.

This is the last level. Scribe: write down your best score, its division and its commit.
