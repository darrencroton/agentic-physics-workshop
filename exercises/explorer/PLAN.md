# Explorer (Exercise E): Frozen Build Contract

Version 1 (2026-10-13). Every build task works from this file. `docs/05-data-explorer.md` is the design and the pedagogy; `BUILD-SPEC.md` the engineering spec; `exercises/speed-run/` the worked example whose conventions this follows (tool package, checks that print a fixed line, `make_answers.py`, pty-driven self-test, walkthrough). Deviations from `docs/05` go to `docs/DECISIONS.md`.

## 1. Levels and timing (45 min = 8 + 18 + 8 + 8 + 3 contingency)

| L | Title | Min | Persona | Gate type | Machine check (`.gatekit/exploretool/checks/levelN.py`, venv python) | Graded question | Reflection (logged) |
|---|---|---|---|---|---|---|---|
| 0 | Plan | 8 | collaborator | crypto-reflection | `PLAN.md` complete (section 5); ≥ 1 commit since `start`; `PLAN.md` clean | — | "One thing in the agent's plan you changed, and why:" |
| 1 | Build the prototype | 18 | collaborator | crypto | tool runs (section 4) on the `PLAN.md` dataset; ≥ 2 commits since the L0 unlock; `explorer/` and `PLAN.md` clean | keyword, worded for the `PLAN.md` dataset via `text_from: explore.browser_question` (pulsars: what is where the known pulsars crowd in XX, YY, ZZ; dimuons: which particle makes the band near 3.1 GeV), with a dataset `wrong_hint`; static fallback points at `BRIEF.md`; accept `sun`, `solar system`, `earth`, `us`, `solar neighbourhood` (and their article forms), plus `contains: ["meson", "psi", "charmonium"]`, so any answer containing one of those words (e.g. "J/ψ meson") canonicalises to that term | "One feature the group would add:" |
| 2 | Test | 8 | collaborator | crypto-reflection | `TESTS.md` ≥ 3 bullets under "Our list" and non-template text under "The agent's plan"; pytest collects ≥ 5 tests, all pass; ≥ 1 test module imports `explorer`; ≥ 1 commit since the L1 unlock; `explorer/`, `tests/`, `TESTS.md` clean | — | "What did the agent's plan cover that yours didn't, or the reverse?" |
| 3 | Review | 8 | collaborator | crypto-reflection (last level; marks complete) | `REVIEW.md` ≥ 2 guess bullets, ≥ 3 table rows with decision in {FIX, ACCEPT, REJECT} and non-empty reason; pytest ≥ 5 pass; the section-4 run checks pass on the `PLAN.md` dataset; ≥ 1 commit since the L2 unlock; `explorer/`, `tests/`, `REVIEW.md` clean | — | "What did the review find that the tests didn't?" |

Success line of every check: exactly `{"level": N, "ok": true}` + newline (`json.dumps(sort_keys=True)`), as in the Speed Run; failure: one sentence on stderr, exit 1. `make_answers.py` writes `answers.json` for levels 0–3.

Hints: three tiers per level, text from `docs/05` section 4; they unlock at 0, 5 and 10 minutes on Level 1 and at 0, 3 and 6 minutes on the 8-minute levels.

## 2. Repo layout (`dist/explorer/`)

```text
README.md  CLAUDE.md  LOG.md  PLAN.md  PLAYBOOK.md  Makefile  requirements.txt  .gitignore
gate  preflight
data/README.md  data/pulsars.csv  data/pulsars.columns.json  data/dimuons.csv  data/dimuons.columns.json
explorer/__init__.py            empty package; Claude writes the rest
tests/__init__.py               empty; Claude writes tests at Level 2
.claude/agents/reviewer.md      shipped from workshop/.claude/agents/reviewer.md
.claude/  .gatekit/  .vault/  .workshop/   as in the Speed Run
.gatekit/exploretool/           __init__.py, gates.py, checks/level0..3.py (+ _pepper.py is NOT needed: no keys.bin)
out/                            gitignored (explorer.html, data.json)
TESTS.md                        appears at Level 2 (manifest files)
REVIEW.md                       appears at Level 3 (manifest files)
```

Source tree `exercises/explorer/`: `manifest.json`, `answers.json`, `make_answers.py`, `make_data.py`, `level0/` (everything above that exists at the start), `levels/0/` (`persona.txt`, `hints.json`, `guard.json`), `levels/1..3/` (`BRIEF.md`, `persona.txt`, `hints.json`, `guard.json`, plus `TESTS.md` in 2 and `REVIEW.md` in 3), `workshop/` (`CLAUDE.workshop.md`, `preflight_extra.py`, `exploretool/`, `.claude/agents/reviewer.md`), `selftest/run.py`, `selftest/solution/` (reference solution and sample files), `FACILITATOR-WALKTHROUGH.md`.

