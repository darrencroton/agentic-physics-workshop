# Level 3: Review

**Target time:** 8 minutes. This is the last level.

## Where we are

The tool works and has tests. The `review-code` skill runs in a fresh context (a subagent in Claude Code) that has not seen this conversation and judges only the code and `PLAN.md`. Some of what it finds will be wrong; you decide which. `REVIEW.md`, `explorer/` and `tests/` are open; `PLAN.md` and `TESTS.md` are frozen.

## Do this

1. **Before you ask**, write two things in `REVIEW.md` that you think a reviewer will find. One minute. (Type them yourselves, or dictate.)
2. Then:

   > "Use the review-code skill to review the code since start against PLAN.md. Rank the findings by severity and paste them into the table in REVIEW.md, most severe first. Don't fix anything."

3. Compare the findings with your guesses.
4. Triage the top three to five as a group: **FIX**, **ACCEPT** (true, but not worth fixing in a prototype) or **REJECT** (wrong), each with a one-line reason.
5. If you marked a FIX:

   > "Fix the top FIX item: add a test that fails before the fix and passes after, run the tests, and commit."

## Watch for

- Fixing every finding without discussing it. Rejecting one with a good reason is as useful as fixing one.
- A fix that changes an existing test to make it pass.
- Fewer than three findings: ask for the next most important, low severity included. ACCEPT with a reason is a fine decision.

## The gate

`./gate check` needs the tests passing, the Level 1 runs passing again on your dataset, at least 1 commit since Level 2, and nothing uncommitted under `explorer/`, `tests/` or in `REVIEW.md`. Fewer than two guesses, or fewer than three triaged findings (each FIX, ACCEPT or REJECT with a reason), still passes with a note. When `REVIEW.md` is triaged and the tests pass: commit, then `./gate unlock`. A talk prompt follows. Scribe: finish `LOG.md`.

## Finished early

Ask the agent for the feature you agreed at Level 1, or one of these: one step, run it, look, commit.

- A day/night button that switches the page between light and dark colours.
- Select points with the mouse (box or lasso, in 2D) and show how many you picked, with their labels if the dataset has them.
