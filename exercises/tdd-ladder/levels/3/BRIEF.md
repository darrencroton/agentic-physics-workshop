# Level 3: Red, green, refactor, for real

**Target time:** 15 minutes. **Persona in force:** `coach`, with phase rules switched on.

The unlock has already saved your earlier work on a branch and restored the stub, so you start clean. Implement `CLIENT_SPEC.md` one behaviour at a time. Reference it (and `SPEC.md`) with `@` in your prompts.

## The cycle

1. **Red.** In the gate terminal: `./tdd red "<behaviour>"`. Claude writes **one** test for that behaviour. Only `tests/` can change.
2. **Oracle.** The expected value comes from a human. The Sceptic computes it by hand on a tiny input (2 to 4 points, exact fractions where possible). No numbers from Claude.
3. **Commit the test.** Then, in the gate terminal: `./tdd green`. The tool checks that the test fails for the right reason (an assertion or `NotImplementedError`, not an import error).
4. **Green.** Claude writes the minimum code to pass. Tests are frozen. Only `src/` can change.
5. Run the tests, see them pass, commit.
6. Every few cycles, `./tdd refactor` (tests stay frozen), then `./tdd done`.

If a test is wrong, say so, and the group decides whether to go back to red on purpose.

## Suggested cycle order

1. Single bin, equal sigma: arithmetic mean.
2. Unequal sigma: inverse-variance weighting.
3. Error = (sum of weights) to the power minus one half.
4. Two bins and the edge convention (S1).
5. Out-of-range points and `n_dropped` (S2).
6. Empty bin (S6).
7. Invalid inputs (S7 to S9).
8. `x_eff` (S5).
9. Inputs unchanged (S10).

## What to watch for

- Claude writing three tests when you asked for one. Navigator: say no.
- Numbers appearing from Claude. Sceptic: did you compute that?
- A tolerance that is looser than it needs to be. Ask what justifies it.
- Claude trying to edit a test during green, and the block that follows. Discuss it.
- Is each test one behaviour?

Run `./tdd score` in the gate terminal now and then to see how you are doing.

## Opening the gate

In the gate terminal, run `./gate unlock`. It needs at least 5 valid cycles, and your latest score must show 0 false alarms and at least 9/16 mutants killed. It then asks: which spec decision (e.g. S4) still has a surviving mutant? Read it from the score, or type `none` if you killed all 16.
