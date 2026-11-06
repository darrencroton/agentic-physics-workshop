# Level 0: Measure before you touch anything

**Target time:** 7 minutes. **Persona:** `coach`.

## Where we are

Find out how slow the reference is, and where the time goes. The agent does the runs; you read the numbers. `fast.py` stays frozen until Level 1.

## Do this

1. In the agent window, press `Shift+Tab` until plan mode is off.
2. Ask the agent to run `make bench N=500 IMPL=reference`, then `N=1000`, then `N=2000`.
3. Ask it to run `make profile`: the reference at N = 1000 under a profiler. Which call is made most often?
4. Ask it to run `make fit`: it fits time against N and predicts the runtime at N = 200,000. **Write down the exponent and your predicted time.**

## Watch for

- The agent offering to optimise now. The guard refuses edits to `fast.py`: read the refusal aloud. It is on purpose.

## The gate

In the gate terminal, `./gate unlock`. It asks how many unique pairs (so `math.sqrt` calls) the reference evaluates at N = 1000. A talk prompt about your prediction follows.
