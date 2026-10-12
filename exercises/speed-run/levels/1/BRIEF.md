# Level 1: Vectorise, and survive the memory wall

**Target time:** 10 minutes. **Persona in force:** `coach`.

## Where we are

At Level 0 you measured the reference: time grows as N squared, the profile showed one `math.sqrt` per pair, and the fit predicted far too long at N = 200,000. The slow part is the Python loop, so the first cure is to let numpy do the arithmetic for many pairs at once. That is **vectorisation**.

Vectorisation trades time for memory: an N × N array of distances is fast to compute but enormous. So this level is about **estimating memory before you run anything**. The harness watches the **resident set size (RSS)**, the physical memory the process is really using. To pass, peak RSS must stay under **1.5 GB**. Past **2.5 GB** the harness kills the run and says so.

`fast.py` is now open for editing. This level is **exact-only**: `race.toml` stays on `exact`, and your counts must match the golden counts bin for bin.

## What to do

1. Ask Claude to rewrite `count_pairs` in `paircount/fast.py` with numpy, keeping the same arithmetic as the reference: `sqrt` of the sum of squares in float64, half-open bins, pairs with i < j.
2. **Before any run at N = 20000,** the Sceptic asks Claude for a memory estimate with the arithmetic: how many bytes is one temporary array, and how many temporaries are alive at once? Check it yourselves. Write the estimate in `LOG.md`.
3. Check small first: `make check N=2000`.
4. Then the real run: `make bench N=20000 IMPL=fast`. It must pass `exact`, take under 10 s and stay under 1.5 GB. (The untouched pure-Python version takes about 20 s here, so the limit forces a real change.)
5. If the harness kills the run, that is the lesson. Compare what it measured with your estimate, and ask Claude to process the points in blocks of rows (**chunking**).

## What to watch for

- A run at 20,000 launched with no estimate. Stop the Driver and ask for it.
- A diff table after a run: show it to the group before anything changes. A pair that lands exactly on an edge can move bin if the comparison is written differently from the reference.
- A speed-up claimed with no `make bench` output next to it.

Commit each verified gain.

## Opening the gate

In the gate terminal, run `./gate unlock`. It looks for a `fast` run at N = 20000 made with the current `fast.py` that passed `exact`, ran under 10 s and peaked under 1.5 GB. If you edit `fast.py` after that run, run it again.

The question: **How many gigabytes is ONE 200,000 × 200,000 float64 matrix?** Work it out; do not guess.

Then the reflection (logged, not graded): your memory estimate before the 20k run, and what the harness measured.
