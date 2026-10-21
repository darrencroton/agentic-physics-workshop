# Level 3: Open race

Target time: 11 minutes. Persona: `collaborator`.

## Where we are

You have cut the work and declared what "correct" means. Now go as fast as you can without losing it. The agent is a normal, evidence-first collaborator: it proposes and implements freely, runs the harness after every change and commits only verified gains.

## Race rules

- **Commit before every submit.** `./race submit` refuses if `paircount/` or `race.toml` has uncommitted changes. Humans commit `race.toml`.
- `./race submit` (a human, in the gate terminal, about 20 s) runs your entry on a **hidden** 200,000-point catalogue, then re-times a calibration entry (a numpy cell list) on the same machine. **Score = calibration time / your time**, to two decimals; about 1.0 means you matched it.
- Limits as before: 1.5 GB to pass, 2.5 GB kills, 180 s timeout.
- A failing entry **scores 0** and is logged. For a failed hidden run only the number of failing bins and the largest absolute difference are shown; `make check N=200000` gives the per-bin table on the public catalogue. Hard-coded answers fail on the hidden catalogue.
- **One process:** no `multiprocessing`. No new packages. Do not edit `reference.py` or `bench/`.
- Write each score on the whiteboard.

Prizes: **Fastest Exact**, **Fastest Toleranced**, **Best "caught it" story** (someone saw a wrong or untested claim, and the evidence showed it).

## Do this

1. Ask the agent for the next biggest win, then `make bench N=200000 IMPL=fast` and `make check N=200000` to verify it.
2. Commit, then `./race submit` in the gate terminal.
3. Repeat. Scribe: record each result in the `LOG.md` table.

**Optional: C.** Compiled code is how you beat the calibration by a large factor. The agent can write a C function and call it with `ctypes`, for example `void count(const double* pos, long n, const double* edges, int nbins, long long* out);`, compiled with `clang -O2 -shared -ffp-contract=off` into `paircount/`, with 64-bit counters. Commit `pairs.c` and `fast.py`; the `.so` is gitignored and does not block a submit. The harness times the import plus the call in a fresh process each repeat, so compile once and reuse the library. `cKDTree` is also allowed, with its `<=` convention.

## Watch for

- A C entry that fails `exact`: show the diff table. Apple's `clang` may fuse `dx*dx + dy*dy + dz*dz` into fused multiply-adds, changing rounding. `-ffp-contract=off` stops that; or declare `toleranced`, honestly.
- A speed-up with no `make bench` output, or a submit with uncommitted changes.
- Two processes or background jobs distorting a measurement.

## The gate

`./gate unlock` needs at least one submission that passed at this level. There is no graded question; a talk prompt follows, with nothing to type. Scribe: write down your best score, its division and its commit.
