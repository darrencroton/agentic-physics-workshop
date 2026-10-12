# The TDD Ladder

## The story

Your group's small H(z) analysis package, `hzbin`, plots cosmic-chronometer-style Hubble-rate measurements. A collaborator sends you this request:

> Can you add a function to bin our measurements and give us the weighted mean and error in each bin? We need it for the H(z) plot.

That is the whole request. It sounds trivial. Over the next hour you will build this one feature several times, starting badly on purpose, while an objective scorecard tells you how good your tests really are at each step.

The big idea: **you define "correct"; the agent cannot.** Tests are only as good as the decisions and expected values behind them.

## Roles

- **Driver:** types the prompts into Claude Code. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock.
- **Sceptic:** owns the check. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence.
- **Scribe:** keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment.
- **Coach:** your leader. Asks questions rather than giving answers, and steps in on tooling problems.

Hands off the code: humans read, think, discuss and type prompts. All code changes go through Claude.

## Two windows

1. **Claude window (large):** Claude Code runs here. Only the Driver types in it.
2. **Gate terminal:** a separate terminal for the humans. Everything starting `./gate` or `./tdd` (apart from the read-only ones) is typed here. Claude never types there.

## Level 0: just build it (about 5 minutes)

1. In the Claude window, paste the client's request exactly as written above. Add nothing.
2. Accept what Claude gives you. Do not correct it or ask for tests.
3. Run `make plot` and look at the result in `results/hz_binned.png`.
4. In the gate terminal, run `./tdd score` and read the scorecard.
5. In the gate terminal, run `./gate unlock`. It will ask how many client acceptance tests passed, then one reflection question.

Do not polish. Score it and move on.

## Commands you will use

| Command | Where | What it does |
|---|---|---|
| `make plot` | Claude window or gate terminal | Writes `results/hz_binned.png` |
| `make test` | Claude window or gate terminal | Runs the test suite |
| `./tdd score` | Gate terminal | Prints your scorecard and records it |
| `./tdd ladder` | Gate terminal | Shows your recorded scores by level |
| `./tdd status` | Either | Shows the level, phase and last score |
| `./gate status` | Either | Shows level, persona, minutes on level, hints used |
| `./gate unlock` | Gate terminal | Checks your work, asks the gate question, opens the next level |

Stuck? `./gate hint` in the gate terminal gives you a hint.
