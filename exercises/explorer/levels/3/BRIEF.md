# Level 3: Review

**Target time:** 8 minutes. **Persona in force:** `collaborator`. This is the last level.

## Where we are

The tool works and has tests. Now get a fresh pair of eyes. The author grading its own work is not a review, so the review comes from the `reviewer` agent: a fresh context that has not seen this conversation and judges only the code and `PLAN.md`. Some of what it finds will be wrong. You decide.

`REVIEW.md` is open, and `explorer/` and `tests/` stay open for the fixes. `PLAN.md` and `TESTS.md` are frozen now.

## What to do

1. **Before you ask:** write two things in `REVIEW.md` that you think a reviewer will find. One minute. (`REVIEW.md` is not code: type into it yourselves, or dictate it to Claude.)
2. The playbook's *Independent review*, using the agent shipped in this repo:

   > "Use the reviewer agent to review the code since start against PLAN.md. Rank the findings by severity. Don't fix anything."

3. Ask Claude to paste the findings into the table in `REVIEW.md`, most severe first. Compare them with your guesses.
4. *Triage* the top three to five as a group: **FIX**, **ACCEPT** (true, but not worth fixing in a prototype) or **REJECT** (wrong), each with one line of reason.
5. Then:

   > "Fix the FIX items one at a time. For each, add a test that fails before the fix and passes after, run the tests, and commit."

## If it goes differently

- Lots of findings: you don't need to debate them all. Decide the ones that matter for a prototype and leave the rest; the gate needs three.
- Nothing worth fixing: that's a fine result. Say why in the reasons, and commit `REVIEW.md`.
- Time left? Build one feature from your Level 1 list, or run `make explore DATA=...` on a CSV of your own.

## What to watch for

- Fixing every finding without discussing it. Rejecting a finding with a good reason is as useful as fixing one.
- A fix that changes an existing test to make it pass.
- A guess the reviewer also found, or missed: it tells you how far to trust each.

## Opening the gate

`./gate check` needs at least 2 guesses and at least **3 triaged findings** in `REVIEW.md` (each FIX, ACCEPT or REJECT with a reason); the tests passing; the tool passing the Level 1 runs again on your dataset; at least 1 commit since Level 2; and nothing uncommitted under `explorer/`, `tests/` or in `REVIEW.md`.

The reflection (logged): what did the review find that the tests didn't?

Scribe: finish `LOG.md`. `PLAYBOOK.md` is yours to take home, and `.claude/agents/reviewer.md` with it.

When the FIX items are done and the tests pass: commit, then `./gate unlock`.
