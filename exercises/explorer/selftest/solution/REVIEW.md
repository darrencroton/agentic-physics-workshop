# Review

## Our guesses (before the review): what we think a reviewer will find
- The JavaScript is untested, so a bug in the log or missing-value handling would go unnoticed.
- Odd CSV input (duplicate headers, a column called "none", very wide files) may not be handled.
- The hover text is rebuilt for every point on every redraw, which may be slow at 20,000 points.

## Findings (from the reviewer), triaged by us

| # | Finding | Severity | Decision (FIX / ACCEPT / REJECT) | Reason |
|---|---|---|---|---|
| 1 | Duplicate column names in the CSV silently collapse into one column and lose data | High | FIX | Silent data loss; now a clear error and a test |
| 2 | A numeric column named "none" would clash with the "none" option in z and colour | Low | ACCEPT | Very unlikely; recorded in the plan as out of scope |
| 3 | Hover text for every point is rebuilt on each redraw (about 0.25 s at 20,000 points in a Node timing) | Medium | ACCEPT | Fast enough for the workshop datasets; revisit if the page feels slow |
| 4 | Unparsable values in a column the sidecar marks numeric are quietly treated as missing | Medium | REJECT | Documented behaviour in PLAN.md (missing values are kept and reported); a warning is a later improvement |

## What the review found that the tests did not
Finding 1 (duplicate headers) was missed by every test we wrote, because all our fixtures had unique column names. Finding 3 cannot be seen by the Python tests at all, because it lives in the page's JavaScript.
