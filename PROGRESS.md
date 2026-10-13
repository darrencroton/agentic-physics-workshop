# Progress

## Done (2026-10-12)

- **Phase 1** (`gatekit/`, `tools/build.py`): complete. 43 unit tests pass under Python 3.9 (`/usr/bin/python3`) and 3.14.
- **Phase 2, Exercise D** (`exercises/tdd-ladder/` → `dist/tdd-ladder/`): complete and reviewed (adversarial review; external panel rounds 1–5). Facilitator feedback round applied: automatic restart at the L0→L1 unlock, recovery advice in every refusal (Level 2 names the exact `git checkout <hash> -- <files>`), per-level plot copies, "Where we are" briefs, "Explain as you go" personas, a "which model am I" rule. `selftest/run.py` passes 109 checks.
- **Phase 4, Exercise B, Speed Run** (`exercises/speed-run/` → `dist/speed-run/`): built and reviewed. Design contract in `exercises/speed-run/PLAN.md` (brainstormed with Codex gpt-6.1-sol, numbers measured on the build machine). Four levels (measure; vectorise and survive the memory wall; reduce the work and defend the answer; open race), crypto gates for 0–2 and a verified gate for the race, a signed bench log with stale-evidence checks, a hidden submission catalogue, a C cell-list solution and a numpy calibration counter. `selftest/run.py` passes 82 checks in ~3.7 minutes (verify_assets, every level, every refusal, submit, install-solution, skip, reset). External panel round 1 (Codex gpt-6.1-sol, Claude Opus 5.5) findings all fixed or accepted (`docs/DECISIONS.md`); round 2 verified the fixes.
- `gatekit`: human-only commands come from the manifest (`human_only`), `race` is a frozen launcher, `model_check.py` reports the starting model, the template `.gitignore` covers compiled objects, `gate check` no longer double-prefixes failures.
- `README.md` is generic and points at each exercise's `FACILITATOR-WALKTHROUGH.md` for the specifics.
- Documentation by role (2026-10-13): `README.md` "Run the workshop" is the facilitator's checklist; each walkthrough is the operating guide for the facilitator (sections 1–2: build, rehearse, bundle, passphrase policy) and the group leaders (section 3 onwards: laptop set-up from the bundle, running the session, levels, troubleshooting, reset). `docs/00` §5 and §7 updated to match the build; `docs/02` and `docs/04` marked as designs superseded by the walkthroughs. Bundle clone and preflight verified for both exercises. Decisions in `docs/DECISIONS.md`.
- Environment: `dist/tdd-ladder/.venv` (Python 3.13.2; numpy 2.3.2, matplotlib 3.10.5, pytest 9.1.1) and `dist/speed-run/.venv` (adds scipy 1.17.0). Master passphrase in `~/.config/workshop/master-passphrase`.

## How to re-run everything

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/speed-run/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

Each self-test rebuilds its `dist/<name>` (keeping `.venv`) and leaves it clean at level 0.

## Next

1. Human calibration runs on Haiku for both exercises (`exercises/<name>/FACILITATOR-WALKTHROUGH.md`), then a trial with the research group. Watch, in particular: whether "Explain as you go" makes the literal persona narrate its design choices at TDD Level 0; whether a Haiku-written cell list fits the 14-minute Speed Run Level 2; the Speed Run Level 3 pacing with the ~20 s submit.
2. Phases 3 and 5 (Exercises A and C): not started. Gaps in BUILD-SPEC §9.

## Open questions

- Should `./tdd score` be allowed to Claude at Level 5 (collaborator)? Currently human-only at every level.
- Speed Run: room-wide leaderboard or within-group only (docs/02 §10)? The board is per repo; a facilitator can read `./race board` out.
- Speed Run on Intel Macs: the FMA trap does not fire without `-mfma`; Apple silicon is assumed.
- `BUILD-SPEC.md` still quotes the short reset (`git reset --hard start && ./gate reset`); left as the historical spec (the walkthroughs' reset is canonical).