`.gitignore`: `out/` has been added to the gatekit template `.gitignore` (harmless for the other exercises), so generated pages never show as untracked. The checks run the tool into a temporary directory and restrict `git status --porcelain` to the paths listed per level.

## 3. Frozen interfaces

### 3.1 Command line (README; checks call exactly this)

```
.venv/bin/python -m explorer DATA.csv [--out DIR] [--max-points N] [--seed S]
.venv/bin/python -m explorer DATA.csv --list
```

- `DATA.csv`: any CSV with a header row; empty field = missing. Sidecar `DATA.columns.json` optional (format: `data/README.md`). Without it, a column is numeric when it has at least one non-empty value and every non-empty value parses as a float; units blank, descriptions blank, `log` false.
- Errors (missing file, unreadable, no numeric columns): message on stderr, non-zero exit, no traceback.
- `--max-points` default 20000, `--seed` default 0; sampling without replacement when `n_read > max_points`.
- `--list`: one line per column: name, unit, description, missing count; exit 0.
- Prints `n_read` and `n_written` on a normal run.

### 3.2 `data.json`

```json
{"source": "<path as given>", "n_read": 4503, "n_written": 4503,
 "columns": [{"name": "P0", "unit": "s", "description": "Spin period", "log": true}],
 "rows": {"P0": [0.00575, null]},
 "labels": {"JNAME": ["J0437-4715", "B0531+21"]}}
```

Strict JSON (`allow_nan=False`); every list in `rows` and `labels` has length `n_written`; `1 <= n_written <= max_points`; `columns` names are exactly the keys of `rows`, in CSV order.

### 3.3 `explorer.html`

Self-contained. Must contain: an inline `<script>` holding plotly.js (test: the string `plotly.js v` or `Plotly.react`/`Plotly.newPlot` present, file size > 1 MB, and no `<script src="http`); `<select id="x">`, `<select id="y">`, `<select id="z">`, `<select id="colour">` each with `<option value="COL">` for every numeric column (`z` and `colour` also `value="none"`), and `<select id="palette">` with at least three colour-scale options; checkboxes `id="logx"`, `id="logy"`, `id="logz"`, `id="logc"`; the strings `scattergl` and `scatter3d`. The check is a string/regex search; it does not execute JavaScript.

### 3.4 `PLAN.md` dataset line

`Dataset: data/pulsars.csv` or `Dataset: data/dimuons.csv` (exact relative paths). The Makefile reads it: `DATA ?= $(shell sed -n 's/^Dataset:[[:space:]]*//p' PLAN.md)`. The Level 0 check requires one of the two values; the Level 1 and Level 3 checks run on it, and only on it.

### 3.5 Makefile

```make
PY ?= .venv/bin/python
DATA ?= $(shell sed -n 's/^Dataset:[[:space:]]*//p' PLAN.md)
OUT ?= out
ARGS ?=

.PHONY: explore open list test coverage status

explore:
	$(PY) -m explorer $(DATA) --out $(OUT) $(ARGS)
open:
	open $(OUT)/explorer.html
list:
	$(PY) -m explorer $(DATA) --list
test:
	$(PY) -m pytest -q
coverage:
	$(PY) -m pytest -q --cov=explorer --cov-report=term-missing
status:
	./gate status
```

### 3.6 `requirements.txt`

`numpy==2.3.2`, `plotly==7.1.0`, `pytest==9.1.1`, `pytest-cov==7.1.0` (installed in `dist/explorer/.venv` on 2026-10-13). `preflight_extra.py` checks numpy, plotly and pytest_cov import, and that `plotly.offline.get_plotlyjs()` returns > 1 MB.

### 3.7 Git evidence (`exploretool/gates.py`)

