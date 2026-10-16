# Level 3: Red, green, refactor, for real

**Target time:** 15 minutes. **Persona in force:** `coach`, with phase rules switched on.

## Where we are

At Level 2 you decided what the function should do, and `CLIENT_SPEC.md` showed which decisions you missed. Now you build it properly with the **red, green, refactor** cycle:

- **Red:** write one test for one behaviour and watch it fail, for the right reason.
- **Green:** write the least code that makes it pass.
- **Refactor:** tidy the code while the tests stay green.

The tool enforces the phases. Humans own them and the numbers: the agent may not invent expected values. The **oracle** (the trusted source of an expected number) is a person with a calculator.

The unlock has already saved your earlier work on a branch and restored the stub. Implement `CLIENT_SPEC.md` one behaviour at a time, referencing it and `SPEC.md` with `@`.

## The cycle

1. **Red.** In the gate terminal: `./tdd red "<behaviour>"`. The agent writes **one** test for that behaviour. Only `tests/` can change.
2. **Oracle.** The expected value comes from a human. The Sceptic computes it by hand on a tiny input (2 to 4 points, exact fractions where possible). No numbers from the agent.
3. **Commit the test.** Then, in the gate terminal: `./tdd green`. The tool checks that the test fails for the right reason (an assertion or `NotImplementedError`, not an import error).
4. **Green.** The agent writes the minimum code to pass. Tests are frozen. Only `src/` can change.
5. Run the tests, see them pass, commit.
6. Every few cycles, `./tdd refactor` (tests stay frozen), then `./tdd done`. A cycle only counts once `./tdd done` has closed it.

If a test is wrong, the group decides to go back to red: `./tdd abort "wrong oracle"` (gate terminal) closes the cycle without credit and asks whether to keep the new test. Answer no to restore `tests/` to how it was at RED, then start again with the corrected value. If a new test passes straight away, `./tdd abort` closes that cycle too; answer yes to keep it.

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

- The agent writing three tests when you asked for one. Navigator: say no.
- Numbers appearing from the agent. Sceptic: did you compute that?
- A tolerance that is looser than it needs to be. Ask what justifies it.
- The agent trying to edit a test during green, and the block that follows. Discuss it.

Run `./tdd score` now and then. A **false alarm** is one of your tests failing on a correct solution: the test is wrong.

## Opening the gate

In the gate terminal, run `./gate unlock`. It needs at least 5 valid cycles (none left open), and your latest score must show 0 false alarms and at least 9/16 mutants killed. It then asks: which spec decision (e.g. S4) still has a surviving mutant? Read it from the score, or type `none` if you killed all 16.
