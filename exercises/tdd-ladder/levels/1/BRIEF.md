# Level 1: "Use TDD, please"

**Target time:** 6 minutes. **Persona in force:** `literal`.

## Where we are

At Level 0 you asked for the feature in one sentence and got code that looks fine. The scorecard showed how much Claude decided silently: many of the client's **acceptance tests** (hidden checks that say what the client really wanted) failed, and few of the **mutants** (copies of a correct solution, each with one deliberate bug) were caught by any tests.

Now you ask for **test-driven development (TDD)**: write a test first, watch it fail, then write the code that makes it pass. The lesson is that saying "TDD" is not the same as doing it. Claude is still on the `literal` persona, so it does what you literally say and no more. Watch what it does with those words.

Your Level 0 work is already saved on a branch, and the code and `tests/` are back to the starting stub. There is nothing to run first.

## What to do

1. In the Claude window, paste the client's request again, exactly as before, and add: *"Use test-driven development."*
2. Accept what Claude gives you. Watch closely, but do not coach it.
3. Run `make test` and `make plot`. The plot is also kept as `results/hz_binned_L1.png`, so you can compare it with `results/hz_binned_L0.png`.
4. In the gate terminal, run `./tdd score`.

Want to start this level again from the stub? In the gate terminal, run `./tdd new-attempt`. It saves what you have on a branch and resets the code and tests. Then run `./tdd score` again at the end.

## What to watch for

- Did any test fail before the implementation existed? A test that fails first is called **red**; the passing code that follows is **green**.
- When the tests first ran, were they all green?
- Where did the expected numbers come from? That source is the test's **oracle**: whatever you trust to say what the right answer is. Claude's head? Running the code? You?
- Did a test get changed after a failure?
- Did anything get skipped?

Scribe: note the exact moment you would have expected to see red.

## Opening the gate

In the gate terminal, run `./gate unlock`. It checks that you have recorded a score for this attempt, then asks two reflection questions:

- Did any test fail before the implementation existed? (y/n)
- Where did the expected values come from? (a) human hand calculation, (b) Claude's mental arithmetic, (c) running the implementation, (d) independent reference.

Your answers are logged in `LOG.md`, not graded. Be honest.
