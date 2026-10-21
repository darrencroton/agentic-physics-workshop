# Level 1: Vectorise, and survive the memory wall

Target time: 10 minutes. Persona: `coach`.

## Where we are

The reference costs one `sqrt` per pair. Numpy can do many at once (**vectorisation**), but an N × N distance array is enormous: the harness watches peak **resident memory (RSS)**, under **1.5 GB** to pass, killed at **2.5 GB**. `fast.py` is now open, and this level is **exact-only**: counts must match the golden counts bin for bin.

## Do this

1. Ask the agent to rewrite `count_pairs` in `paircount/fast.py` with numpy, keeping the reference arithmetic: `sqrt` of the sum of squares in float64, half-open bins, i < j.
2. **Before any run at N = 20000,** the Sceptic asks for a memory estimate with the arithmetic (bytes per temporary array, how many alive at once). Check it, and write it in `LOG.md`.
3. Check small first: `make check N=2000`.
4. Then `make bench N=20000 IMPL=fast`. It must pass `exact`, take under 10 s and stay under 1.5 GB. The untouched pure-Python version takes about 20 s, so the limit forces a real change.
5. If the harness kills the run, that is the lesson. Compare its number with your estimate, then ask the agent to process **blocks of rows** (chunking).

Commit each verified gain.

## Watch for

- A 20,000 run with no estimate. Stop and ask for it.
- A diff table: show it to the group first. A pair exactly on a bin edge can move if the comparison is written differently from the reference.
- A speed-up claimed with no `make bench` output.

## The gate

`./gate unlock` needs a `fast` run at N = 20000 made with the current `fast.py` that passed `exact`, took under 10 s and peaked under 1.5 GB. Edit `fast.py` after the run and you must run it again. The question: **How many gigabytes is ONE 200,000 × 200,000 float64 matrix?** Work it out. A talk prompt follows, with nothing to type.
