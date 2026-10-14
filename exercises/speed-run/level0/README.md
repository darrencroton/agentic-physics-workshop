# Speed Run

## The story

Your group measures galaxy clustering with the Landy–Szalay estimator. The pair counter at its heart was written years ago as a clear, obviously correct pure-Python double loop. It is fine for 2,000 galaxies. The new mock catalogue has **200,000**.

Make it fast. Every entry is checked against **golden pair counts** that you cannot see, and a fast wrong answer scores zero.

The big idea: **measure first, and decide what "correct" means before you see any results.** Speed only counts if the answer is right, and "right" for floating-point code is a decision your group makes and writes down.

## The correctness contract

`count_pairs(pos, edges)` returns, for each of 15 bins, the number of **unique pairs** (i < j) whose separation r falls in the half-open bin `[edge_k, edge_k+1)`.

- r is `sqrt(dx*dx + dy*dy + dz*dz)` in float64.
- The box is 100 Mpc/h on a side and **not periodic**.
- 15 log-spaced bins from 0.5 to 10 Mpc/h (16 edges, stored in `paircount/__init__.py`).
- Your counts are compared with golden counts you cannot see. Two divisions exist: `exact` and `toleranced`. You will choose at Level 2; until then it is `exact`.

## Roles

- **Driver:** types the prompts into Claude Code. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock.
- **Sceptic:** owns the check and the memory estimates. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence.
- **Scribe:** keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment.
- **Coach:** your leader. Asks questions rather than giving answers, and steps in on tooling problems.

Hands off the code: humans read, think and type prompts. All code changes go through Claude.

## Two windows

1. **Claude window (large):** Claude Code runs here. Only the Driver types in it.
2. **Gate terminal:** a separate terminal for the humans. `./gate unlock`, `./gate hint`, `./race submit` and `./race install-solution` are typed here. Claude never types there.
3. **Plan mode:** the Claude session starts in plan mode (read-only planning). Press `Shift+Tab` until it says plan mode is off before asking for runs or edits.

## Level 0: Measure before you touch anything (about 7 minutes)

Find out how slow the reference is, and where the time goes, before changing anything. Claude does the runs; you read the numbers.

1. In Claude: `make bench N=500 IMPL=reference`, then `N=1000`, then `N=2000`. Each run is timed and checked (against the golden counts at N = 2000, and against the reference itself for smaller N).
2. `make profile` runs the reference at N = 1000 under a profiler. Find the call that is made most often.
3. `make fit` fits time against N and predicts the runtime at N = 200,000. Write down the exponent and the predicted time. The reference takes about 0.2 s at N = 2000 and roughly an hour at N = 200,000 on a laptop; the group measures the real number.
4. In the gate terminal, run `./gate unlock`. It asks how many unique pairs, and so `math.sqrt` calls, the reference evaluates at N = 1000, then one reflection question: the predicted runtime at 200,000 and how you got it.

## What to watch for

- Haiku will want to optimise straight away ("I can vectorise this!"). At this level the guard refuses edits to `fast.py`. When that happens, read the refusal aloud: it is on purpose.
- Any number Claude quotes should have a command and its output next to it.
- When a run fails or is stopped, `make` adds its own `make: *** [bench] Error 1` line. That is not a crash: the harness output above it says what happened.

## Commands

| Command | Where | What it does |
|---|---|---|
| `make bench N=2000 IMPL=reference` | Claude or gate terminal | Times `reference` or `fast` on N points, checks the counts, records the run |
| `make check N=2000` | Either | Correctness only; prints a per-bin diff table if counts differ |
| `make profile` | Either | Profiles the reference at N = 1000 |
| `make fit` | Either | Fits the scaling and predicts the time at N = 200,000 |
| `make log` | Either | Shows the bench log |
| `./race status` | Either | Level, division, recent runs, submissions |
| `./race log` | Either | The bench log as a table |
| `./race board` | Either | Submissions: score, division, seconds, commit |
| `./race submit` | Gate terminal only | Level 3: runs your entry on the hidden catalogue and scores it |
| `./race install-solution <level>` | Gate terminal, facilitator only | Installs a reference solution |
| `make status` | Either | `./gate status` and `./race status` |
| `./gate status` | Either | Level, persona, time on level, hints used |
| `./gate brief` | Either | Shows the current level brief |
| `./gate check` | Either | Runs the level's machine check |
| `./gate hint` | Gate terminal | A hint (tiers at 0, 5 and 10 minutes, and the gate question's answer at 13) |
| `./gate unlock` | Gate terminal | Checks your evidence, asks the gate question, opens the next level |
