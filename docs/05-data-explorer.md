# Exercise E — Explorer: Plan, Build, Test, Review

> **Design document and record.** Version 2 (2026-10-13), after the facilitator's review of version 1. This is the design the exercise is built from. Once built, `exercises/explorer/FACILITATOR-WALKTHROUGH.md` is the operating guide and supersedes the "Group leader guide" here; deviations found during the build go to [`DECISIONS.md`](DECISIONS.md). Section 12 records the decisions taken in this revision and the alternatives not chosen, so the reasoning is not lost.

| | |
|---|---|
| **One-liner** | Have Claude build a small browser tool that plots any columns of a real physics dataset against each other, in 2D or 3D, coloured by any other column, with the axes chosen from drop-down menus. Do it the way the lecture says to: plan, build in checked steps, test, review, committing as you go. |
| **Core lesson** | **A good agentic workflow is a habit, not a technique:** plan before code, build in small verified steps, ask what the tests will and won't cover, get a fresh pair of eyes, and own every decision. |
| **Model** | Sonnet (Section 12, decision 1). The lesson is the workflow, not supervising a weak model. |
| **Duration** | 42 min core (8 + 18 + 8 + 8) + 3 min contingency = the 45-minute hands-on block |
| **Group size** | 2–5 |
| **Languages** | Python (numpy, plotly, pytest, pytest-cov in the venv); a little JavaScript inside one HTML page |
| **Prep effort** | Low to moderate: two frozen datasets with column metadata, four structural check scripts, briefs, personas, three templates, the playbook and a reviewer agent. No planted bugs, no hidden assets. |

### How this differs from Exercises A–D

A–D each drill one discipline in depth (debugging, measurement, oracles, TDD), with planted bugs and gates that test the physics. Exercise E is deliberately lighter and broader. Participants are not taught *how* to test or review; they are shown *that* each step belongs in the workflow, by doing each one once with the agent and seeing what it catches. The group builds something they would actually use, watches how an agent goes about it, and leaves with a short reusable playbook (Section 6) that they can apply to their own code the next day.

Consequences for the design:

- **Persona:** `collaborator` at every level. Claude behaves normally and helpfully; each level's injected brief enforces only the step (plan only; one step at a time; test plan before tests; review before fixes).
- **Gates check that the step happened, not that it was done expertly.** The machine checks are structural; the human questions are mostly logged reflections. One graded question (Level 1) sends a human to look at the result in a browser; it prompts a look rather than proving one (Section 12).
- **Guess first, then ask.** At the test and review steps the group writes its own list before asking Claude for one, then compares. The comparison is the lesson.
- **Version control is part of every level.** Each gate requires new commits since the previous gate and a clean tree.
- **The playbook is the product.** Every brief quotes the playbook prompt for that step, so by the end the group has used every prompt once.

---

## 1. The Story (What Attendees See)

> Your group has a dataset and a question you can't answer from a table: **what does it look like?** You want a quick tool that lets you pick any columns as the axes of a 2D or 3D plot, colour the points by another column, and explore in a browser: rotate, zoom, hover. Nothing exists that does exactly this for your data, so you'll have Claude build it.
>
> It's a prototype: quick and dirty is fine. But you'll build it the way you'd want a careful student to: **plan it, build it in checked steps, test it, and have it reviewed**, committing each step that works. Each step is a gate.

Each group works on one dataset, chosen by the leader (Section 3.4); the tool must not care which. Running

```
make explore
make open
```

builds `out/explorer.html` from the group's dataset and opens it. The page has drop-down menus for X, Y, Z (or none), colour (or none) and palette, and log toggles per axis. Choosing `XX`, `YY`, `ZZ` on the pulsar catalogue shows the Galactic disc and the crowd of known pulsars around the Sun; choosing `M` against `pt1` on the dimuon events, with log axes, shows the J/ψ, ϒ and Z as sharp bands.

---

## 2. Learning Objectives

By the end, every group member should be able to:

1. **Use plan mode to agree a plan before any code exists**, and edit the agent's plan rather than accept it.
2. **Write acceptance criteria** the group can check, before building.
3. **Direct a build in two checked steps**, asking for the command and output at each step, looking at the result themselves, and committing each step that works.
4. **Say what the tests should cover before asking the agent**, then ask the agent for its test plan and what it will *not* cover, and compare the two.
5. **Get an independent review** from a fresh context, after predicting what it will find, and triage each finding as FIX, ACCEPT or REJECT with a reason.
6. **Recognise the red flags** of agentic coding: claimed success without output, tests changed to pass, code outside the plan, confident recall of an API.
7. **Take the playbook home** and use it on their own code.

---

## 3. Repo Design

```
explorer/                       # the participant repo (dist/explorer/)
├── README.md                   # Level 0 brief: story, the interface (3.1), roles, two windows, commands
├── PLAYBOOK.md                 # the take-home script (Section 6); frozen
├── PLAN.md                     # template with headings to fill (3.5); names the dataset
├── LOG.md                      # Scribe template
├── TESTS.md                    # appears at Level 2 (3.5)
├── REVIEW.md                   # appears at Level 3 (3.5)
├── Makefile                    # explore | open | list | test | coverage | status
├── requirements.txt            # numpy, plotly, pytest, pytest-cov (pinned)
├── CLAUDE.md                   # Section 7
├── gate  preflight
├── data/
│   ├── README.md               # sources, citations, licences, the sidecar format
│   ├── pulsars.csv             # ATNF catalogue snapshot (3.4)
│   ├── pulsars.columns.json    # per column: unit, description, suggested log scale
│   ├── dimuons.csv             # CMS Run2010B dimuon events (3.4)
│   └── dimuons.columns.json
├── explorer/__init__.py        # empty package. Claude builds the rest.
├── tests/__init__.py           # empty. Claude writes the tests at Level 2.
├── out/                        # generated: explorer.html, data.json (gitignored)
├── .claude/agents/reviewer.md  # the fresh-context reviewer (Section 8)
└── .claude/ …  .gatekit/ …  .vault/level{1..3}.pack  .workshop/ …
```

**Design notes:**

