# Level 4: Think like a physicist

**Target time:** 8 minutes. **Persona in force:** `coach`, with phase rules still on.

## Where we are

At Level 3 you wrote example tests ("these inputs, this number"). Each checks only a few points, so some mutants (deliberately buggy copies of a correct solution) usually survive. Physics gives you something stronger: rules that hold for any input. A **property test** checks such a rule, for example that shuffling the data must not change the answer. One property test can kill a whole class of bug.

You still use red, green, refactor, with the agent as coach and the humans owning the phases and numbers. Use fixed seeds in random tests, and justify tolerances with a binomial argument, not by feel.

## What to do

1. Pick at least three properties from the menu.
2. For each one, run `./tdd red "<property>"`, have the agent write the test, commit, then `./tdd green`, and so on. A property test often passes first time on a correct implementation. That is fine: `./tdd abort "already satisfied"` closes the cycle (answer yes to keep the test) and you move to the next property.
3. Keep the whole suite under 10 seconds. Use fixed seeds in any random test.
4. Run `./tdd score` in the gate terminal and see which survivors remain.

| Property test | Kills mutants like |
|---|---|
| Permutation invariance: shuffle the inputs, results unchanged | Order-dependent accumulation |
| Uniform-sigma limit: equal sigma (pick sigma != 1, and y values that scatter more than sigma) gives the arithmetic mean and err = sigma/sqrt(n), to within floating-point rounding | Wrong weights; a missing square root; scatter-based error |
| Affine equivariance: y to a*y + b **and sigma to abs(a)*sigma** gives mean to a*mean + b, err to abs(a)*err and x_eff unchanged (needs abs(a) != 1) | Wrong weights; a missing square root |
| Bin merging: combining two adjacent bins' weighted means equals binning with the edge removed | Weighting errors; `x_eff` errors |
| Coverage: fixed-seed Monte Carlo. Draw y from N(mu, sigma) and check the fraction of bins with abs(mean - mu) < err is about 0.683, within a binomially justified bound | Wrong error definitions, wrong weights |
| Precision: float32 input with a large offset (y about 1e6 plus a small signal) matches the float64 result | float32 accumulation |

## What to watch for

- Monte Carlo tolerances picked by feel. What is the binomial sigma for your N? Is your bound 3 sigma?
- Slow tests. Smaller N means a wider bound, so recompute it.
- A property test that just re-implements the formula.

## Opening the gate

In the gate terminal, run `./gate unlock`. It needs your latest score to show at least 14/16 mutants killed and 0 false alarms (none of your tests failing on a correct solution), and your own suite to run in under 10 seconds. It then asks: for a coverage test with 2,500 independent bin-trials and true coverage 0.683, what is the standard deviation of the measured coverage fraction?
