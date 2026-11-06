# Level 0: Just build it

**Target time:** 5 minutes. **Persona:** `literal`.

## Where we are

You will do what most of us do with an AI assistant: ask for the feature in one sentence and accept what comes back. Then score it. With no tests yet, expect a poor score. That is the baseline.

## Do this

1. In the agent window, press `Shift+Tab` until plan mode is off.
2. Paste the client's request exactly as written. Add nothing:

   > Can you add a function to bin our measurements and give us the weighted mean and error in each bin? We need it for the H(z) plot.

3. Accept what the agent gives you. Do not correct it or ask for tests.
4. Run `make plot` and look at `results/hz_binned.png`.
5. In the gate terminal, run `./tdd score` and read the scorecard.

## Watch for

- Choices the agent makes without asking you. Scribe: note them.
- Polishing. Score it and move on.

## The gate

`./gate unlock` asks how many acceptance tests passed, saves your work on a branch and starts Level 1 from a fresh stub. A talk prompt follows.