- **Claude writes all of `explorer/` and `tests/`.** Nothing is provided beyond the interface, the data and the column metadata. Watching how the agent structures a small tool from nothing is part of the point.
- **Only the interface is fixed** (3.1–3.3), so the checks can run the tool and read its output without knowing how it is built. Internals (module layout, how the page is wired, how missing values and log scales are handled) are the group's decisions, recorded in `PLAN.md`.
- **The plotting happens in the browser.** Python prepares the data and writes one self-contained HTML page; the page holds the data, plotly.js and a few lines of JavaScript that read the drop-downs and redraw. This is what makes "choose any column from a menu" cheap: no Python runs when a menu changes.
- **`data.json` is the machine-readable twin of the page.** The checks read it and inspect the HTML's structure; no check needs a browser. The browser is for the humans, which is the point of the Level 1 question.
- **Offline.** The page embeds plotly.js from the installed package, so it opens with no network.
- **Runtime:** `make explore` should take under 5 s on either dataset, so groups iterate freely.

### 3.1 Interface (Fixed; Stated in the README)

```
.venv/bin/python -m explorer DATA.csv [--out DIR] [--max-points N] [--seed S]
.venv/bin/python -m explorer DATA.csv --list
```

| Requirement | Detail |
|---|---|
| Any CSV | `DATA.csv` is any comma-separated file with a header row. If `DATA.columns.json` exists beside it (format in `data/README.md`), its units, descriptions and suggested log scales are used; otherwise every column that parses as numeric is numeric, units are blank and no log scale is suggested. A file that does not exist or has no numeric columns is a clear error, not a traceback. |
| Missing values | An empty field is a missing value. Rows are kept; the page drops a row only when a *selected* column is missing there, and says how many it dropped. |
| Size | At most `--max-points` rows (default 20,000) are written, chosen at random with `--seed` (default 0) when the file is larger. The numbers read and written are printed. |
| Output | `DIR/explorer.html` and `DIR/data.json` (3.2); `DIR` defaults to `out/`. |
| `--list` | Prints each column with its unit, description and number of missing values, and exits 0. |

`make explore` wraps the command on the dataset named in `PLAN.md` (`Dataset:` line); `make explore DATA=path/to/other.csv` overrides it. `make open` runs `open out/explorer.html`, `make list` runs `--list`, `make test` runs `pytest -q`, `make coverage` runs `pytest --cov=explorer --cov-report=term-missing`, and `make status` runs `./gate status`.

### 3.2 `data.json` (Fixed)

```json
{
  "source": "data/pulsars.csv",
  "n_read": 4503,
  "n_written": 4503,
  "columns": [
    {"name": "P0", "unit": "s", "description": "Spin period", "log": true},
    {"name": "GL", "unit": "deg", "description": "Galactic longitude", "log": false}
  ],
  "rows": {"P0": [0.00575, 0.0331, null], "GL": [253.4, 184.6, 10.2]},
  "labels": {"JNAME": ["J0437-4715", "B0531+21", "J1748-2446ad"]}
}
```

- `columns` lists every numeric column in CSV order; `rows` has one equal-length list per numeric column; a missing value is `null`. `labels` holds the non-numeric columns (may be empty).
- Strict JSON: no `NaN` or `Infinity` tokens (`json.dumps(..., allow_nan=False)`). The check parses it strictly. This is the one technical trap in the exercise, and it is a real one: Python's default serialiser happily writes invalid JSON.
- `n_written` equals the length of every list, is at least 1 and at most `--max-points`.

### 3.3 The Page (Fixed Controls; Everything Else Free)

`explorer.html` is self-contained: plotly.js inline (no `<script src="http…">`), the data inline, and ordinary HTML controls with these ids, so that the check can find them and the group can read the page's own code:

| Control | id | Options |
|---|---|---|
| X axis | `x` | every numeric column |
| Y axis | `y` | every numeric column |
| Z axis | `z` | `none` + every numeric column; `none` gives a 2D plot |
| Colour | `colour` | `none` + every numeric column; a column adds a colour bar titled with the column and unit |
| Palette | `palette` | at least three Plotly colour scales |
| Log X, Y, Z, colour | `logx`, `logy`, `logz`, `logc` | checkboxes; defaults from the column metadata |

Axis titles show the column name and unit. Hovering a point shows every numeric column of that row with units, and the label column if there is one. 2D plots use WebGL scatter (`scattergl`); 3D plots use `scatter3d`. A line of text on the page says how many points are plotted and how many rows were dropped for the current selection.

What happens to a value ≤ 0 on a log axis, and what the initial selection is, are the group's decisions and must be stated in `PLAN.md`.

### 3.4 Datasets

Each group is given **one** dataset by the leader, who runs the workshop once for an astro audience and once for a particle audience; both ship in every repo, but once the plan is committed the group, the briefs and the gates use only theirs. The tool must not care which; the stretch is to point it at a CSV from the group's own research.

**Astro track: ATNF pulsars** (`pulsars.csv`, catalogue v2.9.0, 4,503 rows).

| Columns | Notes |
|---|---|
| `JNAME` | String; label only |
| `XX`, `YY`, `ZZ` (kpc) | Galactocentric Cartesian, right-handed, Sun at (0, 8.5, 0) kpc, `ZZ` towards the north Galactic pole (psrcat convention). Real 3D structure: the disc, the crowd around the Sun (a selection effect), globular-cluster clumps well off the plane. |
| `GL`, `GB` (deg), `DIST`, `DIST_DM` (kpc) | Sky position and distances |
| `P0` (s), `P1`, `DM` (cm⁻³ pc), `AGE` (yr), `BSURF` (G), `EDOT` (erg/s) | Spin and derived quantities; the P–Ṗ diagram is `P0` against `P1` with both logs on |

Many rows lack `P1` and the derived columns (about 1,500 of each) and 74 have no distance; psrcat places those 74 at the Sun's position, so the build blanks their `XX`, `YY`, `ZZ` rather than plant fake points at the Sun. The missing-value policy matters here. A few `P1` values are zero or negative (globular-cluster pulsars), which makes the log-axis decision real. The catalogue (Manchester et al. 2005, AJ 129, 1993) and its URL are acknowledged in `data/README.md`.

