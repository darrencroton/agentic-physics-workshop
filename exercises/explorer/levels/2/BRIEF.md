# Level 2: Test

**Target time:** 8 minutes.

## Where we are

The tool works and you've seen it. Now make sure it keeps working. You write your own list first, then the agent writes its test plan, and you compare. `tests/` and `TESTS.md` are open; `PLAN.md` is frozen.

## Do this

1. **Before you ask the agent anything**, the Scribe writes three things that must not break under "Our list" in `TESTS.md`. Two minutes, no agent. (Type into it yourselves, or dictate it to the agent.)
2. Then:

   > "Using the test-code skill, talk me through the five to eight tests this code needs, one line each: what each checks, what coverage that gives, and what it won't cover. Write the plan under 'The agent's plan' in TESTS.md. Don't write the tests yet."

3. Compare the plan with your list and agree what to write under "What we agreed to write, and why". pytest can't see a browser: what can be tested, and what still needs a human? If your dataset never triggers a rule in `INTERFACE.md` (missing values, a text column, zeros on a log axis), a test can use a small made-up CSV.
4. Then:

   > "Write them. Run them and show me the output."

5. Run `make test` yourselves in the gate terminal, and `make coverage` if there's time. Ask the agent to commit the tests and `TESTS.md`.

## Watch for

- A failing test is a finding, not a nuisance. Ask whether the code or the test is wrong before anything changes, and never accept a test "fixed" just to pass.
- Only the easy functions tested and the page left alone: coverage shows it.
- The agent's plan runs past eight tests: pick the handful that matter. The gate needs five. Time left? Break one behaviour on purpose and see whether the tests notice, then revert.

## The gate

`./gate check` needs at least 5 passing tests, one of them importing `explorer`; at least 1 commit since Level 1; and nothing uncommitted under `explorer/`, `tests/` or in `TESTS.md`. If "Our list" has fewer than three items, or the agent's plan is missing, the gate still passes with a note. When the tests pass in your own terminal: commit, then `./gate unlock`. A talk prompt follows.
