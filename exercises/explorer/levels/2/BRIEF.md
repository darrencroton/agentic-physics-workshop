# Level 2: Test

**Target time:** 8 minutes. **Persona in force:** `collaborator`.

## Where we are

The tool works, and you've seen it work. Now make sure it keeps working. Write your own list first, then ask the agent for its test plan, and compare: your list shows you what you'd have missed, and asking for the plan before the tests changes what you get.

`tests/` and `TESTS.md` are open. `PLAN.md` is frozen now.

## What to do

1. **Before you ask the agent anything:** the Scribe writes three things that must not break under "Our list" in `TESTS.md`. Two minutes, no agent. (`TESTS.md` is not code: type into it yourselves, or dictate it to the agent.)
2. The playbook's *Test plan, then tests*:

   > "Using the test-code skill, talk me through the five to eight tests this code needs, one line each: what each checks, what coverage that gives, and what it won't cover. Write the plan under 'The agent's plan' in TESTS.md. Don't write the tests yet."

3. Compare the agent's plan with your list and agree what to write under "What we agreed to write, and why". pytest can't see the page in a browser: what *can* be tested, and what still needs a human? If your dataset never triggers a rule in the README (missing values, a text column, zeros on a log axis), a test can check it with a small made-up CSV.
4. Then:

   > "Write them. Run them and show me the output."

5. Run `make test` yourselves in the gate terminal and, if there's time, `make coverage`: which lines does no test run? Then ask the agent to commit the tests and `TESTS.md`.

## If it goes differently

- The agent's plan is longer than eight tests: agree the handful of tests that matter most and write those. The gate needs five.
- A test fails: that's a finding, not a nuisance. Ask the agent whether the code or the test is wrong, and why, before anything changes.
- Time left? *Does the alarm ring?* "Break <one behaviour> on purpose and run the tests. Do they fail? Then revert."

## What to watch for

- The agent writing tests before the group says go.
- Only the easy functions tested, and the page left untested. Coverage shows it.
- A failing test "fixed" by changing the test. Never accept it: fix the code, or decide the test was wrong and say why.

## Opening the gate

`./gate check` needs at least 3 items under "Our list" and the agent's plan written in `TESTS.md`; at least **5 tests**, all passing, with at least one test module importing `explorer`; at least 1 commit since Level 1; and nothing uncommitted under `explorer/`, `tests/` or in `TESTS.md`.

The reflection (logged): what did the agent's plan cover that yours didn't, or the reverse?

When the tests pass in your own terminal: commit, then `./gate unlock`.
