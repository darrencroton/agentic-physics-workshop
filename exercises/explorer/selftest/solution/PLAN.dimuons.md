# Plan

Dataset: data/dimuons.csv

## Goal
A command-line tool that reads a CSV (with an optional columns.json sidecar) and writes a self-contained explorer.html plus data.json, so a physicist can pick X, Y, optional Z and colour columns, toggle log scales and hover over points, all offline in a browser.

## Decisions
- Values <= 0 on a log axis: the page drops those rows in JavaScript and counts them in the "n plotted (m dropped)" line, so nothing is silently hidden. Log colour uses log10 of the column and drops non-positive values the same way.
- Missing values in a selected column: rows are kept in data.json (written as null); the page drops a row only when a column currently selected (x, y, z or colour) is missing there, and reports the count.
- Initial selection when the page opens: x = first numeric column, y = second, z and colour = none; each log checkbox starts from the column's `log` flag in the sidecar (false without one) and follows it when the column changes.
- Sampling above --max-points: random sample without replacement using numpy default_rng(seed), seed 0 by default, original row order preserved, so the same seed gives the same rows.

## Design (modules and what each does)
- explorer/data.py: read the CSV and sidecar, decide which columns are numeric, count missing values, sample rows.
- explorer/page.py: build explorer.html (inline plotly.js, controls, data blob, JavaScript).
- explorer/__main__.py: command line (argparse), --list, write data.json (strict JSON) and explorer.html, clean errors.
- tests/test_explorer.py: pytest checks for the acceptance criteria.

## Steps (a numbered list of two or three, each ending in something we can run and look at)
1. data.py and __main__.py: load dimuons.csv, write data.json strictly, add --max-points sampling and the clean error for a bad path; run `make list` and `make explore` and read n_read and n_written.
2. page.py: write explorer.html with every control, 2D and 3D plots, the colour bar, log toggles, hover text and the count line; run `make open` and try each control.

## Acceptance criteria (at least three, each something we can check)
- `python -m explorer data/dimuons.csv` exits 0, prints n_read 60000 and n_written 20000, in under 5 seconds.
- data.json parses with json.loads strictly (no NaN), every list has length n_written, missing values are null.
- explorer.html contains plotly.js inline, no `<script src="http`, and every control id with one option per numeric column.
- `--max-points 500` writes exactly 500 rows; the same seed gives the same rows.
- A missing file exits non-zero with a one-line message and no traceback.

## Out of scope
Server, file upload in the page, histograms, saving images, categorical colouring, datasets beyond the two CSV examples.
