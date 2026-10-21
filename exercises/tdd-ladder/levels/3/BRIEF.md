# Level 3: Red, green, refactor, for real

**Target time:** 15 minutes. **Persona:** `coach`, with phase rules on.

## Where we are

Now you build it properly with **red, green, refactor**. The tool enforces the phases; humans own them and the numbers. The **oracle** (the trusted source of an expected value) is a person with a calculator, never the agent.

Your earlier work is saved on a branch and the stub is restored. Implement `CLIENT_SPEC.md` one behaviour at a time, referencing it and `SPEC.md` with `@`.

## The cycle

In the gate terminal unless noted.

1. **Red.** `./tdd red "<behaviour>"`. The agent writes **one** test; only `tests/` can change.
2. **Oracle.** The Sceptic computes the expected value by hand on a tiny input (2 to 4 points, exact fractions where possible). No numbers from the agent.
3. **Commit the test, then `./tdd green`.** It checks the test fails for the right reason (an assertion or `NotImplementedError`, not an import error).
4. **Green.** The agent writes the minimum code to pass; only `src/` can change. Run the tests and commit.
5. Every few cycles, `./tdd refactor`, then `./tdd done`. A cycle counts only once `./tdd done` closes it.

Wrong test? `./tdd abort "wrong oracle"` closes the cycle without credit; answer no to restore `tests/` to how it was at red, then restart with the corrected value. If a new test passes straight away, `./tdd abort` closes that cycle too; answer yes to keep it.

Suggested order: single bin, equal sigma (arithmetic mean); unequal sigma (inverse-variance weights); error is (sum of weights) to the power minus one half; two bins and the edge convention (S1); out-of-range points and `n_dropped` (S2); empty bin (S6); invalid inputs (S7 to S9); `x_eff` (S5); inputs unchanged (S10).

## Watch for

- The agent writing three tests when you asked for one. Navigator: say no.
- Numbers from the agent, or a tolerance looser than it needs. Sceptic: did you compute that, and what justifies the tolerance?
- The agent trying to edit a test during green, and the block that follows. Discuss it.

Run `./tdd score` now and then.

## The gate

`./gate unlock` needs at least 5 closed cycles and a latest score with 0 false alarms (a **false alarm** is your test failing on a correct solution: the test is wrong) and at least 9/16 mutants killed. It asks which spec decision (e.g. S4) still has a surviving mutant: read it from the score, or type `none` if you killed all 16.
