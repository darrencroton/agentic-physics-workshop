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

Hands off the code: humans read, think, discuss and type prompts. All code changes go through the agent.

## Two windows

This exercise needs Claude Code.

1. **Agent window (large):** Claude Code runs here. Only the Driver types in it.
2. **Gate terminal:** a separate terminal for the humans. Everything starting `./gate` or `./tdd` (apart from the read-only ones) is typed here. The agent never types there.
3. **Plan mode:** the agent session starts in plan mode (read-only planning). Press `Shift+Tab` until it says plan mode is off before asking for runs or edits.

## Level 0: just build it (about 5 minutes)

### Where we are

This is the starting line. You will do what most of us do with an AI assistant: ask for the feature in one sentence and accept what comes back. Nothing is wrong with the agent here. The point is to find out, with a scorecard, how much it decided for you without asking.

The scorecard has three numbers:

- **Acceptance tests:** a hidden set of 12 checks that say what the client really wanted. Passing them means the function does the job.
- **Mutants:** copies of a correct solution, each with one small deliberate bug (there are 16). Your tests "kill" a mutant if they fail on it. Few kills means your tests would not notice a real bug.
- **False alarms:** tests of yours that fail on a correct solution. That means the test itself is wrong.

At Level 0 there may be no tests at all, so expect a poor score. That is the baseline the rest of the hour improves on. The lesson: the agent cannot define "correct" for you.

### What to do

1. In the agent window, paste the client's request exactly as written above. Add nothing.
2. Accept what the agent gives you. Do not correct it or ask for tests.
3. Run `make plot` and look at the result in `results/hz_binned.png`. Each run also keeps a copy named for the level (`results/hz_binned_L0.png` now), so you can compare plots from different levels later.
4. In the gate terminal, run `./tdd score` and read the scorecard.
5. In the gate terminal, run `./gate unlock`. It will ask how many client acceptance tests passed, then one reflection question. It then saves your work on a branch and gives you a fresh starting stub for Level 1 automatically.

Do not polish. Score it and move on.

## Commands you will use

| Command | Where | What it does |
|---|---|---|
| `make plot` | Agent window or gate terminal | Writes `results/hz_binned.png`, plus a copy `results/hz_binned_L<level>.png` for each level |
| `make test` | Agent window or gate terminal | Runs the test suite |
| `./tdd score` | Gate terminal | Prints your scorecard and records it |
| `./tdd ladder` | Gate terminal | Shows your recorded scores by level |
| `./tdd new-attempt` | Gate terminal | Saves your work on a branch and resets the code and tests to the stub (the unlock does this for you at Levels 1 and 3; use it to restart a level) |
| `./tdd status` | Either | Shows the level, phase and last score |
| `./gate status` | Either | Shows level, persona, minutes on level, hints used |
| `./gate unlock` | Gate terminal | Checks your work, asks the gate question, opens the next level |

Stuck? `./gate hint` in the gate terminal gives you a hint.
