# Level 1: "Use TDD, please"

**Target time:** 6 minutes. **Persona in force:** `literal`.

Same request as before, but this time you ask for test-driven development.

## What to do

1. In the gate terminal, run `./tdd new-attempt`. It saves your Level 0 work on a branch and restores the starting stub and an empty `tests/`.
2. In the Claude window, paste the client's request again, exactly as before, and add: *"Use test-driven development."*
3. Accept what Claude gives you. Watch closely, but do not coach it.
4. Run `make test` and `make plot`.
5. In the gate terminal, run `./tdd score`.

## What to watch for

- Did any test fail before the implementation existed?
- When the tests first ran, were they all green?
- Where did the expected numbers come from? Claude's head? Running the code? You?
- Did a test get changed after a failure?
- Did anything get skipped?

Scribe: note the exact moment you would have expected to see red.

## Opening the gate

In the gate terminal, run `./gate unlock`. It checks that you have started a new attempt and recorded a score, then asks two reflection questions:

- Did any test fail before the implementation existed? (y/n)
- Where did the expected values come from? (a) human hand calculation, (b) Claude's mental arithmetic, (c) running the implementation, (d) independent reference.

Your answers are logged in `LOG.md`, not graded. Be honest.
