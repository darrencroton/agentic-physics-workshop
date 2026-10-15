# Explorer

## The story

Your group has a dataset and a question you can't answer from a table: **what does it look like?** You want a quick tool that lets you pick any columns as the axes of a 2D or 3D plot, colour the points by another column, and explore in a browser: rotate, zoom, hover. Nothing does exactly this for your data, so Claude will build it.

It's a prototype: quick and dirty is fine. But you'll build it the way you'd want a careful student to: **plan it, build it in checked steps, test it, and have it reviewed**, committing each step that works. Each stage is a gate.

The big idea: **a good agentic workflow is a habit, not a technique.** `PLAYBOOK.md` is that habit on one page. Every level uses one part of it, and it's yours to take home. The four skills in `.claude/skills/` (plan-code, style-code, test-code and review-code) are the same habit as Claude Code skills, used at each level and also yours to take home.

## Your dataset

The leader picks one, and it goes on the `Dataset:` line of `PLAN.md`. Both ship in `data/`, with sources and citations in `data/README.md`.

- **Pulsars** (`data/pulsars.csv`): the ATNF Pulsar Catalogue, 4,503 pulsars. Sky position, distance, Galactic `XX`, `YY`, `ZZ` (kpc), spin period `P0`, its derivative `P1`, and quantities derived from them. Many values are missing.
- **Dimuons** (`data/dimuons.csv`): 60,000 CMS muon pairs from 2010. Energy, momentum, `pt`, `eta`, `phi` and charge for each muon, and the pair's invariant mass `M`. No values are missing, and there are no text columns.

Each CSV has a column file beside it (`data/<name>.columns.json`) giving every column's unit, a description, and whether a log scale suits it.

Once `PLAN.md` is committed, the dataset on its `Dataset:` line is the only one you work with: `make explore` and every gate use it.

## What the tool must do

This interface is fixed: the gates run the tool and read its output. Everything else is your group's decision, written in `PLAN.md`.

```
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

## Roles

- **Driver:** types the prompts into Claude Code. Rotates at each gate.
- **Navigator:** owns the plan and the scope, and watches the clock. Asks "is it in the plan?"
- **Sceptic:** owns the acceptance criteria and the evidence. Nothing is committed until the Sceptic has seen the command and its output and, once the page exists, someone has looked at it.
- **Scribe:** keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment, the decisions Claude made for you.
- **Coach:** your leader. Asks questions rather than giving answers, and steps in on tooling problems.

Hands off the code: humans read, look and decide. All code changes, and all commits, go through Claude.

## Two windows, and a browser

1. **Claude window (large):** Claude Code runs here. Only the Driver types in it.
2. **Gate terminal:** a separate terminal for the humans. `./gate unlock` and `./gate hint` are typed here, and it's where you run `make open`, `make list` and `make test` yourselves. Claude never types there.
3. **Browser:** `make open` shows the page. Claude can't see it; you can.

The Claude session starts in **plan mode**: Claude reads and proposes, but changes nothing. That is where Level 0 happens. `Shift+Tab` cycles the modes, and the line under the prompt shows which one is on. When you approve a plan, Claude leaves plan mode and starts on it.

## Level 0: Plan (about 8 minutes)

No code yet. Agree a plan, write it down, commit it.

1. Read this README together.
2. In Claude (plan mode), the playbook's *Understand* and *Plan* prompts in one go:

   > "Read README.md, data/README.md and the column file for our dataset. Say what the data contains, which columns have missing values and how many, and anything unclear. Then, using the plan-code skill, propose a plan: the goal, the decisions it depends on, the design, two build steps that each end in something we can run and look at, acceptance criteria we can check, and what's out of scope. Ask me about any decision you're unsure of. Don't write any code."

   If your dataset has no missing values, the decision still matters: the tool must handle any CSV, and at Level 2 a test with a small made-up file can check it.
3. Read it. Argue about it. Change it. The four decisions in `PLAN.md` are the group's, not Claude's. The Sceptic owns the acceptance criteria (at least three, each something you can check by eye or by test). The Navigator cuts anything beyond the interface above.
4. Approve the plan and ask Claude to write it into `PLAN.md`, keeping the template's headings and the `Dataset:` line exactly as `Dataset: data/pulsars.csv` or `Dataset: data/dimuons.csv`. Then ask Claude to commit it.
5. `./gate check` names the first thing still missing. When it passes, run `./gate unlock` in the gate terminal.

## If it goes differently

- The plan has more than two steps: ask Claude to merge them into two, each ending in something you can run and look at. The split that works: the command line, `--list` and `data.json` first; then the page, with your decisions and the initial view built in. Two bigger steps get you to the page sooner, and the gate checks it.
- Claude asks something nobody knows: pick a reasonable answer, write it in `PLAN.md` and move on.
- Claude tries to write code: at this level the guard refuses everything except `PLAN.md` and `LOG.md`. Read the refusal aloud: it's on purpose.

## What to watch for

- Decisions Claude makes silently: dropping rows, clipping logs, which columns the page opens on. Each one belongs in `PLAN.md`, decided by you.
- A plan bigger than the job: class hierarchies, config systems, a build step for the JavaScript. It's a prototype.
- A step that ends in nothing you can see, such as "set up the package". Each step should end in a command you can run.

## Opening the gate

`./gate check` needs every section of `PLAN.md` filled in: the four decisions answered, two steps, at least three acceptance criteria, and at least 1 commit with `PLAN.md` committed.

The reflection (logged): one thing in Claude's plan you changed, and why.

When the check passes: `./gate unlock`.

## Commands

| Command | Where | What it does |
|---|---|---|
| `make explore` | Claude or gate terminal | Runs the tool on the `PLAN.md` dataset into `out/` (once Claude has built it) |
| `make explore DATA=path/to/other.csv` | Either | Runs it on another CSV |
| `make open` | Gate terminal | Opens `out/explorer.html` in your browser |
| `make list` | Either | Lists the columns, units and missing counts (once the tool has `--list`) |
| `make test` | Either | Runs the tests (`pytest -q`) |
| `make coverage` | Either | Runs the tests and shows the lines no test runs |
| `make status` | Either | Same as `./gate status` |
| `./gate status` | Either | Level, time on level, hints used, dataset, commits since the last gate |
| `./gate brief` | Either | Shows the current level brief |
| `./gate check` | Either | Runs the level's check and names the first thing missing |
| `./gate hint` | Gate terminal | A hint (three tiers, unlocking as the level goes on; where the gate asks a question, a fourth gives the answer) |
| `./gate unlock` | Gate terminal | Checks your work, asks the gate question, opens the next level |
