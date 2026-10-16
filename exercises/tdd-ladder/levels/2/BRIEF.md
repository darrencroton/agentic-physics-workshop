# Level 2: Decide before you test

**Target time:** 10 minutes. **Persona in force:** `coach`.

## Where we are

At Level 1 you asked for TDD, and probably saw tests and code arrive together, all green, with expected numbers that came from the agent. A test that never failed, with numbers nobody checked, proves little. The deeper problem comes earlier: nobody had decided what the function should do, so every awkward case was settled by default.

This level is about **specification**: writing the decisions down *before* any test or code. The agent switches to `coach` mode and interviews you. It asks questions but never suggests answers, because the decisions have to be yours.

**No code, no tests.** The agent may only write `SPEC.md` (and `LOG.md`). Please do not touch `src/` or `tests/` during this level, because the gate checks that they are unchanged.

## What to do

1. In the agent window, ask the agent to interview you. A good prompt:

   > We need to implement binned_weighted_mean(x, y, sigma, edges). Interview us about every behavioural decision: inputs, edge cases, conventions, errors, outputs. Ask about the hard parts we may not have considered. Don't suggest answers. Then write SPEC.md with numbered decisions.

2. Answer as a group, not as one person. Argue it out.
3. Scribe: record each decision and who disagreed.
4. Check that `SPEC.md` has numbered decisions (at least six, each on its own line as `1.`, `2.`, ...) and says what you actually decided.

## What to watch for

- One person deciding everything.
- The agent steering your answers instead of asking.
- Questions you did not think of until the agent asked.
- Do you all agree on what the error bar means? What does the person reading the plot assume?

## Opening the gate

In the gate terminal, run `./gate unlock`. It checks `SPEC.md` has at least six numbered decisions and that `src/` and `tests/` are unchanged. If they changed, it names the files and how to put them back.

Once it unlocks, `CLIENT_SPEC.md` appears. Read it, then answer the reflection question: how many of the client's 10 decisions did your SPEC address (0 to 10)? Whatever you chose counts.

Then reconcile: adopt the client's spec where it differs. If you think the client got something wrong, that is a conversation with the client, not something to override quietly in code.
