# Progress

## Done (2026-10-12)

- **Phase 1** (`gatekit/`, `tools/build.py`): complete. 43 unit tests pass under Python 3.9 (`/usr/bin/python3`) and 3.14.
- **Phase 2, Exercise D** (`exercises/tdd-ladder/` → `dist/tdd-ladder/`): complete and reviewed (adversarial review; external panel rounds 1–5). Facilitator feedback round applied: automatic restart at the L0→L1 unlock, recovery advice in every refusal (Level 2 names the exact `git checkout <hash> -- <files>`), per-level plot copies, "Where we are" briefs, "Explain as you go" personas, a "which model am I" rule. `selftest/run.py` passes 109 checks.
- **Phase 4, Exercise B, Speed Run** (`exercises/speed-run/` → `dist/speed-run/`): built and reviewed. Design contract in `exercises/speed-run/PLAN.md` (brainstormed with Codex gpt-6.1-sol, numbers measured on the build machine). Four levels (measure; vectorise and survive the memory wall; reduce the work and defend the answer; open race), crypto gates for 0–2 and a verified gate for the race, a signed bench log with stale-evidence checks, a hidden submission catalogue, a C cell-list solution and a numpy calibration counter. `selftest/run.py` passes 82 checks in ~3.7 minutes (verify_assets, every level, every refusal, submit, install-solution, skip, reset). External panel round 1 (Codex gpt-6.1-sol, Claude Opus 5.5) findings all fixed or accepted (`docs/DECISIONS.md`); round 2 verified the fixes.
- `gatekit`: human-only commands come from the manifest (`human_only`), `race` is a frozen launcher, `model_check.py` reports the starting model, the template `.gitignore` covers compiled objects, `gate check` no longer double-prefixes failures.
- `README.md` is generic and points at each exercise's `FACILITATOR-WALKTHROUGH.md` for the specifics.
- Documentation by role (2026-10-13): `README.md` "Run the workshop" is the facilitator's checklist; each walkthrough is the operating guide for the facilitator (sections 1–2: build, rehearse, bundle, passphrase policy) and the group leaders (section 3 onwards: laptop set-up from the bundle, running the session, levels, troubleshooting, reset). `docs/00` §5 and §7 updated to match the build; `docs/02` and `docs/04` marked as designs superseded by the walkthroughs. Bundle clone and preflight verified for both exercises. Decisions in `docs/DECISIONS.md`.
- Environment: `dist/tdd-ladder/.venv` (Python 3.13.2; numpy 2.3.2, matplotlib 3.10.5, pytest 9.1.1) and `dist/speed-run/.venv` (adds scipy 1.17.0). Master passphrase in `~/.config/workshop/master-passphrase`.

## Done (2026-10-14)

- **Phase 6, Exercise E, Explorer** (`exercises/explorer/` → `dist/explorer/`): built. Design in `docs/05-data-explorer.md`, build contract in `exercises/explorer/PLAN.md`, operating guide in `exercises/explorer/FACILITATOR-WALKTHROUGH.md`. Four levels on Sonnet (plan; build the prototype; test; review), all collaborator persona, no planted bugs; `crypto-reflection` gates for 0, 2 and 3 and one graded keyword question at Level 1 (`sun` or `jpsi`); every gate checks commits since the previous unlock and a clean tree. A shipped `reviewer` agent (`.claude/agents/reviewer.md`) gives the Level 3 fresh-context review. `selftest/run.py` passes 134 checks in about 61 s (both datasets, every refusal, skip, reset). Reference solution (`selftest/solution/`): 15 tests, 96% coverage. The generated page was rendered in Chrome: 2D to 3D switch, colour bar, hover, no console errors.
- Datasets: `pulsars.csv` 4,503 rows (ATNF v2.9.0, 451 KB; pulsars without a distance have `XX`, `YY`, `ZZ` blanked) and `dimuons.csv` the first 60,000 CMS Run2010B events (7.9 MB). The bundle is about 10 MB.
- `gatekit` fixes found by building E: the last level's crypto gate now gets a verify token in `tools/build.py` (an exercise ending on a crypto gate could never complete); the build wipe tolerates a Finder `.DS_Store` and always restores a stashed `.venv`; `out/` and `.coverage` added to the template `.gitignore`. Unit tests added for the first two.
- Environment: `dist/explorer/.venv` (Python 3.13.2; numpy 2.3.2, plotly 7.1.0, pytest 9.1.1, pytest-cov 7.1.0). Decisions and deviations from `docs/05` in `docs/DECISIONS.md`.

