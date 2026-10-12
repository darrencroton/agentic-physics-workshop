# Plan: Phase 1 (gatekit + build) and Phase 2 (TDD Ladder → dist/tdd-ladder)

## Context

The repo is greenfield: only `CLAUDE.md`, `BUILD-SPEC.md` and `docs/` exist. Today's deliverable is the shared gate toolkit, the build tool, and the first exercise repo (`dist/tdd-ladder`), finishing with every self-test in BUILD-SPEC Section 7 passing, an adversarial review, and a facilitator walkthrough. Exercises A–C are out of scope.

`BUILD-SPEC.md` wins over `docs/`; deviations go in `docs/DECISIONS.md`. This plan file is copied to `PLAN.md` in the repo as the first write after approval, together with `docs/DECISIONS.md` (Claude Code facts, from the verification subagent).

## Environment (checked, nothing installed)

| Item | Found |
|---|---|
| Claude Code | 2.1.296 |
| `python3` on PATH | Homebrew 3.14.7 (no numpy/pytest/matplotlib) |
| Homebrew 3.13.2 | numpy 2.3.2, matplotlib 3.10.5, **no pytest** |
| macOS CLT `/usr/bin/python3` | 3.9.6 (numpy 2.0.2) → gatekit/hooks must run here |
| pytest | 9.1.1 only in an unrelated venv (`ai-agent-bench`) |
| scipy | nowhere (not needed for TDD) |
| `uv` | `/opt/homebrew/bin/uv` available |
| git | 2.54.0, identity Darren Croton / 2062219+darrencroton@users.noreply.github.com |

No interpreter has all three TDD packages, so `./preflight --setup` must install into `dist/tdd-ladder/.venv` (network). Proposed pins: `numpy==2.3.2`, `matplotlib==3.10.5`, `pytest==9.1.1` (the versions already present on the machine), on Python 3.13.

## Blocking questions (answered)

1. `.venv` Python: `/opt/homebrew/bin/python3.13` (3.13.2). Pins: `numpy==2.3.2`, `matplotlib==3.10.5`, `pytest==9.1.1`.
2. Approved: I run `./preflight --setup` once in `dist/tdd-ladder` (pip install into `.venv`, network). No other installs.
3. Master passphrase: I create `~/.config/workshop/master-passphrase` (mode 600) with a generated 6-word passphrase and print it once.

## Claude Code facts (verified by subagent against code.claude.com docs, Claude Code 2.1.296)

| # | Fact | Verdict | Design consequence |
|---|---|---|---|
| 1 | `"model": "haiku"` alias in project settings | Verified (aliases: haiku, sonnet, opus, …; full ID `claude-haiku-5-5`) | Keep alias |
| 2 | `PreModelSwitch` (v2.1.251+): input `from_model`, `to_model`, `requested_model`, `source`; matcher compares canonical name of `to_model`; deny = exit 2 or `hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason` (shown to user) | Verified | Matcher `.*`; script checks `to_model` itself; JSON deny; 30 s default timeout |
| 3a | `tool_input`: Read/Edit/Write `file_path`; Bash `command`; Grep/Glob `pattern`,`path`; NotebookEdit `notebook_path` | Verified | guard.py reads these |
| 3b | Exit 2 (stderr → Claude) or JSON `permissionDecision: "deny"` with reason → Claude | Verified | Use JSON deny; fail-closed on bad input |
| 3c | Exec form `"command": "python3", "args": [...]`, placeholders substituted | Verified | Use `${CLAUDE_PROJECT_DIR}` with braces |
| 3d | `onFailure: "block"` requires v2.1.295+ | Verified; 2.1.296 OK | Keep; also set `timeout` |
| 4 | `UserPromptSubmit` plain stdout on exit 0 → context (not shown to user); default timeout 30 s | Verified | teacher_context prints plain text |
| 5 | Deny rules: `Read(./.vault/**)` also blocks Edit/Write; Edit rules cover Write/NotebookEdit/MultiEdit; Bash rules split on `&&`/`;`/pipes, deny if any subcommand matches; `Bash(pip *)` does not cover `pip3`/`python3 -m pip`; Bash rules are not a security boundary | Verified | Add `Read(**/.vault/**)`, `Edit(**/.vault/**)`, `Edit(**/.workshop/**)`, `Bash(pip3 *)`, `Bash(python3 -m pip *)`, `Bash(uv *)`, `Bash(brew *)`; guard.py is the real guard |
| 6 | `permissions.defaultMode: "plan"` honoured from project settings (`auto`/`bypassPermissions` are not) | Verified | Keep |
| 7 | Trust: deny/ask rules apply before trust; `allow` rules wait for trust; hooks listed as "Used" for parent-trusted and `-p` cases; interactive first launch shows the dialog | Verified with gap | Facilitator checklist keeps "accept trust once"; preflight prints a reminder (cannot detect trust) |
| 8 | `SessionStart` may carry `model` but "not always"; no `CLAUDE_MODEL` env var | Verified | Add best-effort `SessionStart` hook that prints a warning into context if `model` is present and not allowed; log as honest limit |
| 9 | `/model` and picker fire `PreModelSwitch`; launch `--model` does not | Verified / not documented | Matches docs/00 honest limits |

