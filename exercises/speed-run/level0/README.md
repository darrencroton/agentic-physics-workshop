# Speed Run

Your group's pair counter is clear, correct and pure Python. It is fine for 2,000 galaxies. The new mock catalogue has **200,000**. Make it fast, but every entry is checked against golden pair counts you cannot see, and a fast wrong answer scores zero.

So the big idea is: **measure first, and decide what "correct" means before you see any results.** For floating-point code that is a decision your group makes and writes down.

## The contract

`count_pairs(pos, edges)` returns, for each of 15 bins, the number of **unique pairs** (i < j) whose separation r falls in the half-open bin `[edge_k, edge_k+1)`.

- r is `sqrt(dx*dx + dy*dy + dz*dz)` in float64.
- The box is 100 Mpc/h on a side and **not periodic**.
- 15 log-spaced bins from 0.5 to 10 Mpc/h (16 edges, in `paircount/__init__.py`).
- Two divisions exist, `exact` and `toleranced`. You choose at Level 2; until then it is `exact`.

## Roles

- **Driver:** types the prompts in the agent window. Rotates at each gate.
- **Navigator:** owns the plan and the clock.
- **Sceptic:** owns the checks and memory estimates. Nothing is committed until the Sceptic has seen the evidence.
- **Scribe:** keeps `LOG.md`.
- **Coach:** your leader. Asks questions and fixes tooling.

Hands off the code: humans read, think and type prompts. All code changes go through the agent.

## Two windows

1. **Agent window (large):** Claude Code. Only the Driver types here. It starts in plan mode; press `Shift+Tab` until plan mode is off before asking for runs or edits.
2. **Gate terminal:** a separate terminal for `./gate` and `./race submit`. The agent never types there.

## Level 0: Measure before you touch anything (about 7 minutes)

Find out how slow the reference is, and where the time goes. The agent does the runs; you read the numbers.

1. In the agent window: `make bench N=500 IMPL=reference`, then `N=1000`, then `N=2000`.
2. `make profile` runs the reference at N = 1000 under a profiler. Which call is made most often?
3. `make fit` fits time against N and predicts the runtime at N = 200,000. **Write down the exponent and your predicted time.** The real number is the group's to measure.
4. In the gate terminal: `./gate unlock`. It asks how many unique pairs (so `math.sqrt` calls) the reference evaluates at N = 1000, then gives you a talk prompt about your prediction.

If the agent offers to optimise now, the guard will refuse edits to `fast.py`. Read the refusal aloud: it is on purpose.

## Commands

| Command | What it does |
|---|---|
| `make bench N=2000 IMPL=reference` | Times `reference` or `fast` on N points, checks the counts, records the run |
| `make check N=2000` | Correctness only; prints a per-bin diff table if counts differ |
| `make profile` / `make fit` | Profile at N = 1000 / predict the time at N = 200,000 |
| `./race status` | Level, division, recent runs, submissions |
| `./race board` | Submissions: score, division, seconds, commit |
| `./race submit` | Gate terminal, Level 3: scores your entry on the hidden catalogue |
| `./gate brief` | Shows the current level brief |
| `./gate hint` | A hint (tiers open at 0, 5 and 10 minutes) |
| `./gate unlock` | Checks your evidence and opens the next level |

Errors from `make` such as `Error 1` are not crashes: the harness output above them says what happened.