**Particle track: CMS dimuons** (`dimuons.csv`, the first 60,000 of the 100,000 Run2010B events, CC0; the full file is 15 MB and 60,000 rows keep the repo small while still exercising sampling). Two muons per event from the Run2010B `Mu` dataset, invariant mass 2–110 GeV: per muon `E`, `px`, `py`, `pz`, `pt`, `eta`, `phi`, `Q`, plus the pair's invariant mass `M`. `M` against `pt1` with log axes shows the resonances as sharp vertical bands; `eta1` against `phi1` coloured by `M` shows the detector. The row count exercises `--max-points` sampling.

**Not chosen:** the GWTC catalogue (a few hundred events, no spatial structure); a synthetic xenon TPC dataset (most spatial structure, but not real data; Section 12).

### 3.5 Templates

**`PLAN.md`**, shipped at Level 0; the Level 0 check requires every section filled.

```markdown
# Plan

Dataset: data/pulsars.csv
<!-- The leader sets the Dataset line: data/pulsars.csv or data/dimuons.csv. -->

## Goal
## Decisions
- Values <= 0 on a log axis:
- Missing values in a selected column:
- Initial selection when the page opens:
- Sampling above --max-points:
## Design (modules and what each does)
## Steps (two, each ending in something we can run and look at)
## Acceptance criteria (at least three, each something we can check)
## Out of scope
```

**`TESTS.md`**, appears at Level 2.

```markdown
# Tests

## Our list (before asking Claude): things that must not break
-
-
-

## Claude's plan: each test, what it checks, and what it will not cover
(Claude writes it here)

## What we agreed to write, and why
```

**`REVIEW.md`**, appears at Level 3.

```markdown
# Review

## Our guesses (before the review): what we think a reviewer will find
-
-

## Findings (from the reviewer), triaged by us

| # | Finding | Severity | Decision (FIX / ACCEPT / REJECT) | Reason |
|---|---|---|---|---|
|   |         |          |                                  |        |

## What the review found that the tests did not
```

---

## 4. Levels

| Level | Title | Min | Gate: machine check | Gate: human question |
|---|---|---|---|---|
| 0 | Plan | 8 | `PLAN.md` complete (3.5) and committed; ≥ 1 commit since `start` | Logged: "One thing in Claude's plan you changed, and why." |
| 1 | Build the prototype | 18 | The tool runs on the group's dataset (3.1–3.3); ≥ 2 commits since Level 0; clean tree | **Graded:** a question that prompts a look in the browser |
| 2 | Test | 8 | `TESTS.md` both lists filled; ≥ 5 tests pass, importing `explorer`; ≥ 1 commit; clean tree | Logged: "What did Claude's plan cover that yours didn't, or the reverse?" |
| 3 | Review (last) | 8 | `REVIEW.md`: ≥ 2 guesses, ≥ 3 triaged findings; tests pass; the tool runs on the group's dataset; ≥ 1 commit; clean tree | Logged: "What did the review find that the tests didn't?" |

All gates are `crypto-reflection` except Level 1 (`crypto`, one keyword question). Check scripts live in `.gatekit/exploretool/checks/levelN.py` (the manifest names that path, relative to the repo root), run under the venv Python, print one diagnostic sentence to stderr on failure and, on success, a fixed line, as in the Speed Run. Their slot secret is therefore the human answer (or nothing); that is the documented honest limit and is acceptable here. The Level 3 gate marks completion.

**Version control at every gate.** At each unlock the tool records `HEAD`. The next check requires the stated number of new commits since that record (`git rev-list --count`) and a clean tree for the paths it checks (`git status --porcelain`). Every brief ends with "commit, then unlock". Humans do not touch code, so Claude makes the commits when asked; the guard already allows `git add` and `git commit`.

### Level 0 — Plan (8 min)

**Brief:** "Read the README together. Then, in plan mode, give Claude one prompt: read the interface and your dataset's column file, say what the data contains and which columns have missing values, and propose a plan. Read it, argue about it, change it, save it as `PLAN.md`, and commit it. No code yet."

**Playbook prompts used:** *Understand* and *Plan* (Section 6).

**What the group does:**

- Starts in plan mode (the default in these repos). Gives Claude one prompt that combines *Understand* and *Plan*: summarise the data and the interface, say which columns have missing values and how many (`make list` only works once the tool exists, so at this level Claude reads the column file and counts), list anything unclear, and propose the plan.
- Has Claude draft the plan, then makes the four decisions in `PLAN.md` as a group. The Sceptic owns the acceptance criteria. The Navigator cuts scope: the plan is for the prototype in 3.1–3.3 and nothing more.
- Asks Claude to commit `PLAN.md`.

**Typical behaviour:** Claude produces a competent, generic plan and makes the decisions silently (drop rows with missing values, clip logs, plot the first two columns). Some plans over-engineer (a class hierarchy, a config system, a build pipeline for the JavaScript). The Navigator cuts.

**Guard:** editable `PLAN.md`, `LOG.md` only.

**Gate:**

- *Machine:* every section of `PLAN.md` filled beyond the template text; `Dataset:` names one of the two shipped files; all four decisions stated; at least three acceptance-criteria bullets; at least one commit since `start`; `PLAN.md` not modified since that commit.
- *Human (logged):* "One thing in Claude's plan you changed, and why."

**Teaching point:** the plan is where the decisions are visible and cheap to change. An agent will always make them; the question is whether you saw them.

**Hints:**

1. "If Claude hasn't said which columns have missing values and how many, ask."
2. "What should the page do with a zero on a log axis, or a row whose colour column is missing? Write it down."
3. "Acceptance criteria are things you could check by eye or by test: 'the 3D view rotates', 'hovering shows the unit', 'the dropped-row count changes when I pick P1'. Then: 'commit PLAN.md'."

### Level 1 — Build the prototype (18 min)

**Brief:** "Build it, one step of the plan at a time (two steps). After each step, ask for the command and its output and what you can run to check it, run that yourselves (once the page exists, `make explore` then `make open`), and commit. When `./gate check` passes, play with the page for a minute and agree one feature the group would add. Keep it for later; it goes in the reflection."

