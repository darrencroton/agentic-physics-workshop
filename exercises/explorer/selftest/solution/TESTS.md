# Tests

## Our list (before asking Claude): things that must not break
- data.json must be strict JSON: no NaN or Infinity, missing values as null, every list the same length.
- A selected column with missing values must drop only those rows, and the page must say how many.
- The same --seed must give the same rows, and never more than --max-points.
- A missing file must give a one-line error and a non-zero exit, never a traceback.

## Claude's plan: each test, what it checks, and what it will not cover
1. Numeric detection without a sidecar: columns that parse as float are numeric, text columns become labels. Does not cover locale-specific number formats.
2. Numeric detection with a sidecar: units, descriptions and log flags are carried through; the sidecar's `numeric` flag overrides detection. Does not cover sidecars naming columns absent from the CSV.
3. Missing counts: empty fields become null and are counted per column; nan and inf also count as missing. Does not cover quoted fields containing only spaces.
4. Sampling: size equals --max-points, same seed gives identical rows, different seed differs, no duplicate rows, no sampling below the limit. Does not test statistical uniformity.
5. data.json: run the real command, parse with a parser that rejects NaN, check n_read, n_written and list lengths. Does not cover very large files.
6. Null for missing: a CSV with a gap writes null. Does not cover the page's handling of null.
7. HTML: every control id, every column as an option, `none` in z and colour, plotly inline, no remote script, scattergl and scatter3d strings. Does not execute the JavaScript, so log scales, dropped counts and hover text are not tested.
8. Errors: missing file, empty file, bad sidecar, no numeric columns, duplicate column names and --max-points 0 all give a clear message and exit 2. Does not cover permission errors.

## What we agreed to write, and why
- Tests 1 to 8 as planned, because each protects one of our four must-not-break items or an acceptance criterion in PLAN.md.
- We also asked for a deliberate break (switch to allow_nan=True and write NaN) to confirm the strict JSON test fails, then reverted it.
- We did not write browser tests; the JavaScript is checked by hand in the browser and listed under out of scope for the automated suite.
