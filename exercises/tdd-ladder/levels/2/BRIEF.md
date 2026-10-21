# Level 2: Decide before you test

**Target time:** 10 minutes. **Persona:** `coach`.

## Where we are

At Level 1 nobody decided what the function should do, so every awkward case was settled by default. Now you write the decisions down first. The agent becomes a coach: it interviews you and never suggests answers.

**No code, no tests.** The agent may write only `SPEC.md` and `LOG.md`. The gate checks that `src/` and `tests/` are unchanged.

## Do this

1. Ask the agent to interview you:

   > We need to implement binned_weighted_mean(x, y, sigma, edges). Interview us about every behavioural decision: inputs, edge cases, conventions, errors, outputs. Ask about the hard parts we may not have considered. Don't suggest answers. Then write SPEC.md with numbered decisions.

2. Answer as a group and argue it out. Scribe: log each decision and who disagreed.
3. Check `SPEC.md` has at least six numbered decisions (`1.`, `2.`, ...), one per line, saying what you actually decided.

## Watch for

- One person deciding everything, or the agent steering your answers.
- Questions you hadn't thought of until the agent asked.
- Do you all agree what the error bar means? What does the person reading the plot assume?

## The gate

`./gate unlock` needs six numbered decisions and `src/` and `tests/` unchanged; if not, it names the files and how to restore them. It then reveals `CLIENT_SPEC.md`: read it together, and adopt the client's choice where you differ. If you think the client is wrong, that is a conversation with the client, not a quiet override in code. A talk prompt follows.
