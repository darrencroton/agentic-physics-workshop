# The tool interface

This is the fixed part of the tool. The gates run it and read its output, so it never changes, at any level. Everything else is your group's decision, written in `PLAN.md`.

## What the tool must do

```text
.venv/bin/python -m explorer DATA.csv [--out DIR] [--max-points N] [--seed S]
.venv/bin/python -m explorer DATA.csv --list
```

| | |
|---|---|
| Any CSV | `DATA.csv` is any comma-separated file with a header row. If `DATA.columns.json` sits beside it, use its units, descriptions and log suggestions. Without it, a column with at least one value, every one of them a number, is numeric, units and descriptions are blank and no log scale is suggested. A missing file, or one with no numeric columns, gives a clear message and a non-zero exit, not a traceback. |
| Missing values | An empty field is a missing value. Every row is kept; the page leaves out a row only when a *selected* column is missing there, and says how many it left out. |
| Size | At most `--max-points` rows are written (default 20,000), picked at random without replacement using `--seed` (default 0) when the file is larger. The tool prints how many rows it read and wrote. |
| Output | `DIR/explorer.html` and `DIR/data.json`. `DIR` defaults to `out/`. |
| `--list` | Prints each column with its unit, description and number of missing values, and exits 0. |

**`data.json`** is the machine-readable twin of the page:

```json
{
  "source": "data/example.csv",
  "n_read": 3,
  "n_written": 3,
  "columns": [
    {"name": "E", "unit": "J", "description": "Energy", "log": true},
    {"name": "theta", "unit": "deg", "description": "Angle", "log": false}
  ],
  "rows": {"E": [0.5, 12.0, null], "theta": [253.4, 184.6, 10.2]},
  "labels": {"name": ["a", "b", "c"]}
}
```

- `columns` lists every numeric column, in CSV order. `rows` has one list per numeric column, with the same names in the same order; a missing value is `null`. `labels` holds the text columns (it may be empty).
- It must be strict JSON: no `NaN` or `Infinity`. Python's `json.dumps` writes them unless you pass `allow_nan=False`.
- `n_written` is the length of every list, at least 1 and at most `--max-points`.

**`explorer.html`** is one self-contained page: plotly.js inline (from `plotly.offline.get_plotlyjs()`; no `<script src="http...">`), the data inline, and these controls, written as plain HTML `<select>` and `<input type="checkbox">` elements with every `<option>` in the file Python writes (the gate reads the file as text and does not run JavaScript):

| Control | id | Options |
|---|---|---|
| X axis | `x` | every numeric column (`<option value="E">` and so on) |
| Y axis | `y` | every numeric column |
| Z axis | `z` | `none` plus every numeric column; `none` gives a 2D plot |
| Colour | `colour` | `none` plus every numeric column; a column adds a colour bar titled with its name and unit |
| Palette | `palette` | at least three Plotly colour scales |
| Log X, Y, Z, colour | `logx`, `logy`, `logz`, `logc` | checkboxes; defaults from the column file |

Axis titles show the column name and unit. Hovering a point shows every numeric column of that row with units, and the label if there is one. 2D plots use WebGL (`scattergl`); 3D plots use `scatter3d`. A line of text says how many points are plotted and how many rows were left out for the current selection. What happens to a value of zero or below on a log axis, and what the page shows when it first opens, are yours to decide in `PLAN.md`.
