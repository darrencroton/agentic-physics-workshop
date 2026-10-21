# Level 2: Reduce the work, defend the answer

Target time: 14 minutes. Persona: `coach`.

## Where we are

Numpy still looks at every pair: 2 × 10¹⁰ at N = 200,000. But you only need separations up to 10 Mpc/h in a 100 Mpc/h box, so most pairs can be skipped. Ask the agent about a **cell list** (cells at least 10 Mpc/h across; compare only the same and neighbouring cells). `cKDTree` is another route, but it compares squared distances, so expect the toleranced division.

The target: **N = 200,000 in under 60 s, peak RSS under 1.5 GB.** Reformulated arithmetic can move a few pairs that sit within rounding error of a bin edge. That makes "correct" a decision, and it is yours.

## The two divisions

`race.toml` holds your declaration. **Humans edit it; the agent never does.**

```toml
[division]
name = "exact"
sigma_fraction = 0.0
justification = ""
```

- **exact:** every bin identical to the golden counts.
- **toleranced:** a bin passes when `|count - golden| <= sigma_fraction * sqrt(golden)`. `sigma_fraction` must be above 0 and at most 0.2, and `justification` a real paragraph of at least 80 characters. Going back to exact needs `sigma_fraction = 0.0`.

`sqrt(golden)` is a nominal Poisson yardstick: a bin holding 2,500 pairs would scatter by about 50, one holding 100 by about 10. Real pair counts scatter more, so it is conservative, but it is a yardstick, not the bin's true uncertainty. With `sigma_fraction = f`, a bin of 2,500 allows a difference of 50 f. **Which f, if any, is your call.**

## Do this

1. Ask the agent for a faster algorithm in `fast.py`. Test at `N=20000` first, then `make bench N=200000 IMPL=fast`. A slow first attempt at 200,000 can burn the full 180 s timeout.
2. If counts differ, the agent shows the **diff table** (bin, edges, golden, yours, difference, allowed) and stops. Read it: which bins, by how many, and why?
3. Decide: match the reference arithmetic exactly, or declare `toleranced` in `race.toml` with a justification (also in `LOG.md`). Do it before you hunt for a passing run.
4. Run the bench again.

## Watch for

- `np.allclose`, or "it is just floating-point error" with no table. Demand the table.
- The agent suggesting a `sigma_fraction`. The group decides.
- Stale evidence: the gate accepts only a run made with the **current** `fast.py` and `race.toml`.

## The gate

`./gate unlock`. The question: **Golden counts [100, 1000000]; yours [101, 1000010]; declared sigma_fraction 0.05. Which bins pass? (a) both, (b) the first only, (c) the second only, (d) neither.** Do the arithmetic for each bin. A talk prompt follows, with nothing to type.
