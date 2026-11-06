# The TDD Ladder

A collaborator sends your group one line:

> Can you add a function to bin our measurements and give us the weighted mean and error in each bin? We need it for the H(z) plot.

It sounds trivial. In about 45 minutes you will build this one feature several times, starting badly on purpose, while an objective scorecard shows how good your tests really are at each step. By the end you will have caught an agent marking its own homework, and have a test habit you can reuse on real analysis code.

The big idea: **you define "correct"; the agent cannot.**

## How it runs

| Level | | Target |
|---|---|---|
| 0 | Just build it | 5 minutes |
| 1 | "Use TDD, please" | 6 minutes |
| 2 | Decide before you test | 10 minutes |
| 3 | Red, green, refactor, for real | 15 minutes |
| 4 | Think like a physicist | 8 minutes |
| 5 | Stretch: test the tests | 5 minutes |

A gate checks each level before the next one opens. **`BRIEF.md` is your running sheet**: what to do now, what to watch for, and what the gate needs. It changes at every unlock. Read this page once, then open `BRIEF.md` (or run `./gate brief`).

## The scorecard

`./tdd score` measures your code and your tests against:

- **Acceptance tests:** 12 hidden checks of what the client really wanted.
- **Mutants:** 16 copies of a correct solution, each with one deliberate bug. A test that fails on one "kills" it.
- **False alarms:** your tests that fail on a correct solution, so the test is wrong.

## Roles

- **Driver:** types the prompts into Claude Code. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock.
- **Sceptic:** owns the check. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence.
- **Scribe:** keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment.
- **Coach:** your leader. Asks questions rather than giving answers.

Humans read, think and type prompts. All code changes go through the agent.

## Two windows

1. **Agent window (large):** Claude Code. Only the Driver types here.
2. **Gate terminal:** a separate terminal. Every `./gate` and `./tdd` command goes here. The agent never types there.

## Your files

| File | What it's for |
|---|---|
| `BRIEF.md` | What to do at this level |
| `LOG.md` | The Scribe's log |
| `src/hzbin/binning.py`, `tests/` | The function and its tests |
| `results/` | The plot, `hz_binned.png`, with a copy per level |
| `AGENTS.md`, `CLAUDE.md` | The agent's instructions. You don't need to read them. |

## Commands

| Command | Where | What it does |
|---|---|---|
| `make plot` | Either | Writes `results/hz_binned.png` (and a copy per level) |
| `make test` | Either | Runs the test suite |
| `./tdd score` | Gate | Prints and records your scorecard |
| `./tdd ladder` | Gate | Shows your scores by level |
| `./tdd new-attempt` | Gate | Saves your work on a branch and resets to the stub, to restart a level |
| `./gate unlock` | Gate | Checks your work and opens the next level |
| `./gate brief` | Gate | Shows the current level's brief |
| `./gate hint` | Gate | Gives a hint |
| `./gate status` | Either | Level, persona, minutes, hints used |
