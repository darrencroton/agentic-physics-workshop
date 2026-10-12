# Facilitator Walkthrough: The TDD Ladder

Private. Contains gate answers and spoilers. Never copy into `dist/`.

## 1. Build and set up (once per machine)

```zsh
cd <this repository>
python3 tools/build.py tdd-ladder --master-passphrase-file ~/.config/workshop/master-passphrase --keep-venv
cd dist/tdd-ladder
./preflight --setup      # only if .venv is missing; creates .venv with /opt/homebrew/bin/python3.13 and installs the pins
./preflight              # must end with "Preflight passed"
claude                   # accept the workspace trust dialog once, then the checks below, then /exit
```

Checks inside that first `claude` session (about a minute):

1. `/hooks`: all four events must be listed (SessionStart, UserPromptSubmit, PreToolUse, PreModelSwitch). If the list is empty, the trust dialog was not accepted: exit and re-open `claude`.
2. `/status`: the model line must say Haiku (the start-up banner also names `.claude/settings.json` as the source).
3. `/model` and pick Sonnet (or Default): it must be refused with "Today's exercise uses haiku. Ask a facilitator for a power-up." Picking Haiku again is allowed and does nothing.

`--keep-venv` preserves an existing `dist/tdd-ladder/.venv` across rebuilds. Everything else in `dist/tdd-ladder` is regenerated, including the git history, so rebuild only between runs.

The master passphrase is in `~/.config/workshop/master-passphrase`. You type it for `./gate skip --master` and `./gate allow-model`. It never goes into a repo.

## 2. Two windows

| Window | Command | Who types |
|---|---|---|
| Claude (large) | `cd dist/tdd-ladder && claude` | the Driver |
| Gate (small) | `cd dist/tdd-ladder` in a fresh Terminal window (not one opened from Claude Code), then `./gate …` and `./tdd …` | the humans |

The session starts in plan mode on Haiku. `Shift+Tab` leaves plan mode. `/model` to anything but Haiku is refused by the hook until you grant a power-up with `./gate allow-model sonnet`. Choosing Haiku in `/model` is allowed, because Haiku is the allowed model; that is not a bypass.

**Which model is it, really?** Trust `/status` (or a status line), not what Claude says about itself. Haiku models sometimes misreport their own name, so "I'm Claude Sonnet" in answer to "what model are you?" is not evidence of an override. Claude Code applies a project `model` setting at launch unless `--model`, `ANTHROPIC_MODEL` or an earlier `/model` overrides it; a launch-time `--model` or environment override is not blocked by the `PreModelSwitch` hook, and the SessionStart check only warns when Claude Code reports the model. If in doubt, quit and re-open with plain `claude`, then check `/status`. `CLAUDE.workshop.md` tells Claude to say it cannot be sure and to point at `/status`.

Useful at any time in the gate terminal: `./gate status`, `./gate brief`, `./tdd status`, `./tdd ladder`, `./gate hint` (tiers unlock at 0, 5 and 10 minutes on the level).

## 3. Level by level

### Level 0: Just build it (5 min, persona literal)

1. Driver pastes the client's request from `README.md` into Claude exactly as written. Accept what it gives you. If it asks a question, answer "whatever you think best".
2. In Claude: `make plot`. Look at `results/hz_binned.png`; a copy is kept as `results/hz_binned_L0.png`.
3. Gate terminal: `./tdd score` (about 2 s). Then `./gate unlock`. The unlock saves the Level 0 work on branch `attempt-L1-<timestamp>` and restores the stub and an empty `tests/` automatically, and says so.

Observe: does Haiku ask any questions, or just decide? Does it write tests? Typical score with the sample naive code: acceptance 4/12, 1/16 killed, 2 false alarms. Anything in the band acceptance 4–9 and kills ≤ 6 is the expected experience.

Gate answer: the acceptance number printed by `./tdd score`. Reflection (logged, not graded): two silent decisions.

### Level 1: "Use TDD, please" (6 min, persona literal)

1. Nothing to run: the L0 unlock already started the attempt from the stub. (`./tdd new-attempt` is still there to restart the level; the gate then wants a fresh `./tdd score`.)
2. Driver: same request plus "Use test-driven development."
3. Watch for: tests and code in one turn; first `pytest` run all green; expected numbers from Claude's head. `.tdd/runs.jsonl` records every pytest run, so `./tdd status` after a score shows what happened.
4. `make plot` keeps `results/hz_binned_L1.png` next to the L0 plot, for comparison. `./tdd score`, then `./gate unlock`.

The unlock commits the Level 1 work as "Level 2 start", so the Level 2 refusal can quote an exact `git checkout <hash>` restore.

Gate: no graded question. Reflections: red seen (y/n); oracle source (a–d). Expected band: acceptance 6–10, kills ≤ 8.

### Level 2: Decide before you test (10 min, persona coach)

1. Driver uses the interview prompt from `BRIEF.md`. Claude should ask one question at a time and never suggest answers. Cap the interview at 8 minutes.
2. Claude writes `SPEC.md` with numbered decisions (`1.`, `2.`, … at least 6). No code, no tests: the guard allows only `SPEC.md` and `LOG.md`, and the gate checks that `src/` and `tests/` are byte-identical to when the level began.
3. `./gate unlock`. If `src/` or `tests/` changed, the refusal names the files and the `git checkout` or delete needed. The unlock writes `CLIENT_SPEC.md`, resets `src/hzbin/binning.py` and `tests/` to the stub (your work is on `attempt-L3-<timestamp>`), and only then asks the reflection "how many of the client's 10 decisions did your SPEC address?".

