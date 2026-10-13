# Level 2: Test

**Target time:** 8 minutes. **Persona in force:** `collaborator`.

## Where we are

The tool works, and you've seen it work. Now make sure it keeps working. You'll write your own list first, then ask Claude for its test plan, and compare: writing your list first shows you what you'd have missed, and asking for the plan before the tests changes what you get.

`tests/` and `TESTS.md` are open. `PLAN.md` is frozen now.

## What to do

1. **Before you ask Claude anything:** the Scribe writes three things that must not break under "Our list" in `TESTS.md`. Two minutes, no Claude. (`TESTS.md` is not code: type into it yourselves, or dictate it to Claude.)
2. The playbook's *Test plan, then tests*:

   > "Talk me through the tests this code needs: what each one checks, what coverage that gives, and what it won't cover. Don't write them yet."

3. Paste Claude's plan into `TESTS.md`. Compare it with your list, and agree what to write under "What we agreed to write, and why". pytest can't see what the page does in the browser: what *can* be tested, and what still needs a human?
4. Then:

   > "Write them. Run them and show me the output."

5. Ask Claude to commit the tests and `TESTS.md`. Run `make test` yourselves in the gate terminal and, if there's time, `make coverage`: which lines does no test run?
6. Optional, one minute, *Does the alarm ring?*:

   > "Break <one behaviour> on purpose and run the tests. Do they fail? Then revert."

## What to watch for

- Claude writing tests before the group says go.
- Only the easy functions tested, and the page left untested. Coverage shows it.
- A failing test "fixed" by changing the test. Never accept it: a failing test is a finding. Fix the code, or decide the test was wrong and say why.

## Opening the gate

`./gate check` needs at least 3 items under "Our list" and Claude's plan pasted in `TESTS.md`; at least **5 tests**, all passing, with at least one test module importing `explorer`; at least 1 commit since Level 1; and nothing uncommitted under `explorer/`, `tests/` or in `TESTS.md`.

The reflection (logged): what did Claude's plan cover that yours didn't, or the reverse?

When the tests pass in your own terminal: commit, then `./gate unlock`.
