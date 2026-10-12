# Level 5 (stretch): Test the tests

**Target time:** 5 minutes. **Persona in force:** `collaborator`.

## Where we are

Your suite now scores well against our 16 hidden mutants. But those mutants are ours, not yours. How do you know your tests would catch a bug nobody has thought of yet? That is the question for this level.

**Mutation testing** means planting small deliberate bugs (**mutants**) in your own implementation and checking that your suite fails on each. A mutant your tests catch is **killed**. One they miss **survives**, which points to a gap in your tests, or to an **equivalent mutant**: a change that does not alter behaviour, so no test could notice it.

Claude is now a normal collaborator, still evidence-first. It must show every command and its output, and you should not accept a claim without them.

## What to do

1. Ask Claude to use a subagent to write about ten small mutants of **your** `binning.py`, for example flipping a comparison, changing an exponent or dropping a term. Each one should be a separate copy under `mutants/` (Claude may write there at this level), not an edit to your real file.
2. Run your suite against each mutant. Ask for the command and the output.
3. For each survivor, decide: is it a real gap in your tests, or an equivalent mutant?
4. Ask which of your tests are redundant.
5. Scribe: add a `## Mutation report` section to `LOG.md` with the mutants, which survived, and what you decided.

## What to watch for

- Claude reporting "all killed" without showing the runs.
- Mutants that are so silly any test would catch them.
- Any change to your real `src/` left behind by the mutation run.

## Opening the gate

In the gate terminal, run `./gate unlock`. It checks `LOG.md` has a `## Mutation report` section, then asks a free-text question: one test you would delete, and why.
