# Progress

## Done (2026-10-12)

- **Phase 1** (`gatekit/`, `tools/build.py`): complete. 38 unit tests pass under Python 3.9 (`/usr/bin/python3`) and 3.14. Commit `0ba09ef`.
- **Phase 2** (`exercises/tdd-ladder/` → `dist/tdd-ladder/`): complete. `selftest/run.py` passes 85 checks against a fresh build (BUILD-SPEC 7.2 items 1–5); score runs 1.3–1.7 s. Commit `82adf8e`.
- `docs/DECISIONS.md` records the Claude Code facts verified against 2.1.296 and every deviation from `docs/`.
- `exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md` has the manual-walkthrough commands, per-level observations, reset and distribution.
- Environment: `.venv` at `dist/tdd-ladder/.venv` (Python 3.13.2; numpy 2.3.2, matplotlib 3.10.5, pytest 9.1.1). Master passphrase in `~/.config/workshop/master-passphrase`.

## How to re-run everything

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

The self-test rebuilds `dist/tdd-ladder` (keeping `.venv`) and leaves it clean at level 0.

## Next

1. Adversarial review findings → fix cheap items, document the rest in `gatekit/README.md` ("Honest limits").
2. External review panel (orchestrator: Codex gpt-6.1 sol high, Claude Opus 5.5 high); iterate on serious findings only.
3. Human calibration runs in `dist/tdd-ladder` on Haiku (facilitator), then a trial with the research group. Adjust persona/hint text in `exercises/tdd-ladder/levels/` and rebuild.
4. Phases 3–5 (Exercises A, B, C): not started. Gaps listed in BUILD-SPEC Section 9. The gatekit crypto-gate path is exercised only by the fixture in `gatekit/tests/`.

## Open questions

- Should `./tdd score` be allowed to Claude at Level 5 (collaborator)? Currently human-only at every level.
- The L2 "code untouched" check compares a content hash from the moment Level 2 began; a group that committed nothing at Level 1 and runs `git checkout -- src` will fail the check (the message now says to restore the files as they were).