- `post_unlock` `explore.record_head` (every level's gate): stores `git rev-parse HEAD` in `state["records"]["heads"][str(new_level)]`; level 0's baseline is the `start` tag.
- `commits_since(root, level)`: `git rev-list --count <base>..HEAD` where base = `records.heads[str(level)]` if present else `start`.
- `dirty(root, paths)`: `git status --porcelain -- <paths>` non-empty.
- Required commits: L0 ≥ 1, L1 ≥ 2, L2 ≥ 1, L3 ≥ 1. Checked paths: L0 `PLAN.md`; L1 `explorer PLAN.md`; L2 `explorer tests TESTS.md`; L3 `explorer tests REVIEW.md`.
- Failure sentences name the fix: "1 commit since the last gate; this level needs at least 2: ask Claude to commit each step that works (two commits or more)" / "explorer/ has uncommitted changes: ask Claude to commit, then unlock".

### 3.8 Manifest (shape)

```json
{"exercise": "explorer", "title": "Explorer: plan, build, test, review",
 "tool": "exploretool", "human_only": {},
 "models": {"default": "sonnet", "allowed": ["sonnet"]},
 "levels": [
  {"id": 0, "title": "Plan", "persona": "collaborator", "target_minutes": 8,
   "gate": {"type": "crypto-reflection", "check": "checks/level0.py", "python": "venv", "timeout": 120,
            "questions": [], "reflection": "One thing in the agent's plan you changed, and why:",
            "post_unlock": "explore.record_head"}},
  {"id": 1, "title": "Build the prototype", "persona": "collaborator", "target_minutes": 18,
   "gate": {"type": "crypto", "check": "checks/level1.py", "python": "venv", "timeout": 300,
            "questions": [{"id": "browser", "kind": "keyword", "prompt": "...", "accept": [...], "contains": [...]}],
            "reflection": "...", "post_unlock": "explore.record_head"}},
  {"id": 2, "title": "Test", "persona": "collaborator", "target_minutes": 8,
   "files": {"TESTS.md": "TESTS.md"},
   "gate": {"type": "crypto-reflection", "check": "checks/level2.py", "python": "venv", "timeout": 300,
            "questions": [], "reflection": "...", "post_unlock": "explore.record_head"}},
  {"id": 3, "title": "Review", "persona": "collaborator", "target_minutes": 8,
   "files": {"REVIEW.md": "REVIEW.md"},
   "gate": {"type": "crypto-reflection", "check": "checks/level3.py", "python": "venv", "timeout": 300,
            "questions": [], "reflection": "...", "pre_reflection_note": "That was the last gate. PLAYBOOK.md is yours to take home."}}
 ]}
```

Check `gatekit/gatekit/manifest.py` and `cli.py` for the exact accepted keys (the `files` map is applied on unlock; `questions: []` with `crypto-reflection` must be accepted: verify with the fixture exercise or the TDD manifest, and adapt).

### 3.9 Guards

| Level | editable | frozen (beyond gatekit's always-frozen set) |
|---|---|---|
| 0 | `PLAN.md`, `LOG.md` | `explorer/**`, `tests/**` |
| 1 | `explorer/**`, `PLAN.md`, `LOG.md` | `tests/**` |
| 2 | `explorer/**`, `tests/**`, `TESTS.md`, `LOG.md` | `PLAN.md` |
| 3 | `explorer/**`, `tests/**`, `REVIEW.md`, `LOG.md` | `PLAN.md`, `TESTS.md` |

`out/**` is editable at every level (scratch files). `PLAYBOOK.md` and `data/` are frozen at every level (add `PLAYBOOK.md` to each level's `frozen`; `data/` is always frozen by gatekit). Each guard has a one-sentence `message`.

## 4. The Level 1/3 run checks (`exploretool/gates.py: run_tool_checks(root, dataset) -> (ok, sentence)`)

In a temporary directory `T`, with the venv python and a 30 s timeout per command, from the repo root:

1. `python -m explorer <dataset> --out T/a`: exit 0; `T/a/data.json` parses with `json.loads` (strict), has the 3.2 structure, `n_written >= 1`, `n_written <= 20000`, every column in the sidecar marked numeric appears in `columns` and `rows`, no value is a non-finite number; `T/a/explorer.html` passes 3.3.
2. `python -m explorer <dataset> --out T/b --max-points 500`: exit 0; `n_written == 500`; `n_read` unchanged from run 1.
3. `python -m explorer <dataset> --list`: exit 0; stdout contains every column name of the sidecar.
4. `python -m explorer T/does-not-exist.csv --out T/c`: non-zero exit; combined output lacks `Traceback`.

The first failing item gives the sentence, naming the run and what was wrong (for example: `data.json is not valid JSON (NaN is not JSON; write it with allow_nan=False)`; `explorer.html has no <select id="colour">`; `--max-points 500 wrote 4503 rows`). `explorer/__init__.py` present but empty gives: "there is no explorer/__main__.py yet: ask Claude to add the command line".

## 5. `PLAN.md` completeness (Level 0 check)

Template in `docs/05` section 3.5. Pass when: `Dataset:` is one of the two paths; each of the four decision bullets has text after the colon; each `##` section has at least one non-empty line that is not the template's own text; "Acceptance criteria" has ≥ 3 bullets; "Steps" has exactly 2 top-level bullets or numbered items (sub-bullets do not count).

## 6. Reference solution (`selftest/solution/`)

Built by a Sonnet subagent following `PLAYBOOK.md` against the frozen interfaces (so it is also a first calibration of the build time). Layout: `explorer/__init__.py`, `explorer/data.py` (load CSV + sidecar, numeric detection, missing counts, sampling), `explorer/page.py` (HTML with inline plotly.js from `plotly.offline.get_plotlyjs()`, controls, the JavaScript), `explorer/__main__.py` (argparse, `--list`, writes both files); `tests/test_explorer.py` (≥ 6 tests: numeric detection, missing counts, sampling size and determinism, strict JSON, controls present, bad path exits cleanly); `PLAN.md`, `TESTS.md`, `REVIEW.md` filled samples; `PLAN.md` for both datasets (`PLAN.pulsars.md`, `PLAN.dimuons.md`). Also a broken variant `solution_nan/explorer/__main__.py` that writes `NaN` (for the refused gate).

## 7. Self-test (`selftest/run.py`, pty-driven, `--skip-build`, `--dist`)

1. Build (`--keep-venv`), `./preflight` through a pty.
2. L0: unlock refused (template `PLAN.md`, no commit); install `PLAN.pulsars.md`, refused ("no commit since start"); commit; unlock with a reflection → Level 1; `BRIEF.md` present; reflection in `LOG.md`; `records.heads["1"]` set.
3. L1: `gate check` refused (no `__main__.py`); install `solution_nan`, commit, refused with the NaN sentence; install the solution uncommitted, refused ("1 commit since the last gate; this level needs at least 2"); commit; small further commits to `explorer/` files; edit `explorer/data.py` without committing → refused ("uncommitted changes"); commit; `make explore` → `out/explorer.html` and `data.json` exist, `make list` prints the columns; wrong answer `the moon` rejected with the pulsar hint; `sun` unlocks Level 2 (the dimuon pass checks its own prompt and hint); `TESTS.md` present.
4. L2: refused (empty `TESTS.md`); install the sample `TESTS.md` and a 4-test file → refused ("4 tests ... needs at least 5"); install the full tests, commit; `make test` passes; unlock → Level 3; `REVIEW.md` present.
5. L3: refused (untriaged `REVIEW.md`); install the sample `REVIEW.md`; refused (no commit); commit; a corrupted `data/pulsars.columns.json` is refused, a corrupted `data/dimuons.columns.json` is ignored (Level 3 runs only the `PLAN.md` dataset); unlock → complete; completion note printed.
6. Dimuons path: after the reset, repeat L0–L1 with `PLAN.dimuons.md` and the answer `jpsi` (covers the second dataset and the keyword set).
7. `gate skip --master` from a fresh reset; `gate reset`; clean tree at the end (`git status --porcelain` empty apart from nothing; `out/` removed by the self-test).

Report timings for each `make explore` (target < 5 s) and the whole run.

## 8. Personas and briefs

Collaborator at every level; each `persona.txt` starts `persona: collaborator`, states the level rule from `docs/05` section 7, then the "Explain as you go" paragraph and the "Never" list, in the Speed Run's style and length (about 150–200 words). Briefs (`BRIEF.md`) follow the Speed Run structure: title with target time and persona, "Where we are", "What to do" (numbered), "What to watch for", "Opening the gate" (ending with "commit, then `./gate unlock`"). Each brief quotes the playbook prompt(s) for the level.

## 9. Build tasks (disjoint file sets)

| Task | Files | Who |
|---|---|---|
| A. Data | `make_data.py`, `level0/data/*` | Sonnet (running) |
| B. Core | `manifest.json`, `make_answers.py`, `answers.json`, `level0/` (README, LOG, PLAN, PLAYBOOK, Makefile, requirements, explorer/, tests/), `levels/0..3/*`, `workshop/*` (CLAUDE.workshop.md, preflight_extra.py, exploretool/, .claude/agents/reviewer.md), venv set-up, build and preflight green | Opus |
| C. Reference solution | `selftest/solution/*` | Sonnet, following the playbook against this contract |
| D. Self-test | `selftest/run.py` | Opus, after B and C |
| E. Docs | `FACILITATOR-WALKTHROUGH.md`, `README.md` table, `docs/00` §1, `PROGRESS.md`, `docs/DECISIONS.md` | Sonnet, after D |

## 10. Deviations from `docs/05` (to `docs/DECISIONS.md`)

Recorded in `docs/DECISIONS.md` ("Explorer (Exercise E) build"): check paths under `.gatekit/exploretool/checks/`; the last-level crypto gate fix in `tools/build.py`; the `.DS_Store`-tolerant wipe; the PLAN.md leader note as an HTML comment; `make list` unavailable at Level 0; extra keyword forms; `scattergl`/`scatter3d` searched outside the plotly bundle; commit count checked before the clean tree; `on_reset` removes `out/`; `out/` and `.coverage` in the template `.gitignore`; persona length; data sizes (4,503 pulsars, 60,000 dimuon rows) and blanked positions for pulsars without a distance.
