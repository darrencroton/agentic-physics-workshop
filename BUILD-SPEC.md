# Build Spec — Workshop Exercise Repos

*Engineering spec for building the participant repos described in `docs/`. The docs define what each exercise teaches; this spec defines how the repos are built. It also resolves the gaps and contradictions in the docs.*

---

## 0. Scope and Build Order

| Phase | Deliverable | Done when |
|---|---|---|
| **1** | `gatekit/` + `tools/build.py` | Gatekit self-tests pass (Section 7.1) |
| **2** | `exercises/tdd-ladder/` → `dist/tdd-ladder/` | TDD self-tests pass (Section 7.2); I can run a manual walkthrough |
| 3 | Two Roads (A) | Later session |
| 4 | Speed Run (B) | Later session |
| 5 | Fortran Archaeology (C) | Later session |

Phases 3–5 have their own known gaps (Section 9). Don't start them unless asked.

**Out of scope for you:**

- Calibration runs with Haiku and Sonnet.
- Timing the levels.
- Running a real participant session.

These need a human driving a separate Claude Code session in `dist/<name>/`. Your job ends at a repo that self-tests clean, plus instructions for me to walk it manually.

---

## 1. Workspace and Build Pipeline

```
ai-project-session/                 # top-level git repo (dist/ and **/.venv/ gitignored)
├── CLAUDE.md, BUILD-SPEC.md, PROGRESS.md
├── docs/                           # design docs 00–04 + DECISIONS.md
├── gatekit/
│   ├── gatekit/                    # python package: crypto, packs, answers, state, manifest, tty, cli
│   ├── templates/                  # gate, preflight, .claude/settings.json, hooks/*.py, .gitignore
│   └── tests/                      # gatekit self-tests (stdlib unittest)
├── exercises/
│   └── tdd-ladder/
│       ├── manifest.json           # levels, personas, guards, gates, hints (Section 4.3)
│       ├── level0/                 # participant-visible starting content (README, src stub, data…)
│       ├── levels/1..5/            # per-level content to pack: BRIEF.md, persona.txt, hints.json, guard.json, extra files
│       ├── workshop/               # CLAUDE.workshop.md, exercise-specific tools (tdd), pytest plugin
│       ├── hidden/                 # reference impl, mutants, acceptance tests (packed into .vault)
│       ├── answers.json            # gate answers/validators (never copied to dist)
│       └── selftest/               # scripted walkthrough, sample suites, expected score bands
├── tools/build.py                  # build <exercise> --master-passphrase-file <path> [--out dist/<name>]
└── dist/<name>/                    # generated; its own git repo
```

### `tools/build.py <exercise>` Must:

1. Wipe and recreate `dist/<name>/`.
2. Copy `level0/`, the gatekit templates and the exercise tools.
3. Render `CLAUDE.workshop.md` → `CLAUDE.md`.
4. Pack `levels/N` → `.vault/levelN.pack` and `hidden/` → `.vault/scoring.pack`.
5. Write `.workshop/` scaffolding (gitignored).
6. Run `git init`, commit as "Workshop start", and tag `start`.

**Determinism:** the same inputs give the same plaintext. Packs may differ only by random salts and nonces.

**Master passphrase:** read from a file outside the repo. Never stored in any repo. Ask me for its location.

---

## 2. Environment and Dependencies

### Python

- Exercise code runs in `dist/<name>/.venv`, created from a Python ≥ 3.11 interpreter. Ask me which one; check `python3 --version` and Homebrew/pyenv paths.
- **Pinned `requirements.txt`** for the TDD exercise: `numpy`, `pytest`, `matplotlib`. Use the versions already on my machine if present; otherwise ask.
- Gatekit, hooks and the `gate`/`tdd` CLIs run under whatever `python3` is on `PATH` (macOS CLT ships 3.9), so they must be **stdlib-only and 3.9-compatible**.
- When a gatekit command needs the exercise environment (running checks, pytest or scoring), it **re-executes under `.venv/bin/python`**.

