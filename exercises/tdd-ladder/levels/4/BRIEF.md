# Level 4: Think like a physicist

**Target time:** 8 minutes. **Persona:** `coach`, phase rules still on.

## Where we are

Example tests check a few points, so some mutants usually survive. Physics gives you something stronger: rules that hold for any input. A **property test** checks one, such as "shuffling the data must not change the answer", and can kill a whole class of bug. Same red, green, refactor, same ownership of numbers.

## Do this

1. Pick at least three properties from the menu.
2. For each: `./tdd red "<property>"`, agent writes the test, commit, `./tdd green`, and so on. A property test often passes first time on a correct implementation. Then `./tdd abort "already satisfied"`, answer yes to keep the test, and move on.
3. Use fixed seeds in random tests, justify tolerances with a binomial argument rather than feel, and keep the whole suite under 10 seconds.
4. Run `./tdd score` and see which survivors remain.

| Property test | Kills mutants like |
|---|---|
| Permutation invariance: shuffle the inputs, results unchanged | Order-dependent accumulation |
| Uniform-sigma limit: equal sigma (not 1, with y scattering more than sigma) gives the arithmetic mean and err = sigma/sqrt(n), to within rounding | Wrong weights; missing square root; scatter-based error |
| Affine equivariance: y to a*y + b **and sigma to abs(a)*sigma** gives mean to a*mean + b, err to abs(a)*err, x_eff unchanged (abs(a) != 1) | Wrong weights; missing square root |
| Bin merging: combining two adjacent bins' weighted means equals binning with the edge removed | Weighting and `x_eff` errors |
| Coverage: fixed-seed Monte Carlo, y from N(mu, sigma); the fraction of bins with abs(mean - mu) < err is about 0.683, within a binomial bound | Wrong error definitions or weights |
| Precision: float32 input with a large offset (y about 1e6 plus a small signal) matches float64 | float32 accumulation |

## Watch for

- Monte Carlo tolerances picked by feel. What is the binomial sigma for your N? Is your bound 3 sigma? Smaller N means a wider bound, so recompute it.
- A property test that just re-implements the formula.

## The gate

`./gate unlock` needs at least 14/16 mutants killed, 0 false alarms and a suite under 10 seconds. It asks: for a coverage test with 2,500 independent bin-trials and true coverage 0.683, what is the standard deviation of the measured coverage fraction?
