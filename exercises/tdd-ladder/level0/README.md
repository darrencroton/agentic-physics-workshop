# The TDD Ladder

A collaborator sends your group one line:

> Can you add a function to bin our measurements and give us the weighted mean and error in each bin? We need it for the H(z) plot.

It sounds trivial. Over the next hour you will build this one feature several times, starting badly on purpose, while an objective scorecard shows how good your tests really are at each step. By the end you will have caught an agent marking its own homework, and have a test habit you can reuse on real analysis code.

The big idea: **you define "correct"; the agent cannot.**

## Roles

- **Driver:** types the prompts into Claude Code. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock.
- **Sceptic:** owns the check. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence.
- **Scribe:** keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment.
- **Coach:** your leader. Asks questions rather than giving answers.

Humans read, think and type prompts. All code changes go through the agent.

## Two windows

1. **Agent window (large):** Claude Code. Only the Driver types here. It starts in plan mode: press `Shift+Tab` until plan mode is off before asking for edits.
2. **Gate terminal:** a separate terminal. Every `./gate` and `./tdd` command goes here. The agent never types there.

## Level 0: just build it (about 5 minutes)

You will do what most of us do with an AI assistant: ask for the feature in one sentence and accept what comes back. The scorecard then shows how much the agent decided without asking:

- **Acceptance tests:** 12 hidden checks of what the client really wanted.
- **Mutants:** 16 copies of a correct solution, each with one deliberate bug. A test that fails on one "kills" it.
- **False alarms:** your tests that fail on a correct solution, so the test is wrong.

With no tests yet, expect a poor score. That is the baseline.

1. In the agent window, paste the client's request exactly as written above. Add nothing.
2. Accept what the agent gives you. Do not correct it or ask for tests.
3. Run `make plot` and look at `results/hz_binned.png`.
4. In the gate terminal, run `./tdd score` and read the scorecard.
5. In the gate terminal, run `./gate unlock`. It asks how many acceptance tests passed, saves your work on a branch and starts Level 1 from a fresh stub. A talk prompt follows.

Do not polish. Score it and move on.

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
