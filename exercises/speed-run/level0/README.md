# Speed Run

Your group's pair counter is clear, correct and pure Python. It is fine for 2,000 galaxies. The new mock catalogue has **200,000**. Make it fast, but every entry is checked against golden pair counts you cannot see, and a fast wrong answer scores zero.

So the big idea is: **measure first, and decide what "correct" means before you see any results.** For floating-point code that is a decision your group makes and writes down.

## How it runs

| Level | | Target |
|---|---|---|
| 0 | Measure before you touch anything | 7 minutes |
| 1 | Vectorise, and survive the memory wall | 10 minutes |
| 2 | Reduce the work, defend the answer | 14 minutes |
| 3 | Open race | 11 minutes |

A gate checks each level before the next one opens. **`BRIEF.md` is your running sheet**: what to do now, what to watch for, and what the gate needs. It changes at every unlock. Read this page once, then open `BRIEF.md` (or run `./gate brief`).

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

1. **Agent window (large):** Claude Code. Only the Driver types here.
2. **Gate terminal:** a separate terminal for `./gate` and `./race submit`. The agent never types there.

## Your files

| File | What it's for |
|---|---|
| `BRIEF.md` | What to do at this level |
| `LOG.md` | The Scribe's log, with a table for your submissions |
| `paircount/fast.py` | Your entry. `paircount/reference.py` is the slow, correct original. |
| `race.toml` | Your division, declared at Level 2. Humans edit it; the agent never does. |
| `bench/`, `data/` | The harness and the mock catalogues. Frozen. |
| `AGENTS.md`, `CLAUDE.md` | The agent's instructions. You don't need to read them. |

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