### `preflight`

Two modes:

| Mode | Behaviour | Who runs it |
|---|---|---|
| `./preflight` | Check only: venv present, packages importable at pinned versions, git identity, hooks syntax, manifest/state integrity, `./gate status` works, TTY detection works | Anyone |
| `./preflight --setup` | Creates `.venv` and installs `requirements.txt` | **Humans only, during setup.** Do not run it yourself without asking me. |

### Make

The `Makefile` uses `PY ?= .venv/bin/python`.

---

## 3. Claude Code Facts to Verify First

Verify each against current docs (https://code.claude.com/docs: hooks, settings, permissions, model-config) and the installed `claude --version`. Record the results in `docs/DECISIONS.md`. Delegate to a subagent if useful.

1. `"model": "haiku"` (alias) is accepted in project `.claude/settings.json`.
2. **`PreModelSwitch`:**
   - input field names (expected `from_model`, `to_model`);
   - canonical model-name format for the matcher;
   - deny output format.
3. **`PreToolUse`:**
   - `tool_input` field names for `Read`, `Edit`, `Write`, `Bash`, `Grep`, `Glob`, `NotebookEdit`;
   - exit-2 and `permissionDecision: "deny"` behaviour;
   - exec form with `args`;
   - the `onFailure: "block"` minimum version.
4. `UserPromptSubmit`: plain stdout on exit 0 is added to context, and the timeout default.
5. Permission rule syntax and semantics for `Read(./.vault/**)` and `Bash(...)` deny rules in project settings.
6. `permissions.defaultMode: "plan"` is honoured from project settings.
7. Project hooks require **workspace trust**; how a fresh clone behaves before trust is accepted.
8. Whether a hook can see the session's current model (`SessionStart` `model` field) to warn on a launch-time `--model` override.

If a fact differs from `docs/00` Section 5.5, adapt the design and log it.

---

## 4. Gatekit Spec

### 4.1 Commands (`./gate`)

| Command | TTY required | Behaviour |
|---|---|---|
| `status` | No | Current level, persona, minutes on level, hints used, allowed models |
| `check` | No | Runs the level's check; prints PASS/FAIL with a reason (never the expected answer) |
| `unlock` | **Yes** | Runs the check, asks the gate question(s), unlocks the next level, then asks the reflection question and appends the answer to `LOG.md` |
| `hint` | **Yes** | Shows the next tier whose time lock has expired, and logs it |
| `skip --master` | **Yes** | Prompts for the master passphrase (`getpass`); unlocks the next level; asks for and logs a reason |
| `allow-model <name>` | **Yes** + master | Facilitator power-up; updates `allowed_models` |
| `reset` | **Yes** | Confirms, then wipes `.workshop/` state back to level 0 |

### 4.2 TTY Rule

- TTY-required commands check that **both** `sys.stdin.isatty()` and `sys.stdout.isatty()` are true, and refuse otherwise with: *"This command is for humans, in the gate terminal."*
- Answers are read with `input()` (visible). Passphrases are read with `getpass`.
- Self-tests drive these commands through a pseudo-terminal (stdlib `pty` / `os.openpty`).
- **Known limitation, document it:** Claude could also use `pty`. The guard heuristics and `CLAUDE.md` rule against this; it is part of the "honest limits".

### 4.3 Manifest (`exercises/<name>/manifest.json`)

Illustrative; adapt as needed and document the final schema in `gatekit/README.md`.

```json
{
  "exercise": "tdd-ladder",
  "title": "The TDD Ladder",
  "models": {"default": "haiku", "allowed": ["haiku"]},
  "levels": [
    {
      "id": 0,
      "title": "Just build it",
      "persona": "literal",
      "target_minutes": 5,
      "gate": {
        "type": "verified",
        "condition": "tdd.score_recorded_at_level",
        "questions": [{"id": "acceptance_count", "prompt": "How many client acceptance tests passed?",
                       "validator": "tdd.equals_last_acceptance_count"}],
        "reflection": "Name two decisions Claude made that nobody asked you about."
      }
    }
  ]
}
```

Per-level files live in `levels/N/` and are packed: `BRIEF.md`, `persona.txt`, `hints.json` (tiers with `unlock_after_minutes`), `guard.json` (path rules), plus any new participant files (e.g. `CLIENT_SPEC.md`). On unlock, `BRIEF.md` and new participant files are copied to their repo locations as declared in the manifest. Persona, hints and guard stay in `.workshop/levels/N/`.

### 4.4 Gate Types

| Type | Key material | Use |
|---|---|---|
| `crypto` | T ‖ 0x00 ‖ canon(A). T = SHA-256 of the check's canonical output (sorted-key JSON, floats at a stated number of significant figures). The check ships `verify = SHA-256("verify" ‖ T)` so it can say PASS/FAIL without holding answers. | Fixed correct answers (Exercises A, C, most of B) |
| `crypto-reflection` | T only; questions are logged, not graded | Fixed checks, reflective questions |
| `verified` | A per-level secret held by the exercise tool (in `.vault/keys.bin`, protected by the guard and deny rules). Released only when the tool's own validators pass, including **dynamic validators** that compare answers with local results (e.g. the last score). | Group-specific outcomes (all TDD gates; the race in B) |

Be explicit in `gatekit/README.md` that `verified` gates are a soft barrier (obfuscation), and that `crypto` gates are only as strong as the answer space (a small multiple-choice space is guessable).

### 4.5 Pack Format and Crypto (stdlib, Pedagogical-Grade)

**Content:** a deterministic `tar.gz` (stdlib `tarfile`, fixed mtimes, sorted entries) of the level directory.

**Encryption:**

- A random 32-byte content key K.
- Keystream = `shake_256(K ‖ nonce16).digest(len)`; ciphertext = plaintext XOR keystream.
- MAC = `HMAC-SHA256(SHA-256("mac" ‖ K), header_bytes ‖ nonce ‖ ciphertext)`.

**Key slots** (LUKS-style), one per accepted secret S:

- `d = pbkdf2_hmac("sha256", S, slot_salt, 100_000, dklen=64)`.
- `wrapped = K XOR d[:32]`; `tag = HMAC(d[32:], K)`.
- Unlocking tries each slot and accepts the one whose tag verifies.
- One slot per accepted canonical answer, plus a master-passphrase slot on every pack.

**File:** a JSON header (version, exercise, level, slots, nonce, MAC), a newline, then the base64 ciphertext.

**On failure:** "Not quite. Discuss and try again." Log the attempt (timestamp only; never the answer text for crypto gates).

### 4.6 Answer Canonicalisation

| Kind | Canonical form | Slots built for |
|---|---|---|
| `keyword` | NFKC, case-fold, strip whitespace and punctuation, Greek/Latin aliases (Ω→omega) | Each synonym in the list |
| `choice` | Single lower-case letter | The correct letter(s) |
| `numeric` | Parse float (allow units and sci notation; strip non-numeric suffixes), round to `decimals` | Every grid value in `[lo, hi]` at that step |
| `numeric-log` | Round log10(value) to `decimals` | Every log-grid value in range |
| `free` | — | None (logged only) |

### 4.7 State

`.workshop/state.json` is gitignored and written only by `gate` / exercise tools. It records:

- the level and its start/unlock timestamps;
- the persona;
- hints used;
- failed attempts;
- `allowed_models`;
- skips with their reasons;
- exercise-specific records (e.g. scores).

Write it atomically (temporary file + rename).

### 4.8 Hooks (Templates, stdlib)

**`teacher_context.py`** (`UserPromptSubmit`): prints a short block built from `.workshop/levels/<current>/persona.txt`:

```
WORKSHOP LEVEL n — <title> — persona: <mode>
<rules>
```

**`guard.py`** (`PreToolUse`, `onFailure: "block"`):

- Loads the global rules plus the current level's `guard.json` (and, for TDD, `.tdd/phase`). Denies with a teaching message.
- **Always blocks:** access to `.vault/`, `.workshop/`, `.tdd/` writes, `.claude/`, gatekit and exercise tool sources; Bash commands that mention these paths, `gate unlock|hint|skip|reset|allow-model`, TTY-only `tdd` subcommands, `pty`, package managers, or redirection/`sed -i`/`tee`/`cp`/`mv` into frozen paths. Bash matching is best-effort; document this in `gatekit/README.md`.
- **Invalid or missing input:** fail closed with a clear message.

**`model_lock.py`** (`PreModelSwitch`): allows the switch only if the target matches an entry in `allowed_models`. Otherwise it denies with: *"Today's exercise uses <model>. Ask a facilitator for a power-up."*

**`settings.json` template:** as in `docs/00` Section 5.5, corrected per Section 3 of this spec. (As built: `gatekit/templates/.claude/settings.json`; `docs/00` no longer carries the skeleton.)

### 4.9 Participant `CLAUDE.md`

Built from `workshop/CLAUDE.workshop.md`, as drafted in each exercise doc. It must include the "Never" list matching the guard.

---

## 5. Exercise D: TDD Ladder Build Spec

Follow `docs/04-tdd-ladder.md` with these resolutions.

### 5.1 Repo (`dist/tdd-ladder/`)

```
README.md  CLAUDE.md  LOG.md  SPEC.md (absent until L2)  Makefile  pytest.ini  requirements.txt
gate  tdd  preflight
src/hzbin/__init__.py  data.py  plot.py  binning.py (stub raising NotImplementedError, final signature + docstring)
tests/__init__.py (empty)
data/hz_mock.csv
.tdd-tools/tddlog.py           pytest plugin, loaded via pytest.ini (-p tddlog, pythonpath .tdd-tools)
.claude/settings.json  .claude/hooks/*.py
.vault/level1..5.pack  .vault/scoring.pack  .vault/keys.bin
.workshop/  .tdd/              gitignored
```

### 5.2 Data and Domain

- **`data/hz_mock.csv`:** ~40 H(z) points generated by a committed script in `exercises/tdd-ladder/` from flat ΛCDM (H₀ = 70, Ωm = 0.3), z ∈ [0.07, 2.0], with heteroscedastic σ of 4–20%. Use a fixed seed.
  - Include points exactly at the default plot bin edges, **one exactly at the final edge** (so S1 matters), and one region giving an empty bin.
- **`plot.py`:** `make plot` writes `results/hz_binned.png` using the matplotlib Agg backend. Data points with error bars, the binned means at `x_eff`, and the fiducial curve.

### 5.3 The `tdd` Tool

| Command | TTY | Behaviour |
|---|---|---|
| `status` | No | Level, phase, cycle count, last score summary |
| `test` | No | Runs pytest in `.venv` (Claude may use this or plain pytest) |
| `red "<behaviour>"` | Yes | Level ≥ 3 only; entry conditions per doc Section 6 |
| `green` | Yes | Checks new tests are committed; runs pytest; ≥ 1 failure; failure types limited to `AssertionError` or `NotImplementedError` (read from the plugin's records); previously passing tests still pass. Freezes `tests/`. |
| `refactor` | Yes | All tests pass; `tests/` unchanged since `green` (git diff against the recorded commit) |
| `done` | Yes | All pass; committed; closes the cycle in `.tdd/cycles.jsonl` |
| `score` | Yes | Acceptance, mutants killed and false alarms (format in doc Section 5); records the score against the current level |
| `new-attempt` | Yes | Commits the current work to branch `attempt-L<n>-<timestamp>`; restores `src/hzbin/binning.py` and `tests/` to `start`. **Replaces** the doc's `git checkout level1-start`; log this in `DECISIONS.md`. |
| `ladder` | No | Table of recorded scores by level (for the show-and-tell) |

`tdd` implements the `verified` gate conditions and validators and calls gatekit to unlock. `./gate unlock` delegates to `tdd` for this exercise.

### 5.4 Run Logging (`.tdd-tools/tddlog.py`)

The plugin appends to `.tdd/runs.jsonl` on every pytest session, including runs Claude starts directly. Each record holds:

- timestamp and git HEAD;
- phase;
- per-test outcome;
- failure exception type (via `pytest_runtest_makereport` / `excinfo.typename`).

This lets `tdd` report "red never observed" at Level 1, and validates "failing for the right reason" at Level 3.

### 5.5 Scoring

- Decrypt `scoring.pack` into a temp dir, then delete it afterwards, even on error.
- Run in parallel (`concurrent.futures`):
  - **Acceptance:** hidden acceptance tests (~12) against the group's `binning.py`.
  - **Mutants killed:** the group's `tests/` against each of the 16 mutants (doc Section 8).
  - **False alarms:** the group's `tests/` against the reference.
- Copy the repo's `src/` and `tests/` to a temp workspace and swap in `binning.py`; set `-p no:cacheprovider`; disable the run-logging plugin for scoring runs.
- **Survivors** are reported by spec ID only.
- **False-alarm attribution:** a test that fails on the reference but passes on mutant Mk is reported as "conflicts with S(Mk)". Otherwise report "conflicts with: unknown".
- **Target runtime:** < 20 s on an Apple-silicon laptop. Report the measured time in the self-test output.

### 5.6 Gates (All `verified`; Corrects doc Section 7 Inconsistencies)

| Transition | Condition | Graded question | Logged reflection |
|---|---|---|---|
| 0 → 1 | Score recorded at L0. The unlock then runs `new-attempt` itself (facilitator feedback; see `docs/DECISIONS.md`) | Acceptance count = last recorded count | Two silent decisions |
| 1 → 2 | A score recorded at L1 after the latest fresh attempt (made automatically on unlock, or by `./tdd new-attempt`) | — | Red ever seen (y/n); oracle source (a–d) |
| 2 → 3 | `SPEC.md` has ≥ 6 numbered decisions; `src/` and `tests/` unchanged during L2 | — | *After* unlock, once `CLIENT_SPEC.md` is visible: "How many of the client's 10 decisions did your SPEC address?" (0–10) |
| 3 → 4 | ≥ 5 cycles valid per 5.3; last score has 0 false alarms and ≥ 9/16 killed | A spec ID among the last survivors, or `none` if 16/16 | — |
| 4 → 5 | Last score ≥ 14/16, 0 false alarms; own suite runtime < 10 s | numeric 0.0090–0.0096 | — |
| 5 (end) | `LOG.md` contains a `## Mutation report` section | — | "One test you'd delete and why" |

**Level 3 starts from the stub:** the unlock runs the equivalent of `new-attempt` automatically, and says so.

### 5.7 Personas and Guards

| Level | Persona | Editable by Claude |
|---|---|---|
| 0–1 | `literal` | `src/hzbin/binning.py`, `tests/**`, `LOG.md` |
| 2 | `coach` | `SPEC.md`, `LOG.md` only |
| 3–4 | `coach` + phase rules | Per doc Section 6 phase table |
| 5 | `collaborator` | `tests/**`, `src/**`, `LOG.md` |

Write `persona.txt` for every level, using doc Section 9 as the basis. Persona text addresses Claude in the second person and stays under ~150 words.

### 5.8 Participant Text

- `README.md` = the Level 0 brief: the story, roles summary, the two-window setup, and the client's request verbatim.
- Each `BRIEF.md` follows the doc's level brief.
- Hints: three tiers per level, unlocking at 0, 5 and 10 minutes. Write them from the doc's lessons.

---

## 6. Hidden Assets (TDD)

| Asset | Requirement |
|---|---|
| `hidden/reference/binning.py` | Implements `CLIENT_SPEC` S1–S10 exactly; returns a `NamedTuple` `BinnedResult(x_eff, mean, err, n, n_dropped)` |
| `hidden/acceptance/` | ~12 tests covering every S-decision; all pass on the reference |
| `hidden/mutants/M01..M16.py` | Each is the reference with exactly one change from doc Section 8. Each must fail ≥ 1 acceptance test. |

---

## 7. Self-Tests and Acceptance Criteria

### 7.1 Gatekit (stdlib `unittest`, run without network)

- Pack round-trip.
- A wrong answer fails; every accepted synonym and numeric grid value succeeds; out-of-range values fail.
- The master slot opens every pack; a tampered ciphertext fails its MAC.
- The deterministic tar has identical bytes across builds.
- TTY refusal when not on a TTY; success through a pty.
- **`guard.py`, against synthetic hook JSON:** blocks `.vault` read, `gate unlock` via Bash, pip, frozen-path edits, and malformed input; allows normal edits.
- **`model_lock.py`:** allows an allowed model; denies others.
- **`teacher_context.py`:** prints the right persona per level.

### 7.2 TDD (`exercises/tdd-ladder/selftest/run.py`, Against a Fresh Build)

1. `tools/build.py tdd-ladder` produces a clean repo with tag `start`; `./preflight` passes (given an existing `.venv`).
2. The reference passes all acceptance tests; each mutant fails ≥ 1.
3. **Scripted walkthrough (via pty), with expected bands:**
   - **L0:** a sample naive implementation and suite → acceptance 4–9/12, kills ≤ 6.
   - **L1:** a sample "tests-with-code" suite → red never observed.
   - **L2:** a sample `SPEC.md`.
   - **L3:** five scripted cycles, plus a sample Rung-4 suite → ≥ 9 kills, 0 false alarms. Also check that:
     - `green` refuses a test that fails with `ImportError`;
     - the guard blocks a `tests/` edit in green;
     - `refactor` refuses after a Bash edit to `tests/`.
   - **L4:** a sample Rung-5 suite → ≥ 14 kills, 0 false alarms, < 10 s.
   - **L5:** completes.
4. Every gate rejects a wrong graded answer. The master skip works.
5. Score runtime is reported (target < 20 s).

**Finish with:** an adversarial review subagent that tries to reach `CLIENT_SPEC.md` or the mutants from a fresh `dist/` without the gates, and reports what succeeded. Document the findings under "honest limits" in `gatekit/README.md`. Fix anything that's cheap to fix.

### 7.3 Hand-Off

Write `exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md`. Keep it out of the participant repo, because it contains spoilers. It should cover:

- exact zsh commands to set up and run a manual walkthrough with Claude Code on Haiku;
- what to observe at each level;
- how to reset (`git reset --hard start && ./gate reset`).

---

## 8. Working Approach

1. Plan mode first. Read this spec, `CLAUDE.md`, `docs/00` and `docs/04` in full (skim `01`–`03`). Verify Section 3.
2. Write `PLAN.md`: tasks per phase, file list, test strategy, risks. Ask me **all** blocking questions in one batch before building.
3. Build in small verified steps, committing at each milestone. Update `PROGRESS.md` at each phase end.
4. Report the self-test output at the end of each phase. Don't claim completion without it.

---

## 9. Known Gaps for Later Exercises (Don't Build Yet)

| Exercise | Gaps to resolve when we get there |
|---|---|
| **A: Two Roads** | Mock siren catalogue generator and fiducial values; H₀ inference implementation and runtime; canonical-output definitions for each crypto check (significant figures); confirm the four bugs produce the intended ΔH₀ split; matplotlib for the ratio plot |
| **B: Speed Run** | Straddler-pair construction and verification; golden counts at 200k via an independently verified fast counter; the `race` calibration implementation; `race.toml` schema; verifying the FMA trap on the pinned Apple `clang`; Level 0 `numeric-log` answers |
| **C: Fortran** | Licence and download of `halofit.f`; fill the doc's placeholders by inspecting the source; `gfortran` availability (ask before installing); `driver.f`; linear P(k) inputs; golden and intermediate outputs; a partially ported fallback |
