# Level 2: Reduce the work, defend the answer

**Target time:** 14 minutes. **Persona in force:** `coach`.

## Where we are

At Level 1 you made each pair cheaper and met the memory wall. But numpy still looks at every pair, and N = 200,000 means 2 × 10¹⁰ of them. Now look at the physics: you only need separations up to 10 Mpc/h in a 100 Mpc/h box, so most pairs are far too distant to matter. The fix is to **do less work**, not to make each step faster.

There is a **cell list**: chop the box into cells at least 10 Mpc/h across, and only compare points in the same or neighbouring cells. Ask the agent about it. `scipy.spatial.cKDTree` is another route; find out which way its `count_neighbors` treats a pair exactly at the edge (`<` or `<=`) before you trust it. `count_neighbors` also compares squared distances internally, so even with the `<=` convention handled it may never match `exact`; treat it as a route into the toleranced division.

The target: pass at **N = 200,000 in under 60 s, with peak RSS under 1.5 GB.** The harness measures both.

Reformulating the arithmetic can move a handful of pairs that sit within rounding error of a bin edge. That makes **"correct" a decision**, and it is yours.

## The two divisions

`race.toml` holds your declaration. **Humans edit it; the agent never does.**

```toml
[division]
name = "exact"
sigma_fraction = 0.0
justification = ""
```

- **exact:** every bin identical to the golden counts.
- **toleranced:** a bin passes when `|count - golden| <= sigma_fraction * sqrt(golden)`. `sigma_fraction` must be above 0 and at most 0.2, and `justification` must be a real paragraph of at least 80 characters (spaces at either end do not count). Going back to **exact** needs `sigma_fraction = 0.0`; the justification can then be empty or left as it was.

`sqrt(golden)` is a nominal Poisson yardstick, adopted for this exercise: if pair counts were Poisson, a bin holding 2,500 pairs would scatter by about 50, and one holding 100 by about 10. Real pair counts in a clustered catalogue scatter more than that, because pairs share galaxies and neighbouring bins are correlated, so this criterion is conservative. It is a yardstick, not the bin's true uncertainty. For example, with `sigma_fraction = f`, a bin holding 2,500 allows a difference of 50 f. **Which f, if any, is your call.** Write the reason down.

## What to do

1. Ask the agent for a faster algorithm in `fast.py`. Test it at `N=20000` first (cheap, and the golden counts exist), then run `make bench N=200000 IMPL=fast`. A slow first attempt at 200,000 can burn the full 180 s timeout.
2. If counts differ, the agent shows the **diff table** (bin, edges, golden, yours, difference, allowed) and stops. Read it: which bins, by how many, and why?
3. Decide: match the reference arithmetic exactly, or declare `toleranced` in `race.toml` with a justification (also in `LOG.md`). Do it before you look for a run that passes.
4. Run the bench again.

## What to watch for

- `np.allclose`, or "it is just floating-point error" with no table. Demand the table.
- The agent suggesting a number for `sigma_fraction`. The group decides.
- Evidence goes stale: the gate accepts only a run made with the **current** `fast.py` and `race.toml`. Edit either and you must re-run.

## Opening the gate

In the gate terminal, run `./gate unlock`. The question: **Golden counts [100, 1000000]; yours [101, 1000010]; declared sigma_fraction 0.05. Which bins pass? (a) both, (b) the first only, (c) the second only, (d) neither.** Do the arithmetic for each bin.

Reflection (logged): which division you entered, and what evidence decided it.
