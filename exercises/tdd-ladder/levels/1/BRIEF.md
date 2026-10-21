# Level 1: "Use TDD, please"

**Target time:** 6 minutes. **Persona:** `literal`.

## Where we are

You now ask for **test-driven development**: write a test first, watch it fail, then write the code. Saying "TDD" is not the same as doing it, and the agent is still literal, so it does only what the words say. Your Level 0 work is saved on a branch and the code is back to the stub.

## Do this

1. In the agent window, paste the client's request again, exactly as before, and add:

   > Use test-driven development.

2. Accept what the agent gives you. Watch closely; do not coach it.
3. Run `make test`, `make plot`, then `./tdd score` in the gate terminal.

To start the level again, run `./tdd new-attempt` in the gate terminal, then score again at the end.

## Watch for

- **Red** is a test that fails before the code exists; **green** is the passing code after. Did you ever see red? Were the first runs all green?
- The **oracle** is where a test's expected numbers come from: the agent's head, running the code, or you. Whose was it?
- A test changed after it failed, or skipped.

Scribe: note the exact moment you expected to see red.

## The gate

`./gate unlock` needs a fresh score for this attempt. A talk prompt follows.