These go into `docs/DECISIONS.md` verbatim (with URLs) as the first write after approval.

## Design decisions (my calls; recorded in DECISIONS.md)

- **dist layout for frozen tool sources:** `.gatekit/gatekit/` (toolkit package), `.gatekit/tddtool/` (exercise tool package), `.gatekit/levels/0/` (level 0 persona/hints/guard, non-secret, needed by `gate reset`), `.tdd-tools/tddlog.py` (pytest plugin). `gate`, `tdd`, `preflight` are thin launchers that put `.gatekit` on `sys.path`. Guard blocks reads/edits of `.gatekit/`, `.tdd-tools/`, `.claude/`, `.vault/`, `.workshop/`, `.tdd/`.
- **Verified gates:** per-level random 32-byte secrets and the scoring-pack secret live in `.vault/keys.bin`, obfuscated with a key derived from a build-time pepper embedded in `.gatekit/tddtool/_pepper.py` plus the exercise name. Documented as obfuscation only.
- **Each pack** carries one slot per accepted secret plus the master slot. Level N+1 pack is opened by `secret_N` (verified) or canonical-answer secrets (crypto).
- **Unlock flow** (`gate unlock`): condition check → graded questions (validators) → decrypt pack → copy `BRIEF.md`/declared files to repo paths, persona/hints/guard to `.workshop/levels/N+1/` → advance state → post-unlock action (L3: automatic `new-attempt`) → reflection question(s) appended to `LOG.md`.
- **Level 0 brief** is `README.md`; later levels write `BRIEF.md` at repo root (overwritten each level) and keep a copy in `.workshop/levels/N/`. Extra `gate brief` (no TTY) prints the current brief.
- **Phase `none` at Levels 3–4:** Claude may edit only `LOG.md`; guard message says to start a cycle with `./tdd red`. Level 5: phases optional, `src/**`, `tests/**`, `LOG.md` editable.
- **L2 "src/tests unchanged"** uses a content hash of `src/` and `tests/` recorded at L2 entry, independent of git.
- **`new-attempt`:** commit dirty work on the current branch, create `attempt-L<n>-<ts>` there, restore `src/hzbin/binning.py` and `tests/` from tag `start`, clean untracked files under `tests/`, commit "Level n: fresh start from the stub". Replaces `git checkout level1-start` (DECISIONS).
- **Scoring:** temp workspace per run, `-p no:cacheprovider`, own `pytest.ini` without `tddlog`, JUnit XML parsed with `xml.etree`, `ThreadPoolExecutor`, 60 s timeout per run, pack plaintext deleted in `finally`.
- **Model lock matching:** allowed entries are aliases; a target matches if the alias (lower-cased) is a substring of the target model string. Exact field names per DECISIONS.md.
- **Hook output:** `PreToolUse` deny via JSON `permissionDecision: "deny"` on stdout plus exit 0 (fallback exit 2 if docs say otherwise); malformed input → deny. `UserPromptSubmit` plain stdout. `PreModelSwitch` per DECISIONS.md.

## Phase 1: gatekit + tools/build.py

### Files

```
gatekit/
  README.md                    manifest schema, gate types, honest limits, Bash best-effort note
  gatekit/__init__.py
  gatekit/crypto.py            keystream, mac, slot wrap/unwrap, pbkdf2 (Section 4.5)
  gatekit/packs.py             deterministic tar.gz, pack/unpack, header JSON
  gatekit/answers.py           canonicalisation + slot-secret enumeration (Section 4.6)
  gatekit/state.py             atomic state.json, level timers, log helpers
  gatekit/manifest.py          load/validate manifest, level lookup
  gatekit/tty.py               require_tty, ask, ask_secret
  gatekit/exercise.py          loads the exercise tool module named in the manifest
  gatekit/cli.py               gate: status check unlock hint skip allow-model reset brief
  gatekit/hooklib.py           shared hook helpers (path normalisation, rule matching) used by templates
  templates/gate               launcher
  templates/preflight          check / --setup
  templates/Makefile.base      (optional; exercise supplies its own)
  templates/.gitignore
  templates/.claude/settings.json
  templates/.claude/hooks/{guard.py,model_lock.py,teacher_context.py}
  tests/test_crypto.py test_packs.py test_answers.py test_tty.py test_hooks.py test_state.py
tools/build.py
```

### Steps and verification