- **Explorer feedback round** (from a group playthrough to Level 3): plans have two steps (two or three at first, then two after the 2026-10-14 solo run) and Level 1 needs two commits; the Level 1 question is worded for the group's dataset and a wrong answer gives a hint (new optional gatekit question fields `text_from` and `wrong_hint`); every brief has one shape, with an "If it goes differently" section; review triage covers the top three to five findings, and fixes come with a test. The shared guard now reads quotes, heredocs and redirects: replaying the 29 refused playthrough commands allows 28 (the last is correctly refused). Self-tests: Explorer 136, TDD Ladder 109, Speed Run 82; gatekit 55 tests on Python 3.14 and 3.9.6. Details in `docs/DECISIONS.md`. Then tightened for time after the solo run: two steps, capped test plan and review (five to eight tests, three to five findings), prompts that write `TESTS.md` and `REVIEW.md` directly, one Level 0 prompt, one minute of play with one group feature, one fix at Level 3, and a Finished early section in the last brief. Explorer self-test: 137 checks.

- **Release-readiness pass** (2026-10-14): a combined code review, code-health and simplification pass, triaged by an external two-reviewer panel (Codex gpt-6.1-sol, Claude Opus 5.5), then implemented. Report: `archive/REVIEW-2026-10-14-release-readiness.md` (archived, not shipped); decisions in `docs/DECISIONS.md`. Fixed: `./tdd green` accepts a `pytest.raises` red; Explorer plan sections ignore `#` inside code fences; `*.dSYM/` ignored so `./race submit` is not blocked; the guard denies `git clean -x/-X`, covers the `Monitor` tool, resolves redirects against the hook `cwd` and a literal `cd`, treats `sed -i` in any option position and `>!` as writes, and no longer refuses Grep regexes such as `def .*json`; the shipped manifest carries no answer keys for crypto questions; cleaner errors for a damaged scoring pack and a missing Level 2 record; top-level `PLAN.md` archived. Receipt: gatekit 65 tests on Python 3.14 and 3.9.6; self-tests TDD Ladder 112, Speed Run 82, Explorer 138; ruff clean.

## How to re-run everything

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/speed-run/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/explorer/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

Each self-test rebuilds its `dist/<name>` (keeping `.venv`) and leaves it clean at level 0.

## Next

1. Human calibration runs on Haiku for both exercises (`exercises/<name>/FACILITATOR-WALKTHROUGH.md`), then a trial with the research group. Watch, in particular: whether "Explain as you go" makes the literal persona narrate its design choices at TDD Level 0; whether a Haiku-written cell list fits the 14-minute Speed Run Level 2; the Speed Run Level 3 pacing with the ~20 s submit.
2. Calibration run on Sonnet for Explorer, with a stopwatch (walkthrough section 1): record Level 1's time above all, now with two steps; if it still runs over 20 minutes, move part of Level 0 into the README. Watch that the heredoc commit, data reads and the reviewer's commands pass the guard in a live session. Also confirm in that run that plan mode's plan file is written without a guard refusal (the guard now allows `~/.claude/plans`), and that the `reviewer` agent runs cleanly under the guard (hooks do run inside subagents per the docs).
3. Phases 3 and 5 (Exercises A and C): not started. Gaps in BUILD-SPEC §9.

## Open questions

- Should `./tdd score` be allowed to Claude at Level 5 (collaborator)? Currently human-only at every level.
- Speed Run: room-wide leaderboard or within-group only (docs/02 §10)? The board is per repo; a facilitator can read `./race board` out.
- Speed Run on Intel Macs: the FMA trap does not fire without `-mfma`; Apple silicon is assumed.