**Playbook prompts used:** *Build in checked steps*; *Evidence*.

**What the group does:**

- Leaves plan mode. Has Claude implement step 1 only (loading data and `--list`), run it, show the output, commit.
- Steps through the plan; opens the page after each visible change; rotates, zooms, hovers, switches columns and palettes, toggles logs.
- Runs `./gate check` early and often: it names the first thing that is missing.
- After the check passes, the one-minute play and one agreed feature. It is logged, not built; a group with time after Level 3 may build it.

**Typical behaviour:**

- Claude tries to build everything in one go. The Driver stops it (`Esc`) and asks for one step.
- Claude says "this should now work" without running it. The Sceptic asks for the command and output.
- Claude recalls a Plotly API detail wrongly (the hover template, the colour-bar title, the shape of a WebGL trace). The prompt "check the installed version's documentation" is worth a minute here.
- `data.json` contains `NaN` and the check rejects it as invalid JSON. Two minutes of real debugging, on a mistake Python makes easy.
- The hover shows the wrong row after sampling, or the colour bar has no unit. Humans looking at the browser catch these; the check catches some.

**Guard:** editable `explorer/**`, `PLAN.md`, `LOG.md`. `tests/**` frozen (testing is the next step).

**Gate:**

- *Machine:* the check runs the tool on the dataset named in `PLAN.md`, into a temporary directory: once with defaults, once with `--max-points 500`, once with `--list`, and once on a file that does not exist. It requires: exit 0 within 30 s for the valid runs; a non-zero exit and no `Traceback` for the invalid one; `--list` naming every column in the sidecar; `data.json` valid under strict parsing with the structure in 3.2 and `n_written` equal to 500 on the sampled run; and `explorer.html` containing plotly.js inline, no external script, the controls in 3.3 with every numeric column as an option, and the strings `scattergl` and `scatter3d`. Also ≥ 2 commits since the Level 0 unlock and a clean tree under `explorer/` and `PLAN.md`.
- *Human (graded, keyword):* asked only for the group's dataset (gatekit `text_from` reads the `Dataset:` line; a neutral static prompt is the fallback), with a dataset hint after a wrong answer (`wrong_hint`). Pulsars: "Plot `XX`, `YY` and `ZZ` in 3D and rotate it: the known pulsars crowd around one point. What is at that point?" Dimuons: "Plot `M` against `pt1` with log axes: there is a sharp band near M = 3.1 GeV. Which particle makes it?" Accept `sun`, `solar system`, `earth`, `us`, `solar neighbourhood`, `jpsi`, `j/psi`, `jψ`, `psi`, each also with an article ("the sun", "the j/psi") since keyword matching keeps articles. Both sets are accepted for either dataset (honest limit; Section 12).

**Teaching point:** the agent cannot see the browser. The humans are the only ones who can check what the tool actually shows, and the check only knows what can be read from a file.

**Hints:**

1. "Ask for one step, the command and its output, and what you can run to check it. Run that, look, then commit."
2. "`./gate check` prints the first thing that is missing. Paste that line to Claude."
3. Dataset-specific: "Where is the Sun in this coordinate system? Look in `pulsars.columns.json`." / "Put `M` on X with log on. The dense vertical lines are particles."

### Level 2 — Test (8 min)

**Brief:** "Before you ask Claude anything, write three things in `TESTS.md` that must not break. Then ask Claude for a plan of five to eight tests, one line each, with the coverage and what it won't cover, written under "Claude's plan" in `TESTS.md`. Compare the two lists, agree what to write. Then have it write and run them, commit, and run `make test` yourselves in the gate terminal."

**Playbook prompts used:** *Test plan, then tests*; *Does the alarm ring?*

**What the group does:**

