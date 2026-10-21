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

## Done (2026-10-15)

- **Four take-home skills** (`skills/`): `plan-code`, `style-code`, `test-code`, `review-code`, one generic SKILL.md each plus `skills/README.md` (install into `.claude/skills/` or `~/.claude/skills/`). `tools/build.py` copies the ones an exercise's manifest lists (`"skills"`) into `dist/<name>/.claude/skills/`; only Explorer lists them so far. Explorer uses them: the playbook prompts keep their wording and name the skill; `review-code` is a plain forked subagent (`context: fork`) and the `reviewer` agent is now the fallback. Briefs, personas, hints, `PLAYBOOK.md`, the participant `CLAUDE.md`, the manifest take-home note and the walkthrough updated; preflight and the self-test check the four files ship. Skill loading, invocation by name and the fork's round trip verified headless in a built repo on Claude Code 2.1.300 (`docs/DECISIONS.md`).

## Done (2026-10-16)

- **Other agent harnesses** (brief `docs/HARNESS-PORTABILITY.md`, decisions in `docs/DECISIONS.md`).
  - **Instruction files:** participant instructions are now `workshop/AGENTS.workshop.md`, built to `AGENTS.md`. The build renders `CLAUDE.md` from `gatekit/agents/CLAUDE.md`: `@AGENTS.md` plus a shared Claude Code section with the model, PERSONA and Skill-tool lines.
  - **`OTHER-AGENTS.md`:** ships only when the manifest sets `"other_agents": true`. Only Explorer does; TDD Ladder and Speed Run stay Claude Code only.
  - **Hooks:** not ported; the written rules are the fallback.
  - **Wording:** "Claude" became "the agent" in participant text and the Explorer walkthrough, with Claude Code keys in brackets. Explorer's Level 2 heading is now "## The agent's plan", with the gate updated to match.
  - **Review:** two rounds on the brief (Codex gpt-6.1-sol). Then an independent panel on the implementation (Codex gpt-6.1-sol and Claude Fable 5.1): round 1 APPROVE WITH CHANGES with no serious issues, all fixed; round 2 APPROVE from both.
  - **Receipts:** gatekit 68 tests on Python 3.14 and 3.9.6; ruff clean; self-tests TDD Ladder 112, Speed Run 82, Explorer 144.
  - **Headless Claude Code check** (2.1.301, built Explorer): the `@AGENTS.md` import loads, and the Level 0 persona arrives by hook.
- **Gate prompt UX and J/psi answer matching** (decisions in `docs/DECISIONS.md`).
  - **Prompts:** every gate question and reflection in the three exercises now ends in "?", ":" or a format hint. Multiple-choice prompts end "Your answer (a-d):", and asides come before the question. `./gate unlock` prints one "Quick reflection (saved to LOG.md, any answer is fine):" header, and `./tdd abort` explains before asking. `manifest.validate` enforces the ending rule.
  - **`contains`:** new optional list on `keyword` questions. An answer containing a term canonicalises to that term, and the build makes one slot per term. Explorer Level 1 accepts anything containing meson, psi or charmonium. `tools/build.py` now fails a build when a graded crypto question accepts no answers.
  - **Review:** external panel (Codex gpt-6.1-sol, Claude Fable 5.1). Round 1 ACCEPT from both, with one moderate and three minor findings: three fixed, one declined. Round 2 ACCEPT from both, with no findings.
  - **Receipts:** gatekit 72 tests on Python 3.14 and 3.9.6; ruff clean; self-tests TDD Ladder 112, Speed Run 82, Explorer 144.
- **Answers accepted when a group clearly knows them** (KISS scope; decisions and the dropped ideas are in `docs/DECISIONS.md`).
  - **Numbers:** any number in the answer counts (the last 6), and `%`, `k` and `M` are understood. A crypto gate tries one key per candidate, so each attempt can make up to 6 guesses.
  - **Choice:** a letter at the start of the answer wins, otherwise the only stand-alone letter.
  - **Explorer pulsars:** any answer containing sun, solar or earth passes.
  - **Speed Run pairs:** widened to about 499,402–500,092, using a 4-decimal log grid of 6 slots.
  - **TDD Ladder:** "none" answers and multi-id answers now pass where they should.
  - **gatekit fix:** `_grid` now aligns to rounded bounds.
  - **Review:** external panel (Codex gpt-6.1-sol, Claude Fable 5.1). Round 1: Codex REVISE (two parsing regressions, both fixed), Claude ACCEPT (four clean-ups applied). Round 2: ACCEPT from both.
  - **Receipts:** gatekit 75 tests on Python 3.14 and 3.9.6; ruff clean; self-tests TDD Ladder 112, Speed Run 82, Explorer 144.

