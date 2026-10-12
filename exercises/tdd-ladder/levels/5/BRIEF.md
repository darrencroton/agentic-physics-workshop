# Level 5 (stretch): Test the tests

**Target time:** 5 minutes. **Persona in force:** `collaborator`.

Who tests the tests? Mutation testing: plant small deliberate bugs in your implementation and see whether your suite notices.

## What to do

1. Ask Claude to use a subagent to write about ten small mutants of **your** `binning.py`, for example flipping a comparison, changing an exponent or dropping a term. Each one should be a separate copy, not an edit to your real file.
2. Run your suite against each mutant. Ask for the command and the output.
3. For each survivor, decide: is it a real gap in your tests, or an equivalent mutant (a change that does not alter behaviour)?
4. Ask which of your tests are redundant.
5. Scribe: add a `## Mutation report` section to `LOG.md` with the mutants, which survived, and what you decided.

## What to watch for

- Claude reporting "all killed" without showing the runs.
- Mutants that are so silly any test would catch them.
- Any change to your real `src/` left behind by the mutation run.

## Opening the gate

In the gate terminal, run `./gate unlock`. It checks `LOG.md` has a `## Mutation report` section, then asks a free-text question: one test you would delete, and why.