Observe: whether the group argues about what the error bar means and where the point sits (S4, S5). Most groups anticipate 5–8 of 10.

### Level 3: Red, green, refactor, for real (15 min, persona coach + phases)

Each cycle, in the gate terminal:

```zsh
./tdd red "single bin with equal sigma gives the arithmetic mean"   # opens the cycle; src/ frozen
# Claude writes ONE test; the Sceptic supplies the number; Claude commits: git add tests && git commit -m "..."
./tdd green        # refuses unless the test is committed and fails with AssertionError/NotImplementedError
# Claude writes the minimum code; commits
./tdd refactor     # optional
./tdd done         # closes the cycle; needs all green and a clean src/ and tests/
```

Things to try deliberately so the group sees the machinery:

- In GREEN, ask Claude to "fix the test". The guard denies with "Tests are frozen in GREEN…". Let the discussion run.
- Ask Claude to write a test that imports a name that does not exist. `./tdd green` refuses: "red for the wrong reason: ImportError".
- Have someone edit a test file by hand during GREEN. `./tdd refactor` or `./tdd done` refuses: "tests/ changed since GREEN began".

Suggested order of behaviours is in `BRIEF.md`. The gate needs 5 valid cycles with none left open (otherwise it says to run `./tdd done` or `./tdd abort`), then `./tdd score` with 0 false alarms and ≥ 9/16 killed. The sample Rung-4 suite scores 10/12 acceptance, 11/16 killed, survivors S2, S7, S9, S10.

Gate answer: any spec ID listed under "surviving mutants violate" in the last score, or `none` if 16/16.

### Level 4: Think like a physicist (8 min, persona coach)

The brief has the property-test menu. Three property tests (uniform-σ limit, affine equivariance, seeded coverage) plus the validation tests usually take the suite to 14–16/16. The gate needs ≥ 14/16, 0 false alarms, suite under 10 s.

Gate answer: √(0.683 × 0.317 / 2500) ≈ 0.0093. Accepted: 0.0090 to 0.0096.

### Level 5: Stretch, test the tests (5 min, persona collaborator)

Claude (via a subagent) writes mutants of the group's own `binning.py`; the group runs its suite against each. The gate needs a `## Mutation report` section in `LOG.md`. Reflection: one test you'd delete.

## 4. When something goes wrong

| Symptom | Do |
|---|---|
| Group stuck | `./gate hint` (3 tiers), then a question, then `./gate allow-model sonnet` (master passphrase), then `./gate skip --master` as the last resort. All are logged in `LOG.md` and `.workshop/state.json`. |
| Hooks not firing (Claude edits tests in GREEN) | In Claude run `/hooks`; if empty, exit, re-open `claude` in the repo and accept trust. `./tdd` transitions still catch Bash edits via git diff. |
| `./tdd green` refuses | Read the reason aloud. It is the lesson. |
| `./tdd red` refuses because the suite is red or skipped | Claude cannot edit with no cycle open. The message gives the way out: restore the last good commit of `src tests` (or `git rm` the bad test file) in the gate terminal and commit. |
| A group forgot a step | Every gate refusal names the step: score missing, cycle open, SPEC.md missing or short, files changed. The Level 1 and Level 3 restarts are automatic at the unlock. |
| `./tdd score` slow or fails | It runs 18 pytest processes in parallel, normally 1–2 s. A group test that hangs is killed after 120 s. |
| Someone launched `claude --model opus` | The SessionStart hook warns in Claude's context only when Claude Code reports the model. Ask the group to restart with plain `claude`, then check `/status`. |
| Claude names the wrong model when asked | Not an override. Check `/status`. See "Which model is it, really?" above. |

## 5. Reset between runs

```zsh
cd dist/tdd-ladder
./gate reset                       # confirms, wipes .workshop/ and .tdd/, removes BRIEF.md and CLIENT_SPEC.md
git reset --hard start && git clean -fdx -e .venv -e .workshop   # restores the stub and empty tests; removes ignored results; keeps .venv
git branch | grep attempt- | xargs -n1 git branch -D   # optional: drop the attempt branches
```

A full rebuild (`tools/build.py … --keep-venv`) also works and gives fresh packs and secrets.

## 6. Giving the repo to group leaders

The participant repo is self-contained and must not include this file or `exercises/`. Either:

```zsh
cd dist/tdd-ladder
git bundle create ~/Desktop/tdd-ladder.bundle --all      # hand over the bundle
# leader: git clone tdd-ladder.bundle tdd-ladder && cd tdd-ladder && ./preflight --setup && ./preflight
# (preflight creates the level-0 state on first run; .workshop/ is not in git)
```

or push `dist/tdd-ladder` to a private remote. Leaders need Python 3.11+ (preflight uses the path baked in at build time, `/opt/homebrew/bin/python3.13`; otherwise `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`), git, and Claude Code 2.1.295 or later (the hooks use `onFailure: "block"`).

## 7. What to record in a trial

`.workshop/state.json` after the run holds per-level start/unlock times, hints used, failed attempts, skips, model power-ups and every score. `./tdd ladder` prints the score curve for the show-and-tell. `LOG.md` has the reflections and the Scribe's notes. Copy both out before `./gate reset`.
