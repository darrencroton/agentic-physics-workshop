# Level 5 (stretch): Test the tests

**Target time:** 5 minutes. **Persona:** `collaborator`.

## Where we are

Your suite beats our 16 hidden mutants, but would it catch a bug nobody has thought of? **Mutation testing** plants small deliberate bugs (**mutants**) in your own code. A mutant your tests catch is **killed**; one they miss **survives**, meaning a gap in your tests or an **equivalent mutant** (no behaviour change, so no test could notice). The agent is a normal collaborator again, still evidence-first: it shows every command and output.

## Do this

1. Ask the agent to use a subagent to write about ten small mutants of **your** `binning.py` (flip a comparison, change an exponent, drop a term), each a separate copy under `mutants/`, not an edit to your real file.
2. Run your suite against each mutant, with the command and output shown.
3. For each survivor, decide: real gap, or equivalent mutant?
4. Ask which of your tests are redundant.
5. Scribe: add a `## Mutation report` section to the end of `LOG.md`: each mutant, killed or survived, and whether a survivor is a real gap or an equivalent mutant.

## Watch for

- "All killed" without the runs shown.
- Mutants so silly any test catches them.
- Changes left behind in your real `src/`.

## The gate

`./gate unlock` needs a `## Mutation report` section in `LOG.md`. A talk prompt follows.