1. `crypto.py` + `packs.py` + tests: round-trip, master slot, tamper → MAC failure, identical tar bytes across two builds.
2. `answers.py` + tests: every synonym / grid value opens; wrong and out-of-range fail.
3. `state.py`, `manifest.py`, `tty.py` + tests: TTY refusal off-tty; success via `pty.fork`.
4. Hook templates + tests with synthetic hook JSON: guard blocks `.vault` read, `gate unlock` via Bash, `pip`, frozen-path edit, malformed input; allows normal edit. `model_lock` allow/deny. `teacher_context` prints persona per level.
5. `cli.py` end-to-end on a tiny fixture exercise (crypto gate) via pty.
6. `tools/build.py` on the fixture: wipe, copy, render, pack, scaffold, `git init`, commit, tag `start`.
7. Run `python3 -m unittest discover gatekit/tests` under `/usr/bin/python3` (3.9) and Homebrew 3.14. Commit "Phase 1: gatekit". Update `PROGRESS.md`.

## Phase 2: TDD Ladder

### Files

```
exercises/tdd-ladder/
  manifest.json
  make_data.py                 seeded generator for data/hz_mock.csv (edges hit, point at final edge, one empty bin)
  requirements.txt             pinned
  level0/  README.md LOG.md Makefile pytest.ini requirements.txt
           src/hzbin/{__init__,data,plot,binning}.py  tests/__init__.py  data/hz_mock.csv
  levels/0/ persona.txt hints.json guard.json       (non-secret)
  levels/1..5/ BRIEF.md persona.txt hints.json guard.json  (+ levels/3/CLIENT_SPEC.md)
  workshop/CLAUDE.workshop.md
  workshop/tddtool/{__init__,cli,phases,scoring,gates,attempts,_pepper(template)}.py
  workshop/tdd-tools/tddlog.py
  workshop/tdd                 launcher
  hidden/reference/binning.py  hidden/acceptance/test_*.py  hidden/mutants/M01..M16.py  hidden/mutants.json
  answers.json                 gate validator config (L4 numeric range etc.)
  selftest/run.py              scripted walkthrough via pty
  selftest/samples/{l0_naive,l1_tests_after,l2_SPEC.md,l3_cycles,l4_rung5}/...
  FACILITATOR-WALKTHROUGH.md
```

### Steps and verification

1. Data + package: `make_data.py`, `data.py`, `plot.py` (Agg), stub `binning.py`. `make plot` with a quick reference run.
2. Hidden assets: reference `BinnedResult` NamedTuple; ~12 acceptance tests; 16 mutants. Verify: reference passes all; each mutant fails ≥ 1 (script output shown).
3. `tddlog.py` plugin + `tdd status/test`: run records in `.tdd/runs.jsonl` with exception types.
4. `tdd red/green/refactor/done` with git checks; `new-attempt`; `ladder`.
5. `tdd score` (parallel, temp dirs, attribution, runtime printed) + score recording.
6. Gate conditions/validators (`gates.py`), manifest, level content (briefs, personas ≤150 words, hints ×3 tiers at 0/5/10 min, guard.json), `CLAUDE.workshop.md` with the Never list.
7. `tools/build.py tdd-ladder --master-passphrase-file …`; `./preflight --setup` (with permission); `./preflight`.
8. `selftest/run.py`: items 7.2.1–7.2.5 with expected bands; print score runtime. Fix until green; show output.
9. Adversarial review subagent (fresh `dist/`, try to reach `CLIENT_SPEC.md`/mutants without gates); fix cheap items; document "honest limits" in `gatekit/README.md`.
10. `FACILITATOR-WALKTHROUGH.md`, `PROGRESS.md`, commits.

## Test strategy

- Gatekit: stdlib `unittest`, run under 3.9 and 3.14, no network.
- TDD: `selftest/run.py` against a fresh build; sample suites are the calibration oracles (bands from Section 7.2). All transitions driven through `pty`.
- Hooks: synthetic JSON fixtures matching the verified schemas.
- Evidence: command + output pasted in the report at each milestone.

## Risks

| Risk | Mitigation |
|---|---|
| Hook schema/version mismatch (PreModelSwitch, onFailure, args form) | Subagent verification first; DECISIONS.md; fall back to shell-string commands and exit-2 deny if needed |
| Score runtime > 20 s (18 pytest subprocesses) | Parallel executor, small suites, measure and report; reduce sample Monte Carlo N |
| Sample Rung-4/5 suites not hitting bands | Iterate suites against mutants early (step 2) |
| pty-driven tests flaky (prompt timing) | Read-until-prompt helper with timeouts; deterministic prompts |
| Bash guard bypasses | Documented best-effort; `tdd` git-diff backstop; adversarial review |
| pip install needs network | Ask first; pinned versions already on machine |