- The Scribe writes the group's list first (two minutes, no Claude).
- Asks for a plan of five to eight tests, with coverage and what it cannot cover, written straight into `TESTS.md`, and does not let Claude write tests (or run unasked experiments) until the group says go. The obvious gap, that pytest cannot see what the page does in the browser, is the discussion to have: what *can* be tested (the data preparation, `data.json`, the HTML's structure) and what needs a human.
- Runs `make test` and, if there is time, `make coverage` in the gate terminal, and reads the missing-lines report together.
- Optional, one minute: asks Claude to break one thing on purpose (drop the unit from a title, write `NaN` into `data.json`), runs the tests, sees whether they fail, then reverts. A test that never fails proves nothing.

**Typical behaviour:**

- Claude writes tests immediately unless held to the plan; the level brief tells it to wait.
- Claude tests the easy pure functions and leaves the page untested; coverage shows it.
- If a test fails, Claude may change the test to pass. The brief forbids it; the Sceptic watches for it. A failing test is a finding: fix the code, or decide the test was wrong and say why.

**Guard:** editable `tests/**`, `explorer/**`, `TESTS.md`, `LOG.md`.

**Gate:**

- *Machine:* `TESTS.md` has at least three bullets under "Our list" and non-template text under "Claude's plan"; `pytest` collects at least five tests, all pass, and at least one test module imports `explorer`; ≥ 1 commit since the Level 1 unlock; clean tree under `explorer/`, `tests/` and `TESTS.md`.
- *Human (logged):* "What did Claude's plan cover that yours didn't, or the reverse?"

**Teaching point:** asking for the test plan and its coverage before the tests is cheap and changes what you get. Writing your own list first tells you what you would have missed.

**Hints:**

1. "Ask: 'Talk me through the five to eight tests this code needs, one line each, with the coverage and what it won't cover. Write the plan under Claude's plan in TESTS.md. Don't write the tests yet.'"
2. "Run `make coverage`. Which lines are never run by a test?"
3. "Ask Claude to break one thing deliberately and run the tests. Do they notice? Then revert."

### Level 3 — Review (8 min, last level)

**Brief:** "Before you ask, write two things in `REVIEW.md` that you think a reviewer will find. Then ask Claude for a review from the `reviewer` agent (a fresh context that has not seen this conversation) and to paste the findings into `REVIEW.md`. Decide the top three to five yourselves (FIX, ACCEPT or REJECT, one line of reason), and fix the top FIX item (more if there is time) with a test that fails before the fix, running the tests after. Commit, then unlock."

**Playbook prompts used:** *Independent review*; *Triage*.

**What the group does:**

- Writes the guesses first (one minute).
- Asks Claude to "use the reviewer agent to review the code since `start` against `PLAN.md`; rank the findings by severity and paste them into the table in `REVIEW.md`; don't fix anything". The agent is shipped in the repo (Section 8) and returns three to five ranked findings, which Claude pastes into `REVIEW.md` in the same prompt.
- Compares guesses with findings, triages, fixes.
- Groups with time left: the brief's Finished early section offers, after the unlock, the Level 1 feature or two others, built the same way (one step, run it, look, commit): a day/night button that switches the page between light and dark colours, or mouse selection of points (box or lasso, in the 2D view) that shows how many were picked, with their labels if the dataset has them. The completion message says "This is yours to take home" and points at `PLAYBOOK.md`.

**Typical behaviour:** the reviewer finds real issues in 20 minutes of agent-built code: the ≤ 0 log policy not implemented as planned, hover misaligned after sampling, a missing error for a CSV with no numeric columns, duplicated loading code, a unit missing from a title. It also reports noise (style, speculative performance). Rejecting a finding with a reason is as valuable as fixing one.

**Guard:** editable `REVIEW.md`, `explorer/**`, `tests/**`, `LOG.md`.

**Gate:**

- *Machine:* `REVIEW.md` has at least two guess bullets and at least three table rows each with a decision in {FIX, ACCEPT, REJECT} and a non-empty reason; tests still pass; the Level 1 run checks pass on the `PLAN.md` dataset; ≥ 1 commit since the Level 2 unlock; clean tree.
- *Human (logged):* "What did the review find that the tests didn't?"

**Teaching point:** the author grading its own work is not a review. A fresh context finds different things, and some of what it finds is wrong: the human decides.

**Hints:**

1. "Ask: 'Use the reviewer agent to review the code since start against PLAN.md. Rank the findings and paste them into the table in REVIEW.md, most severe first. Don't fix anything.'"
2. "Triage the top three to five: does each matter for a prototype? FIX, ACCEPT or REJECT, and one line why. The rest can wait."
3. "Fix one FIX item with a test that fails first, run `make test`, commit. Then the next, if there is time."

---

## 5. What the Lecture Teaches and Where the Exercise Does It

The lecture (docs/00, Slide 4) teaches the Verify-First Loop. Every step of it is done once here, with the same name, so the cheat card on the table, the briefs and the take-home playbook agree.

| Loop step (lecture) | Level | Playbook prompt | What the gate checks |
|---|---|---|---|
| Understand | 0 | *Understand* | — (the plan shows it) |
| Define the check | 0, 2 | *Plan* (acceptance criteria); *Test plan, then tests* | Acceptance criteria in `PLAN.md`; the group's own list in `TESTS.md` |
| Plan | 0 | *Plan* | `PLAN.md` complete and committed |
| Small steps | 1 | *Build in checked steps* | ≥ 2 commits during the build (the plan has two steps) |
| Evidence | 1, 2 | *Evidence*; *Does the alarm ring?* | The tool runs; the tests run; a human looked (the graded question) |
| Independent review | 3 | *Independent review*; *Triage* | Findings triaged with reasons |
| Recover | any | *Recover* | — (hints and the leader) |

The failure-mode table on Slide 5 maps onto the red flags in the playbook and the "things worth noticing" in Section 9.

---

## 6. The Take-Home Playbook (`PLAYBOOK.md`)

Shipped from Level 0, frozen, quoted in every brief. It stands alone: one page, no workshop references, usable on any codebase next week. Its headings are the lecture's loop steps.

```markdown
# Working With a Coding Agent: a Playbook

The agent is a fast, tireless, literal collaborator. You own the decisions and the result.

## 0. Set up
- Put the project's facts in CLAUDE.md: what it is, how to run it, how to test it,
  conventions. Keep it short. `/init` drafts one.
- Use git. One change, one check, one commit. Any step can then be undone.

## 1. Understand (plan mode: Shift+Tab until "plan mode on")
"Read <files>. Summarise what the code and data contain and what the task asks.
 List anything unclear or ambiguous. Don't write any code."

## 2. Define the check, then plan
"Propose a plan: the goal, the decisions it depends on, the design, a few steps
 (two or three for a small job) that each end in something we can run and look at,
 acceptance criteria we can check, and what's out of scope. Ask me about any
 decision you're unsure of."
- Read it. Change it. The decisions are yours. Save it as PLAN.md. Commit it.

## 3. Build in checked steps
"Implement step 1 of PLAN.md only. Run it, show me the exact command and output,
 and tell me what I can run to check it myself."
- Run that yourself and look at the result. Commit. Then: "Next step."
- Stop it (Esc) if it starts doing more than one step.

## 4. Evidence: test plan, then tests
- First write your own list: three things that must not break.
"Talk me through the tests this code needs: what each one checks, what coverage
 that gives, and what it won't cover. Don't write them yet."
- Compare with your list. Agree. Then:
"Write them. Run them and show me the output."
- Run them yourself. Look at the coverage report.
"Break <one behaviour> on purpose and run the tests. Do they fail? Then revert."
- Never accept a test changed just to make it pass.

## 5. Independent review
- First write your own guess: two things a reviewer will find.
"Use a subagent with no context from this session to review the code against
 PLAN.md. Rank the findings by severity. Don't fix anything."
  (or /code-review, which does the same on the current diff)
- Decide the findings that matter: FIX, ACCEPT or REJECT, with a reason.
  Many low ones? Triage the top few; the rest can wait.
"Fix the FIX items one at a time. For each, add a test that fails before the fix
 and passes after, then run the tests." Commit each.

## 6. Recover
- Esc stops it. Esc Esc or /rewind undoes. After two failed corrections: /clear and
  write a better prompt that includes what you learned.

## Red flags
- "Done" or "all tests pass" with no command and output shown.
- A test or tolerance changed to make a failure go away.
- Code that does more than the plan says.
- Confident use of a library API: "check the installed version's documentation".
- You can't explain what the code does. Ask it to, then check.

## Make it stick (optional)
- A reviewer agent: copy .claude/agents/reviewer.md from this repo into your project.
- A Stop hook that runs your tests, so the agent cannot finish with them failing
  (exit code 2 blocks; a failing pytest exits 1, so wrap it):
  {"hooks": {"Stop": [{"hooks": [{"type": "command",
    "command": "sh -c 'cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/pytest -q || exit 2'"}]}]}}
  in .claude/settings.json. Add it once tests exist.
```

The hook syntax and `/code-review` behaviour were verified against the Claude Code docs on 2026-10-13 (Claude Code 2.1.296; `DECISIONS.md`).

---

## 7. Teacher Instructions (Draft `CLAUDE.md`)

```markdown
# Workshop: Explorer

You are helping a group of physicists build a small data-exploration tool while they
practise a workflow: plan, build in steps, test, review, committing as they go. Be a
normal, capable collaborator. The current level and its rules are injected with each
prompt; follow them.

## Always
- Show the exact command and its output for anything you run. Never claim a result
  you have not run.
- Explain as you go: before each change or command, say in two or three sentences what
  you will do and why; after a run, say in one or two sentences what it showed. Define a
  term on first use. No essays.
- When unsure how a library behaves, check the installed version's documentation or
  source, and say so.
- The humans view the result in the browser. Tell them what to look for.
- Commit when asked, with a one-line message saying what the step did. Use git add and
  git commit only.

## Never
- Change a test or the interface just to make something pass. If a test looks wrong,
  say so and stop.
- Edit data/, README.md, PLAYBOOK.md, CLAUDE.md, the Makefile or requirements.txt.
- Read .vault/, .workshop/, .gatekit/ or .claude/. Run ./gate unlock, hint, skip,
  reset or allow-model. Install packages. Use pty, script or expect.
```

**Per-level injected briefs** (`persona.txt`, all `collaborator`, each with the "Explain as you go" paragraph and the "Never" list as in the Speed Run):

- **L0:** `LEVEL 0 (collaborator). Planning only: do not write code. Help the group understand the data and the interface, and draft PLAN.md. Surface every decision you would otherwise make silently, and ask the group to make it. Commit PLAN.md when asked.`
- **L1:** `LEVEL 1 (collaborator). Build PLAN.md one step at a time. After each step, run it, show the command and output, tell the group what to look for in the browser, and stop. Commit when they say the step works. Do not write tests yet. Do not start the next step until asked.`
- **L2:** `LEVEL 2 (collaborator). Before writing any test, give a short plan of five to eight tests, one line each, with the coverage it gives and what it will not cover, and write it into TESTS.md when asked. Wait for the group's go; no unasked experiments. Then write and run the tests and commit. If a test fails, report it and propose a fix to the code or say why the test is wrong; never weaken a test to pass.`
- **L3:** `LEVEL 3 (collaborator). Review first, fix later. When asked for a review, use the reviewer agent and paste its findings, ranked by severity, into REVIEW.md without changing code. Fix only the top item the group marks FIX (more if they ask), with a test that fails before the fix, running the tests and committing after.`

---

## 8. The Reviewer Agent (`.claude/agents/reviewer.md`)

A custom subagent shipped in the participant repo. A subagent starts with a fresh context (only its own prompt, the task message and `CLAUDE.md`), which is exactly the "fresh pair of eyes" the lecture asks for, and its output is text that Claude can paste into `REVIEW.md`. The built-in `/code-review` also runs as a fresh-context subagent but prints to the conversation and cannot be told to write a file, so it is the playbook's one-liner for home, not the default here.

```markdown
---
name: reviewer
description: Fresh-context code reviewer. Reviews the changes since the start tag against PLAN.md and returns ranked findings. Never edits.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are reviewing a small prototype written in the last half hour. You have not seen
the conversation that produced it; judge the code and PLAN.md only.

1. Read PLAN.md and README.md. Run `git diff start --stat` and read every changed or
   new file under explorer/ and tests/.
2. Find real problems: behaviour that contradicts PLAN.md or the README's interface,
   wrong or missing error handling, a hover or colour that could show the wrong row,
   invalid JSON, a test that cannot fail, duplicated or dead code.
3. Report between three and five findings, ranked by severity, as a Markdown table with
   columns: #, Finding (file and line), Severity (high / medium / low), Why it matters.
   One line each. Do not propose fixes beyond a phrase. Do not edit anything.
4. Do not spend time reproducing findings: read the code. You may run `make test` and
   the tool once each if you need to. Mark a finding you only read as "(not run)".
```

The model line is a decision for calibration (Section 12): Sonnet by default, so the review is at least as good as the author.

---

## 9. Answer Key (Facilitator Only)

| Level | Check passes when | Human answer |
|---|---|---|
| 0 | `PLAN.md` complete per 3.5, committed | Logged |
| 1 | Three valid runs and one clean error per Level 1; ≥ 2 commits; clean tree | Pulsars: `sun` (synonyms above). Dimuons: `jpsi` (synonyms above). |
| 2 | `TESTS.md` filled; ≥ 5 tests pass; `explorer` imported; ≥ 1 commit; clean tree | Logged |
| 3 | `REVIEW.md` triaged (three findings, reasons); tests pass; runs on the group's dataset; ≥ 1 commit; clean tree | Logged |

There are no planted bugs. What the agent gets wrong is whatever it gets wrong on the day; the leader's job is to make sure the group notices.

**Things worth noticing, if they happen** (for the leader and the show-and-tell):

| Moment | Why it matters |
|---|---|
| Claude decides the missing-value or log policy without asking | The plan is where silent decisions surface |
| Claude builds three steps in one go | Small steps make errors local |
| "This should work now", no run shown | Evidence over assertion |
| A Plotly API recalled wrongly | Read the installed docs |
| `NaN` in `data.json` | A real bug the check catches and a human would not |
| Hover shows another row's values after sampling | Only a human looking at the browser, or a review, catches it |
| The group's test list has something Claude's plan lacks, or the reverse | Define the check yourself |
| A failing test "fixed" by editing the test | The one thing never to accept |
| A review finding rejected with a good reason | The human owns the result |
| A guessed finding the reviewer also found, or missed | Calibrates how much to trust each |

---

## 10. Group Leader Guide

*Superseded by section 3 onwards of `exercises/explorer/FACILITATOR-WALKTHROUGH.md` once built; kept here as the design intent.*

### Before the Session

- Run `./preflight`, then reset as in the walkthrough.
- Set the group's dataset: the `Dataset:` line in `PLAN.md`. Pick the one closest to the group's research.
- Build the tool yourself once, on Sonnet, following the playbook. Time each level.
- Arrange two windows: **Claude** (large, visible to the group) and **Gate** (small; also where humans run `make test`, `make list`, `make open`). Have a browser window ready.

### Opening (60 Seconds, Read Aloud)

> "Today we build a real tool, a 3D explorer for our data, and we build it the way you'd want a careful student to: plan, build in two checked steps, test, review, and commit as we go. Claude is a normal, helpful collaborator today; the gates just make sure we do each step. The gate terminal is ours: Claude can't type there, and that's where we run the tests ourselves. Roles: [assign]. The keyboard rotates at each gate. All code goes through Claude; we read, look, decide. At the end, `PLAYBOOK.md` is yours to take home."

### Coaching by Level

| Level | Watch for | Ask the group |
|---|---|---|
| 0 | Accepting Claude's plan unread | "Which decisions did Claude make for us? Do we agree?" |
| 1 | Big-bang builds; nobody opening the browser; nobody committing | "What did that step change? Show me in the browser. Is it committed?" |
| 2 | Asking Claude before writing the group's own list; nobody reading coverage | "What won't these tests catch? Does that matter for us?" |
| 3 | Fixing every finding without discussion | "Is this worth fixing in a prototype? Why?" |

### Managing the Group

- **The expert who wants to write it by hand:** "You'd be faster today. The point is the habit for when the code is ten times bigger. Can you get Claude to do it the way you would?"
- **Plotting rabbit holes** (styling, extra controls): the Navigator owns scope. "Is it in the plan?" Suggestions go in the log for later.
- **2 people:** the leader is Coach + Navigator; the partner is Driver + Sceptic + Scribe.
- **5 people:** split the Sceptic into **Browser Sceptic** (looks at every result) and **Evidence Sceptic** (wants every command and output).
- **Correction spirals:** after two failed corrections, `/clear` and a better prompt.

### Time Checkpoints

| T (since Go) | Expected position | If behind |
|---|---|---|
| 8 min | `PLAN.md` committed | Keep the plan short; give hint 3's advice |
| 26 min | Level 1 gate passed | Narrow to what `./gate check` names; skip styling |
| 34 min | Tests running | Five simple tests are enough |
| 42 min | Review triaged | Three findings is enough; fix one |

### If Things Break

| Problem | Action |
|---|---|
| `make open` does nothing | Open `out/explorer.html` from Finder; check `out/` was written |
| Page blank in the browser | plotly.js not embedded, or a JavaScript error: open the browser console; `./gate check` names the embedding case |
| Check fails on `data.json` | Almost always `NaN`; paste the line to Claude |
| Build too slow for the time | `./gate skip --master`; the facilitator can copy the reference solution from the builder repo (walkthrough) |
| Hooks not loaded | `/hooks`; call the facilitator |

---

## 11. Build Notes

1. **Data (`make_data.py`, facilitator machine only, stdlib):** download the ATNF catalogue (web query for the derived columns, or the package and compute them) and the CERN Open Data Run2010B dimuon CSV; write the CSVs and the sidecars; spot-check `XX`, `YY`, `ZZ` against `GL`, `GB`, `DIST` with the Sun at (0, 8.5, 0), and `M` against the four-vectors. Record versions and licences in the sidecars and `data/README.md`. Freeze under `data/` (frozen globally by gatekit).
2. **Reference solution** (`selftest/solution/`, never shipped): built by following the playbook on Sonnet, so the timings are honest. Three modules (`data.py`, `page.py`, `__main__.py`), a test module, sample `PLAN.md`, `TESTS.md`, `REVIEW.md`. The self-test installs it level by level.
3. **Check scripts** (`.gatekit/exploretool/checks/level0–3.py`): structural only, as specified per level. They run the tool with `.venv/bin/python -m explorer` into a temporary directory and read `data.json` with `json.loads` and a `parse_constant` that rejects `NaN` and `Infinity` (the default parser accepts them). The HTML checks are string searches for the control ids, option values, `scattergl`, `scatter3d` and an inline plotly script. Git checks shell out to `git rev-list --count` and `git status --porcelain`.
4. **Tool package `exploretool`:** checks, a `post_unlock` that records `HEAD` per level in `state.records`, `status_lines` printing the dataset, whether `out/explorer.html` exists and the commits since the last gate, `on_reset` clearing the records. No `conditions`, `validators` or `level_secret`. `human_only: {}`.
5. **Manifest:** four levels as in Section 4; `models.default` `sonnet`, `allowed` `["sonnet"]`; Level 1 `crypto` with one `keyword` question accepting both datasets' synonyms; the others `crypto-reflection`; `files` revealing `TESTS.md` at Level 2 and `REVIEW.md` at Level 3. `answers.json` and `make_answers.py` as in the Speed Run.
6. **Reviewer agent:** `.claude/agents/reviewer.md` as in Section 8, shipped from `workshop/.claude/agents/` (the build copies directories under `workshop/` to the repo root).
7. **Self-test:** build, preflight, then play every level with the reference solution, including one refused gate per level (incomplete or uncommitted `PLAN.md`; a solution that writes `NaN`, then one with too few commits; four tests and an empty `TESTS.md`; an untriaged `REVIEW.md`), the wrong and right Level 1 answer, the master skip and the reset.
8. **Calibration:** can a group following the playbook reach the end of Level 3 in 42 minutes on Sonnet? Measure Level 1 especially; if it runs long, the README takes over Level 0's questions and Level 0 drops to 6 minutes.
9. **Repo entries:** add Exercise E to the `README.md` exercise table and `docs/00` §1 once built (core lesson: "Plan, build, test, review: the workflow as a habit"; model Sonnet).

---

## 12. Decisions Taken in This Revision

Recorded here so the reasoning survives; the build logs any further deviation in `DECISIONS.md`.

1. **Model: Sonnet.** Version 1 proposed Sonnet with Haiku as a calibration option. Building Python plus a JavaScript page in 18 minutes is a real risk on Haiku, and the lesson here is the workflow, not supervision of a weak model. Decided with the facilitator.
2. **Browser page with drop-downs, not a command-line plot.** Version 1 fixed the axes on the command line (`--x`, `--y`, `--z`, `--colour`, `--slider`). The facilitator asked for a page where every axis, the colour column and the palette are chosen from menus. Consequence: Python prepares data and writes the page; the page plots. The checkable contract moved from `figure.json` to `data.json` plus fixed control ids.
3. **Plotly, not PyVista.** PyVista (and the facilitator's ViSAGE viewer, which is PyVista plus trame) was considered seriously. Plain PyVista has sliders, buttons and click picking but no drop-down and no hover; the drop-downs in ViSAGE come from trame's Vuetify widgets, which means a localhost server and a tightly pinned trame stack. The VTK wheel is 103 MB; the window must open from Claude's TTY-less subprocess, and off-screen checks need a GPU context in the check process. Plotly is a 10 MB wheel, the page is a file humans open themselves, and the check reads JSON. PyVista remains the right tool for ViSAGE-scale work and is mentioned to groups as such.
4. **Slider dropped from the requirements.** With drop-downs for colour it is no longer needed to make the page useful, and it was the riskiest Plotly feature to build in the time. It is a natural suggestion for the Level 1 play minute.
5. **Generic dataset path.** Version 1 had `--data {pulsars|dimuons}`. The tool now takes any CSV with an optional sidecar, so the leader's choice is one line in `PLAN.md`, and the stretch is a group's own data. The Makefile reads that line, so the dataset is named in one place.
6. **Two slices merged into one build level, and the test step condensed.** Version 1 of this revision proposed Plan, Slice 1, Slice 2, Test, Review (five gates, no contingency). The facilitator chose to merge the slices into one 18-minute build of "everything needed to use it" and to keep the test step to 8 minutes, leaving 3 minutes of contingency with four gates, the shape of the Speed Run. The play-and-suggest pause survives as the end of Level 1.
7. **Guess first.** `TESTS.md` and `REVIEW.md` each open with the group's own list, written before Claude is asked. Facilitator's suggestion; it turns both steps from "watch the agent" into a comparison.
8. **Review by a shipped reviewer agent, not `/code-review`.** The agent's output can be captured into `REVIEW.md` and its prompt is readable by the group; `/code-review` stays in the playbook for home use. Verified against the Claude Code docs (2.1.296): subagents start with a fresh context; `.claude/agents/*.md` supports `tools` and `model`; `/code-review` runs as a background subagent and prints to the conversation.
9. **Version control in every gate.** Commits counted since the previous unlock, clean tree for the checked paths. Matches the lecture's "one change, one check, one commit" and the Speed Run's commit-before-submit.
10. **Dependencies:** `plotly` and `pytest-cov` added to the exercise venv, pinned, installed by `./preflight --setup` before the day; `preflight_extra.py` checks that plotly imports and that its bundled `plotly.min.js` is present. Agreed with the facilitator.
11. **Datasets:** the two real datasets, both shipped; the synthetic xenon TPC and GWTC options dropped.
12. **Honest limits accepted:** the check scripts print a fixed line, so each crypto gate's only secret is the human answer; Level 1 accepts both datasets' answers, so a group could answer the other dataset's question; the Level 1 answer can also be found in the column file or known from physics, so the question prompts a look rather than proving one; a FIX in `REVIEW.md` is a label, not evidence of a fix. All harmless in practice, and all the leader's to check.
13. **PyVista and other packages, for the record:** PyVista (desktop VTK), pyvistaqt (adds Qt, about 77 MB more), trame (server plus browser), Bokeh and Altair (browser, 2D only or weaker 3D) were considered; Plotly was the only one with native 3D WebGL, hover and a self-contained offline file.
14. **No FIX required at Level 3** (external panel, round 1). Requiring a FIX would push a group whose review came back short or clean to manufacture one in the last eight minutes. The gate needs three triaged findings with reasons; the reviewer is asked for three to five; the brief says fix the top FIX item, more only if there is time.
15. **Hint tiers** on the 8-minute levels unlock at 0, 3 and 6 minutes (0, 5 and 10 on Level 1), so the third hint exists before the level's time is up.

### Build deviations (2026-10-14)

Logged in `DECISIONS.md` with reasons; the ones that change what a leader sees: `make list` fails at Level 0 because the tool does not exist yet, so Claude counts the missing values instead; the last-level crypto gate needed a `tools/build.py` fix (no exercise had ended on a crypto gate before); the pulsar catalogue has 4,503 rows and the dimuon file is trimmed to 60,000; the reference solution's page was rendered in Chrome and behaves as specified.

## 13. Open Questions

1. **Calibration.** Whether 18 minutes is enough for Sonnet to build 3.1–3.3 with a group directing one step at a time. The self-test proves the reference solution passes the checks, not the timing.
2. **Reviewer model.** Sonnet by default. If Haiku finds real issues in calibration, it is cheaper and the contrast with the author is sharper.
3. **Hooks and subagents.** Verified 2026-10-14: settings-file hooks run inside subagents, so the guard covers the reviewer agent's own tool calls. The reviewer is read-only, so nothing changes; closed.
4. **Take-home form.** `PLAYBOOK.md` plus the reviewer agent, as designed, or also a starter `CLAUDE.md` and the Stop-hook settings in a `take-home/` folder.
5. **Time.** If Level 1 runs long in calibration, move Level 0's questions into the README and give it 6 minutes.
