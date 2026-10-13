# Level 3: Review

**Target time:** 8 minutes. **Persona in force:** `collaborator`. This is the last level.

## Where we are

The tool works and has tests. Now get a fresh pair of eyes. The author grading its own work is not a review, so the review comes from the `reviewer` agent: a fresh context that has not seen this conversation and judges only the code and `PLAN.md`. Some of what it finds will be wrong. You decide.

`REVIEW.md` is open. `PLAN.md` and `TESTS.md` are frozen now.

## What to do

1. **Before you ask:** write two things in `REVIEW.md` that you think a reviewer will find. One minute. (`REVIEW.md` is not code: type into it yourselves, or dictate it to Claude.)
2. The playbook's *Independent review*, using the agent shipped in this repo:

   > "Use the reviewer agent to review the code since start against PLAN.md. Rank the findings by severity. Don't fix anything."

3. Ask Claude to paste the findings into the table in `REVIEW.md`. Compare them with your guesses.
4. *Triage*: decide each finding yourselves. **FIX**, **ACCEPT** (true, but not worth fixing in a prototype) or **REJECT** (wrong), with one line of reason.
5. Then:

   > "Fix the FIX items one at a time, running the tests after each."

   Commit each fix.
6. Time left? Build one feature from your Level 1 list, or run `make explore DATA=...` on the other dataset or on a CSV of your own.

## What to watch for

- Fixing every finding without discussing it. Rejecting a finding with a good reason is as useful as fixing one.
- A fix that changes a test to pass.
- A guess the reviewer also found, or missed: it tells you how far to trust each.

## Opening the gate

`./gate check` needs at least 2 guesses and at least **3 triaged findings** in `REVIEW.md` (each FIX, ACCEPT or REJECT with a reason); the tests passing; the tool passing the Level 1 runs on **both** datasets; at least 1 commit since Level 2; and nothing uncommitted under `explorer/`, `tests/` or in `REVIEW.md`.

The reflection (logged): what did the review find that the tests didn't?

Scribe: finish `LOG.md`. `PLAYBOOK.md` is yours to take home, and `.claude/agents/reviewer.md` with it.

When the FIX items are done and the tests pass: commit, then `./gate unlock`.