## Done (2026-10-21)

- **Group UX round** (from the facilitator's Explorer playtest; decisions in `docs/DECISIONS.md`). Applies to all three exercises:
  - **Leader quickstarts:** `exercises/<name>/LEADER-QUICKSTART.md`, sent with the bundle and the walkthrough, not shipped.
  - **Shorter group docs:** README, briefs and LOG rewritten to one shape: Where we are, Do this, Watch for, The gate. Explorer's tool interface moved to `level0/INTERFACE.md`, frozen at every level.
  - **Explorer side tasks warn but pass:** acceptance-criteria count, decision lines, "Our list", the agent's test plan, guesses and triage now print `Note:` lines. Version control, two steps, tests and tool output stay strict.
  - **No typed reflections:** the manifest keys are now `talk`, `note` and `start`, and `crypto-reflection` is gone. The unlock screen shows a header with the target minutes, `Next: swap the Driver, then …`, `Brief: BRIEF.md (or ./gate brief)`, then "Talk it over (30 seconds, nothing to type)".
  - **Preflight:** `./preflight` sets up or repairs `.venv` itself; `--setup` forces a reinstall.
  - **No assumed folders:** the docs no longer name `~/Desktop`, `~/Downloads` or `~/opus-control`.
- **Review:** an external panel (Codex gpt-6.1-sol and Claude Opus 5.5, both on high effort) ran four rounds. All findings were verified and fixed; the tables are in `docs/DECISIONS.md`.
- **Receipts:** gatekit 82 tests on Python 3.14 and 3.9.6; ruff clean; self-tests Explorer 152, TDD Ladder 116, Speed Run 85.
- **Next:** rebuild each exercise and re-send bundles to leaders with the new quickstart. Any bundle already sent uses the old gate format. Then a live playtest of the new unlock screen and briefs.

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
2. Calibration run on Sonnet for Explorer (now on the agent-neutral wording), with a stopwatch (walkthrough section 1): record Level 1's time above all, now with two steps; if it still runs over 20 minutes, move part of Level 0 into the README. Watch that the heredoc commit, data reads and the reviewer's commands pass the guard in a live session. Also confirm in that run that plan mode's plan file is written without a guard refusal (the guard now allows `~/.claude/plans`), that `/` lists the four skills, and that the forked `review-code` review runs the tests (headless it chose not to) and comes back in a usable time.
3. Skills in the other two exercises: add `"skills"` to their manifests and name the skills in the briefs together, in a calibration pass. Natural places: `plan-code` at TDD Level 2 (the spec interview) and Speed Run Levels 1 and 2 (the optimisation plan); `test-code` at TDD Levels 1 and 3 (it must not override the oracle and phase rules); `review-code` at TDD Level 5 and on the Speed Run winning commit. Add in a calibration pass, one exercise at a time.
4. Phases 3 and 5 (Exercises A and C): not started. Gaps in BUILD-SPEC §9.
5. Other-harness rehearsals for Explorer (owner), following `docs/HARNESS-PORTABILITY.md` §7.
   - Copilot CLI first: do the imported `.claude/settings.json` hooks work, block every call, or do nothing? Does the Claude Code section of `CLAUDE.md` (which Copilot also reads) confuse it about reading skills?
   - Then one full Codex path.
   - Record the results in `docs/DECISIONS.md`, and adjust the opt-out line in `OTHER-AGENTS.md` if needed.

## Open questions

- Should `./tdd score` be allowed to Claude at Level 5 (collaborator)? Currently human-only at every level.
- Speed Run: room-wide leaderboard or within-group only (docs/02 §10)? The board is per repo; a facilitator can read `./race board` out.
- Speed Run on Intel Macs: the FMA trap does not fire without `-mfma`; Apple silicon is assumed.
