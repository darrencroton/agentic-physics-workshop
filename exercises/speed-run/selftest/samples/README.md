# Self-test samples

Entries that `selftest/run.py` copies into `dist/speed-run/` as if a group had written them. Each `fast.py` is a complete `count_pairs(pos, edges)` drop-in for `paircount/fast.py`.

| Sample | What it is | Expected outcome |
|---|---|---|
| `l1_naive_matrix/` | Full N x N distance matrix with several float64 temporaries | Killed at the 2.5 GB cap at N = 20000 |
| `l1_chunked/` | Copy of `hidden/solutions/level1/fast.py` (500-row chunks) | Exact at 20k, under 10 s and 1.5 GB |
| `l2_sumsq/` | Level 2 cell list binning `s` against `e*e` (no sqrt) | Fails exact at 200k with a diff table; passes toleranced at sigma 0.1 |
| `l2_celllist/` | Copy of `hidden/solutions/level2/fast.py` | Exact at 200k, under 60 s |
| `l3_c_default/` | Level 3 C counter compiled without `-ffp-contract=off` (FMA) | Fails exact on the hidden catalogue, score 0 |
| `l3_c_off/` | Copy of `hidden/solutions/level3/` | Passes on the hidden catalogue, score > 1 |
| `race_toleranced.toml` | Toleranced division, sigma 0.1, justification over 80 characters | Valid |
| `race_invalid.toml` | Toleranced division with sigma 0.5 | Refused by the harness |

The copies of the solutions must be refreshed by hand if `hidden/solutions/` changes; the self-test checks that they still match.
