# Self-test sample suites

Sample implementations and test suites for the scripted walkthrough. Scores are measured by `hidden/verify_assets.py`. A mutant counts as killed only by a test that passes on the reference. False alarms are tests that fail on the reference.

| Sample | Contents | Acceptance | Mutants killed | False alarms | Band |
|---|---|---|---|---|---|
| `l0_naive/` | vibe-coded `binning.py` (midpoint x_eff, scatter error, no validation, half-open last bin) plus 3 snapshot tests | 4/12 | 1/16 | 2 | acceptance 4-9, kills <= 6 |
| `l1_tests_after/` | better `binning.py` plus 5 tests that restate its formulas | 6/12 | 8/16 | 0 | acceptance 6-10, kills <= 8 |
| `l2/SPEC.md` | group spec with 7 numbered decisions; differs from the client on S1 (last bin half-open) and S6 (empty bin gives 0 and inf) | n/a | n/a | n/a | 7 items |
| `l3_cycles/cycle1..5/` | one `behaviour.txt`, one new test and the minimal `binning.py` per cycle; cumulative when the tests are copied together | 1, 2, 4, 5, 7 of 12 | 0, 2, 4, 7, 9 | 0 | each new test red on the previous code, all green on its own |
| `l3_cycles/rung4/` | 11 spec-driven tests, hand oracles; no S7, S9, S10 or upper-side `n_dropped` tests | 10/12 | 11/16 (survivors M04, M11, M13, M14, M15) | 0 | kills >= 9, false alarms 0 |
| `l3_cycles/bad_import/` | one test importing a missing name; fails at collection with `ImportError` | n/a | n/a | n/a | must fail |
| `l4_rung5/` | Rung-4 style examples plus validation, input-unchanged and property tests (permutation, uniform sigma, affine, bin merging, seeded coverage, float32) | 12/12 | 16/16 | 0 | kills >= 14, false alarms 0, runtime < 10 s (about 0.5 s) |

Acceptance for the `l3_cycles` rows is the cycle's `binning.py` against the hidden acceptance suite, and kills are for the cumulative tests up to that cycle.
