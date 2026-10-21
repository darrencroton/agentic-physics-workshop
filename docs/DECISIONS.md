# Decisions Log

Deviations from `docs/` and verified Claude Code facts. One line of reason each. Newest at the bottom of each section.

## Claude Code facts (verified 2026-10-12 against https://code.claude.com/docs, installed Claude Code 2.1.296)

Verified by a subagent that fetched the current pages: `hooks`, `hooks-guide`, `permissions`, `permission-modes`, `settings-reference`, `model-config`, `security`. Changelog not checked.

| # | Spec item (BUILD-SPEC §3) | Verdict | Finding | Design consequence |
|---|---|---|---|---|
| 1 | `"model": "haiku"` alias in project settings | Verified | `model` accepts an alias or a full ID. Aliases: `default`, `best`, `fable`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`, `opus[1m]`, `opusplan`. Current Haiku ID: `claude-haiku-5-5`. Precedence: `/model` > `--model` > `ANTHROPIC_MODEL` > `model` setting. | Keep the alias. |
| 2 | `PreModelSwitch` | Verified (needs v2.1.251+) | Input: common fields plus `from_model`, `to_model`, `requested_model`, `source` (`command`, `picker`, `config`), cache fields. Matcher compares the canonical name derived from `to_model` (alias, dated ID and Bedrock ID all canonicalise; `[1m]` suffix ignored); unknown names run every hook. Deny: exit 2 (stderr shown to user) or `{"hookSpecificOutput": {"hookEventName": "PreModelSwitch", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`; the reason is shown to the user. Only `allow`/`deny`/`ask`. Default timeout 30 s; a timeout blocks the switch. | Matcher `.*`; `model_lock.py` inspects `to_model` itself and emits the JSON deny. |
| 3a | `PreToolUse` `tool_input` fields | Verified | `Read`: `file_path`, `offset`, `limit`. `Edit`: `file_path`, `old_string`, `new_string`, `replace_all`. `Write`: `file_path`, `content`. `Bash`: `command`, `description`, `timeout`, `run_in_background`. `Glob`: `pattern`, `path`. `Grep`: `pattern`, `path`, `glob`, `output_mode`, … `NotebookEdit`: `notebook_path`. `MultiEdit` is legacy, schema undocumented. | `guard.py` reads these fields; unknown tool with a path-like field is denied (fail closed). |
| 3b | Exit 2 vs JSON deny | Verified | Exit 2 routes like `deny`: Claude sees stderr as the reason. JSON `permissionDecision: "deny"` with `permissionDecisionReason` is shown to Claude. A hook deny cannot be overridden by an allow rule. | `guard.py` emits the JSON deny on stdout with exit 0; malformed input also denies. |
| 3c | Exec form with `args` | Verified | `"command"` is resolved as an executable and spawned with `args` as the argv, no shell. Placeholders such as `${CLAUDE_PROJECT_DIR}` are substituted in exec form; bare `$CLAUDE_PROJECT_DIR` is only documented for shell form. | Use exec form with `${CLAUDE_PROJECT_DIR}` (braces). |
| 3d | `onFailure: "block"` | Verified; 2.1.296 qualifies | "Requires Claude Code v2.1.295 or later." Applies to `command` and `http` hooks; needed to block on timeout. | Keep `onFailure: "block"` and set an explicit `timeout`. |
| 3f | Hook timeouts | Verified | Default 600 s for command hooks, lowered to 30 s on `UserPromptSubmit`, `PreModelSwitch`, `PostModelSwitch`. Key `timeout` (seconds) per handler. | Set `timeout: 10` on all workshop hooks. |
| 4 | `UserPromptSubmit` stdout | Verified | Plain-text stdout on exit 0 is added as context Claude can see (not a visible transcript entry). JSON alternative: `hookSpecificOutput.additionalContext`. Exit 2 blocks the prompt. Default timeout 30 s. | `teacher_context.py` prints plain text. |
| 5 | Permission rule syntax | Verified | Path patterns use gitignore syntax; `./path` is relative to cwd; `**/.vault/**` matches at any depth. A `Read` deny also blocks `Edit`/`Write` on that path, applies to recognised Bash file commands (`cat`, `head`, `tail`, `sed`, `tee`) and redirect targets, best-effort to Grep/Glob, and not to scripts that open files themselves. `Edit` rules cover `Write`, `NotebookEdit`, `MultiEdit`. Bash rules: `*` after a space; `Bash(pip *)` does not match `pip3` or `python3 -m pip`; compound commands are split on `&&`, `\|\|`, `;`, `\|`, newlines and a deny applies if any subcommand matches; wrappers like `timeout`, `nice`, `command` are stripped; deny rules are "not a security boundary" (`/bin/rm`, `bash -c`, `git -C`). | Deny list: `Read(./.vault/**)`, `Read(**/.vault/**)`, `Edit(./.vault/**)`, `Edit(**/.vault/**)`, `Edit(./.workshop/**)`, `Edit(./.gatekit/**)`, `Edit(./.claude/**)`, `Bash(./gate unlock *)`, `Bash(pip *)`, `Bash(pip3 *)`, `Bash(python3 -m pip *)`, `Bash(python -m pip *)`, `Bash(uv *)`, `Bash(brew *)`, `Bash(npm *)`, `Bash(conda *)`. `guard.py` is the real guard. |
| 6 | `permissions.defaultMode: "plan"` | Verified | Valid values `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`; only `auto` and `bypassPermissions` are ignored from project settings. | Keep `"plan"`. |
| 7 | Workspace trust | Verified, one gap | `deny`/`ask` rules apply before trust; `permissions.allow` and `additionalDirectories` wait for trust. Hooks are listed as "Used" when the parent folder is trusted or in `claude -p`. The interactive first launch shows the trust dialog; the docs do not state whether hooks wait for it. `/hooks` lists loaded hooks. | Facilitator checklist keeps "open `claude` once and accept trust". `preflight` prints this reminder; it cannot detect trust. |
| 8 | Model visible to hooks | Verified | Only `SessionStart` can carry a `model` field, and "Claude Code doesn't always include it". No `CLAUDE_MODEL` env var. `CLAUDE_EFFORT` exists. | Add a best-effort `SessionStart` hook (`model_check.py`) that prints a warning into context when `model` is present and not allowed. Listed under honest limits. |
| 9 | What fires `PreModelSwitch` | Verified / not documented | `/model`, the picker and `/config` fire it. Launch-time `--model` is not a documented source. `PostModelSwitch` can observe but not block. | Matches `docs/00` §5.6 honest limits; no change. |

Sources: https://code.claude.com/docs/en/hooks, …/hooks-guide, …/permissions, …/permission-modes, …/settings-reference, …/model-config, …/security.

## Deviations from `docs/` (BUILD-SPEC wins; further deviations below)

| Date | Area | Decision | Reason |
|---|---|---|---|
| 2026-10-12 | Layout | Frozen tool sources live in `dist/<name>/.gatekit/` (`gatekit/` package, `tddtool/` package, `levels/0/`), pytest plugin in `.tdd-tools/`. `gate`, `tdd`, `preflight` are thin launchers. | One place for the guard to block; `gate reset` needs level-0 persona without the vault. |
| 2026-10-12 | Gate kit | Added `gate brief` (no TTY) that prints the current level brief; `BRIEF.md` is also written to the repo root on unlock. | Groups need to re-read the brief without opening `.workshop/`. |
| 2026-10-12 | TDD L1 | `./tdd new-attempt` replaces the doc's `git checkout level1-start`. | Keeps the group's L0 work on a branch and restores the stub without a tag per level (BUILD-SPEC §5.3). |
| 2026-10-12 | TDD L3 | The L2→3 unlock runs `new-attempt` automatically and says so. | BUILD-SPEC §5.6. |
| 2026-10-12 | TDD L2 gate | "`src/` and `tests/` unchanged during L2" is checked by a content hash recorded at L2 entry, not by git. | Robust to uncommitted work and to `new-attempt` commits. |
| 2026-10-12 | TDD phases | At Levels 3–4 in phase `none`, Claude may edit only `LOG.md`. At Level 5 phases are optional and `src/**`, `tests/**`, `LOG.md` are editable. | The doc's phase table has no `none` row; BUILD-SPEC §5.7 gives Level 5 the collaborator persona. |
| 2026-10-12 | Verified gates | Level secrets and the scoring-pack secret live in `.vault/keys.bin`, obfuscated with a build-time pepper in `.gatekit/tddtool/_pepper.py`. | BUILD-SPEC §4.4 calls these a soft barrier; documented as obfuscation in `gatekit/README.md`. |
| 2026-10-12 | Hooks | Added `SessionStart` hook `model_check.py` (best-effort warning on launch-time model override). | Fact 8 above. |
| 2026-10-12 | Environment | `.venv` built from `/opt/homebrew/bin/python3.13` (3.13.2); pins `numpy==2.3.2`, `matplotlib==3.10.5`, `pytest==9.1.1`. | Versions already present on the build machine; user's choice. |
| 2026-10-12 | Master passphrase | Read from `~/.config/workshop/master-passphrase` (mode 600). | User's choice; outside every repo. |

## Adversarial review (2026-10-12, Opus subagent against a fresh dist/tdd-ladder)

| Finding | Outcome |
|---|---|
| Any file under `tests/` runs with repo permissions via `./tdd test`/pytest/`python3`, so Claude can read the pepper and `keys.bin`, decrypt every pack and drive `./gate` through `os.openpty`. | Structural; documented as the primary honest limit in `gatekit/README.md` §11. Verified-gate packs and the TTY rule are soft against a code-running Claude; crypto gates stay hard. |
| APFS is case-insensitive: `.VAULT/keys.bin` readable, `.CLAUDE/hooks/guard.py` writable. | Fixed: all path checks lower-case. |
| `git show HEAD`, `git cat-file`, `git archive`, `git log -p`, `git grep` print the committed vault and pepper. | Fixed: guard denies git object readers; `git status/diff/log --stat/add/commit` still allowed. |
| Quote and variable splitting (`./g''ate unlock`, `T=red; ./tdd $T`), dot-globs (`.v*ult`), `-mpip`, `uvx`, `curl \| python3`. | Fixed: commands normalised (quotes and backslashes stripped) before matching; new patterns. |
| `gatekit/ptyhelper.py` shipped in dist is a ready-made TTY faker. | Fixed: not copied by `tools/build.py`. |
| `require_tty()` cannot tell a pty from a terminal. | Mitigated: also refuses when `CLAUDECODE` is set (Claude Code's Bash sets it); guard blocks `env -i/-u` and `unset CLAUDE*`. `ptyhelper` strips `CLAUDE*` from the test environment. |
| `model_lock.py` substring match accepted `claude-opus-haiku`; list input tracebacked. | Fixed: whole-token match, other family names deny, non-object input denies. |
| `scoring.pack` contained `__pycache__`. | Fixed in `deterministic_tar`. |
| Deny rules lacked `Read(./.git/**)`, `Edit(**/.claude/**)`. | Added. |
| Unverified against Claude Code docs: case sensitivity of deny-rule paths; whether Grep searches hidden directories and whether Read-deny filtering applies to its results. | Open; the guard does not rely on either. |

## External review panel, round 1 (2026-10-12; Codex gpt-6.1-sol high, Claude Opus 5.5 high, read-only via orchestrator)

| Finding (reviewer) | Outcome |
|---|---|
| No way out of an open cycle whose test passes at once or whose oracle is wrong (both) | Added human-only `./tdd abort [reason]`: closes the cycle without credit, phase → none. Briefs 3 and 4 explain it. Logged as a deviation from docs/04 §6 (which has no abort). |
| Guard false positives: `2>&1`, `python -m pytest`, commit-message text, `expect` in messages, `/tdd-ladder` paths, python as a write verb (Claude) | Fixed: redirections and `git commit -m` text stripped before matching; `python -m pytest` is a read; `python -c` is a write only when it opens files for writing; running a `.py` script file still counts as a write; `script`/`expect` anchored to command position; path mentions need a delimiter after the name. Regression tests added. |
| `tools/build.py --out` could wipe the sources (Codex) | Fixed: refuses outputs that contain the sources or are not an earlier build. |
| Symlink inside `tests/` escapes the frozen-path checks (Codex) | Fixed: edits must satisfy the rules on both the lexical and the resolved path; `ln` is always denied in Bash. |
| `git diff --no-index` reads the vault (Codex) | Fixed: denied. |
| M06's spec label `S3/S4` could never be answered (both) | Fixed: validator accepts either part. |
| Skipped, missing or timed-out mutant runs counted as kills (Codex) | Fixed: a kill needs a failure or error of a reference-passing test; incomplete runs are listed. |
| GREEN did not check `src/` unchanged since RED, nor that baseline tests still exist (Codex) | Fixed: `src/` content hash recorded at RED; baseline tests must be present and passing at GREEN. |
| Setup-phase skips (`@pytest.mark.skip`) logged as passed; pytest exit code ignored (both) | Fixed in `tddlog.py` and `_all_pass`. |
| Affine-equivariance menu row wrong (σ must scale too; it cannot kill M07); uniform-σ needs σ ≠ 1 to kill M05 (both) | Brief 4 and hint 2 corrected. Deviation from docs/04 §7 Level 4 table, for physics correctness. |
| Scoring workspace had no `data/` (Claude) | Fixed: `data/` copied; self-test adds a data-loading test. |
| Acceptance demanded Python `int` and `int64` where the spec says "integer" (Claude) | Relaxed to `np.integer`; mutants still all killed; L1 sample now 8/12. |
| SPEC.md counter missed `Decision 1:`, table and bullet formats (Claude) | Regex widened. |
| "Red never observed" was recorded but never shown (Claude) | `./tdd status` at Levels 0–1 prints runs and whether any run had a failing test. |
| Level 5 mutant copies had no allowed location (Claude) | `mutants/` editable at Level 5 and gitignored; brief says so. |
| Post-unlock exception would traceback after state advanced (Claude) | Caught with a clear message. |
| Suite runtime measured under contention (Claude) | Reference run now executes alone before the parallel batch. |
| `allow-model <full-id>` was stored but never matched (Codex) | Exact full-ID match added. |
| Collection errors mis-reported in the score (Claude) | Detected from testcases without a classname. |
| M16 labelled `S1` in `mutants.json` (Claude, open question) | Intended: the baseline mutant needs some spec label for the survivor report; S1 is its nearest decision. |
| Reference rejects infinite edges though S9 does not say so (Codex) | Left as is: S7's "non-finite" rule is read as covering edges; acceptance does not test it. |
| Level 4 can be completed while staying in RED (Claude) | Accepted: the gate needs only the score; the brief recommends cycles. |

## External review panel, round 2 (2026-10-12; same reviewers, focused on the round-1 diff)

| Finding | Outcome |
|---|---|
| `_all_pass` checked the pytest exit code before the failure list, masking every "N tests fail" message (Claude) | Fixed: exit code checked last. Self-test now runs `./tdd red` against a failing suite and checks the test is named. |
| After `./tdd abort` from GREEN the wrong test stayed in a frozen `tests/`, so RED could not restart (both) | Fixed: abort asks "Keep the test(s)?"; answering no restores `tests/` to the RED commit and commits. Brief 3 and 4 updated. Self-test covers both answers. |
| Commit messages naming `.tdd`/`.vault` tripped the secret-path check (Codex) | Fixed: commit-message stripping runs first; `-am`-style flags handled. |
| Absolute paths in Bash writes bypassed the frozen-path check; `/bin/ln` and leading spaces bypassed the `ln` rule (both) | Fixed; regression tests added. |
| `strip_noise` swallowed `python -m "pip"` (Claude) | Fixed: only `git commit` messages are stripped. |
| Affine row still credited the wrong mutants; needs abs(a) != 1 (Claude) | Brief 4 and hint 2 corrected: affine kills weighting and square-root errors only. |
| "src changed during RED" advice could not undo a committed change (Claude) | Message names the RED commit. |
| L1 "red observed" could count Level 0 runs (Claude) | Window starts at max(level start, last new-attempt). |
| Uniform-σ row said "exactly" (Claude, risk) | Reworded to "to within floating-point rounding". |
| Reference stricter than S9 on infinite edges (Codex, residual) | Accepted as is; not exercised by acceptance or mutants. |

## External review panel, round 3 (2026-10-12; verification of round 2)

All round-2 items confirmed resolved by both reviewers. New: a command substitution (`$(…)` or backticks) inside a stripped commit message escaped the secret-path check (Codex serious, Claude moderate). Fixed: only literal messages (no `$` or backtick) are stripped, per `git commit` segment, so multiple `-m` flags also work; absolute repo paths are reduced to relative before matching. Minor: abort's restore commit now has a `tests` pathspec; the "tests kept" message says RED needs a passing suite. Accepted: `/Volumes/data/...`-style clone paths can trip the frozen-path check on Bash writes (clear message, path tools unaffected).

## External review panel, round 4 (2026-10-12; verification of round 3)

Both reviewers found the same residual: message text that itself looks like `-m '…'` (nested inside a substitution) was still stripped. Fixed in `89cec79`: when a command contains `$(`, a backtick, `${` or `<(` anywhere, nothing is stripped and the raw command is inspected. Accepted false positive: a literal commit message containing `;` and a secret-looking token is denied (fails safe). Reviewer summary across four rounds: Codex gpt-6.1-sol (read-only sandbox, high effort) and Claude Opus 5.5 (plan mode, high effort), both launched through the orchestrator; every serious finding was independently verified in the code before fixing.

## Facilitator feedback round (2026-10-12; trial in a fresh clone; Claude Code 2.1.296)

### Model: "doesn't start with Haiku and I can still switch models"

Verified against <https://code.claude.com/docs/en/model-config> and …/hooks, and by running `claude -p` in a scratch directory whose only config is `{"model":"haiku"}`.

| Fact | Evidence |
|---|---|
| Precedence is `/model` > `--model` > `ANTHROPIC_MODEL` > `model` setting > `ANTHROPIC_DEFAULT_MODEL`; project and managed `model` settings apply again at every launch. | model-config page. |
| "The `model` setting is an initial selection, not enforcement"; only `availableModels` in managed settings restricts `/model`, which is why the workshop uses a `PreModelSwitch` hook. | model-config page. |
| The active model is shown by the status line and `/status`; the docs say nothing about a model reporting its own name correctly. | model-config page. |
| With project `model: haiku` (and a user setting of `fable`), `claude -p --output-format json` reported `modelUsage` key `claude-haiku-5-5` only, and the model answered "I'm Claude Haiku 5.5". So the project setting does win at launch. | Run 2026-10-12. |
| `model_lock.py` allows `haiku` and `claude-haiku-5-5` and denies `sonnet`, `claude-sonnet-5-5`, `default`, `opus` and `fable` (exit 0 with the JSON deny). `/model` to Haiku is allowed by design because Haiku is in `allowed_models`. | Hook run directly with `to_model` payloads. |
| `SessionStart` may carry `model` but "can be omitted"; `PreModelSwitch` fires only for switches, so a launch-time `--model` or `ANTHROPIC_MODEL` override is not blocked, only possibly warned about by `model_check.py`. | hooks page. |

Conclusion: the banner said Haiku, so Haiku was running; the "I'm Sonnet" answer was a self-identification error (a Haiku-class model misnaming itself), not an override. Not reproduced in the scratch run, and not provable after the fact for the facilitator's session. The facilitator did not try Sonnet, so "I can still switch" was the allowed switch to Haiku. Hardening, all in the exercise (nothing in `gatekit/`): `CLAUDE.workshop.md` tells Claude it cannot be sure which model it is and to point at `/status`; the walkthrough says to trust `/status`, adds a setup check that `/model` to Sonnet is refused, and explains the launch-time limit.

### Deviations from BUILD-SPEC

| Date | Area | Decision | Reason |
|---|---|---|---|
| 2026-10-12 | TDD L0 to L1 | The L0 unlock runs `new-attempt` itself (`post_unlock: tdd.start_from_stub`, generalised to name the new level); `./tdd new-attempt` stays for manual restarts. The L1 gate condition `new_attempt_and_score_at_level` is unchanged: a score after the latest fresh attempt. Deviation from BUILD-SPEC §5.6 row 1 to 2 ("`new-attempt` done at L1"), which now holds automatically. | A group that forgot the manual step had no clear way to recover; same pattern as L2 to L3. |
| 2026-10-12 | TDD L2 gate | The "src/tests changed" refusal names changed files (restore with `git checkout`) and new files (delete); the level-2 snapshot now also stores a per-file hash map. The "missing SPEC.md" and "too few decisions" refusals say how to fix. | Untracked files cannot be undone by `git checkout`; groups needed the exact file. |
| 2026-10-12 | TDD L3 gate | The L3 to L4 unlock refuses while a cycle is open and says to run `./tdd done` or `./tdd abort`. The "< 9 killed" refusal points at `./tdd score`. | A cycle left open carried into Level 4 and blocked `./tdd red` there. |
| 2026-10-12 | TDD red entry | `./tdd red` refusals for a failing, skipped or non-collecting suite append how to restore a green state in the gate terminal. | With no cycle open Claude cannot edit `src/` or `tests/`, so only a human git restore recovers. |
| 2026-10-12 | `make plot` | Also writes `results/hz_binned_L<level>.png`, level from `.workshop/state.json` (0 if missing or unreadable; a failed copy only prints a note). | Facilitator request: compare plots across levels. `results/` is gitignored. |
| 2026-10-12 | Personas, CLAUDE.workshop.md | Added an "Explain as you go" rule to every persona (all under 180 words) and to `CLAUDE.workshop.md`. For `literal` it allows explaining what it is doing but still bans process advice and pointing out its own assumptions, so the Level 0 "silent decisions" lesson survives. | Facilitator request: people who missed the introduction need to catch up at each level. |
| 2026-10-12 | Briefs, README, score output | Each level brief opens with "Where we are" and defines terms on first use; the Level 0 README section adds a short scorecard glossary; `./tdd score` adds one-line glosses under MUTANTS KILLED and FALSE ALARMS (the parsed lines are unchanged). | Same request. |

## Speed Run (Exercise B) build (2026-10-12)

Design brainstormed with Codex gpt-6.1-sol (high, read-only via orchestrator) against `exercises/speed-run/PLAN.md` and a measurement probe on the build machine (M1 Max, Python 3.13, numpy 2.3, Apple clang 21). The PLAN is the frozen contract; its section 11 lists the deviations from `docs/02`, repeated here with the reasons.

| Date | Area | Decision | Reason |
|---|---|---|---|
| 2026-10-12 | Levels | Four levels (measure; vectorise; reduce the work; race), not the doc's five: baseline and profile merged. Minutes 7 + 10 + 14 + 11, with 1 to start and 2 contingency. | Each gate costs 2–3 minutes of human time; five gates leave no recovery time in 45 minutes. |
| 2026-10-12 | Bins | r_max = 10 Mpc/h, 15 log bins from 0.5 (16 edges, stored as float64 literals in `paircount/__init__.py`). | Measured: numpy cell list at 200k takes 11.5 s at r_max 10 and 77 s at r_max 20 (5.3 × 10⁸ pairs inside r_max). A 60 s gate and a race need the smaller budget. |
| 2026-10-12 | Toleranced division | A bin passes when `abs(count - golden) <= sigma_fraction * sqrt(golden)`, `0 < sigma_fraction <= 0.2`, with a written justification (≥ 80 characters) in `race.toml`. | The doc's `rtol <= 1e-6` cannot pass a one-count shift unless the bin holds ≥ 10⁶ pairs; integer counts need an absolute criterion, and the Poisson error is the physical one. Verified: every wrong-semantics variant passes at 0.1 on every bin of every catalogue. |
| 2026-10-12 | Level 2 question | The per-bin tolerance question (golden [100, 1000000], yours [101, 1000010], sigma 0.05 → only the second bin passes), not the measured scaling exponent. | A cell list at fixed box and r_max is still ~N² (measured 1.89 between 50k and 200k); "accept 0.9–1.5" would reject a correct method. |
| 2026-10-12 | Level 1 | Exact division only; limit 10 s, not 30 s. | Divisions are introduced with the diff table at Level 2. The untouched pure-Python entry does 20k in 22–32 s, so a 30 s limit was passable with no work; chunked numpy takes ~1–3 s. |
| 2026-10-12 | Memory wall | Harness-enforced: a level passes only under 1.5 GB peak RSS; a worker is killed above `RACE_RSS_CAP_GB` (2.5) or `RACE_TIMEOUT_S` (180). The Level 1 hint says chunks of a few hundred rows. | A 32 GB laptop does not swap at 20k (full N×N measured 10 GB); 2000-row chunks peak at 3.3 GB and would fail the ceiling. |
| 2026-10-12 | Golden counts | Tool-private in `.gatekit/racetool/golden.json`; partial runs (first n rows, n ≤ 4000) are checked against the reference on the same rows; other partial runs record `pass: null`. | A readable `data/golden.json` could be returned verbatim. |
| 2026-10-12 | Submit | `./race submit` runs the entry and the calibration counter (numpy cell list, ~4 s at 200k, cached per machine) on a hidden 200k catalogue from `scoring.pack`; score = calibration seconds / entry seconds; a failing entry scores 0 with the same diff table. Clean-tree check covers `paircount/**` and `race.toml` only; untracked `.so`/`.dylib`/`.o` are ignored (and gitignored by the template). [superseded by review round 1: re-timed every submit; hidden failures print a summary only] | Hard-coded answers score 0; compiled objects must not block a submission. |
| 2026-10-12 | Bench evidence | Records in `.workshop/race/bench.jsonl` are HMAC-signed with the build pepper and carry `source_hash` (paircount tree), `toml_hash`, `level`, catalogue and an `error` field (kill or crash reason); gates reject stale or unsigned evidence. | Git HEAD does not identify uncommitted code; a hand-written log must not pass a gate (soft, like all pepper-based checks). |
| 2026-10-12 | Straddlers | Three disjoint kinds per catalogue, verified from the stored float64 rows: exact-edge (`sqrt(s) == e`, including one pair at r_max), sum-of-squares (`s < e*e` but `sqrt(s) == e`; impossible at edges 0, 6, 8, 10, 11, so those are skipped), FMA (clang default contraction vs `-ffp-contract=off`). Edges are planted only where both neighbouring bins hold ≥ 400 base pairs (at 2k this skips edges 0–2). No natural straddlers occur. | Every variant (sum of squares, `<=` convention, `np.histogram`, FMA) must move ≥ 1 bin and pass toleranced 0.1; the 2k catalogue's inner bins are too small to absorb a moved pair otherwise. |
| 2026-10-12 | Goldens | Reference at 2k and 20k; numpy cell list (bit-identical to the reference at 2k and 20k) at 200k and hidden, cross-checked by an independent C brute-force counter compiled with `-ffp-contract=off`. | Independent evidence for the large catalogues. |
| 2026-10-12 | Cuts | No ξ(r), randoms, 50k catalogue, "per line changed" prize or multiprocessing (single-process measurement). | Session time; the harness measures one process. |
| 2026-10-12 | Gatekit | `human_only` manifest field drives the guard's Bash rule and the rendered `settings.json` deny list (fallback: the tdd list); `race` added to `FROZEN_FILES`; `model_check.py` always prints the session model when supplied; the template `.gitignore` ignores `*.so`, `*.dylib`, `*.o`. | Second exercise tool. |
| 2026-10-12 | Environment | `requirements.txt` pins numpy 2.3.2, scipy 1.17.0, matplotlib 3.10.5, pytest 9.1.1. | scipy 1.18 needs Python ≥ 3.12; 1.17.0 keeps the 3.11 floor and supports numpy < 2.7. |
| 2026-10-12 | Fallback | `./race install-solution <level>` (TTY + master passphrase) copies the hidden solution for that level into `paircount/`. | Master skip opens the next level but installs no code. |
| 2026-10-12 | Personas | Every persona carries the "Explain as you go" paragraph (two or three sentences before each experiment or change, one or two after a run, terms defined on first use); briefs open with "Where we are". | Facilitator feedback from the TDD trial: Claude was too terse and groups lacked context. |
| 2026-10-12 | Personas and briefs length | Personas run to ~190–200 words and the Level 2 and 3 briefs to ~550–600 words, over BUILD-SPEC's ~150 and PLAN's ~450, because the 'Explain as you go' paragraph and the never-list are kept verbatim. | Facilitator feedback asked for more context. |

## External review panel, round 1 for the Speed Run and the TDD feedback changes (2026-10-12; Codex gpt-6.1-sol high, Claude Opus 5.5 high, read-only via orchestrator, staggered parallel launch)

Every finding was verified in the code by the integrator before a fix was assigned.

| Finding (reviewer) | Outcome |
|---|---|
| `make bench CAT='… --golden my.json'` forwards arbitrary flags, so a zero-returning entry plus a zero golden file is recorded under the public catalogue name and passes the Level 1 and 2 gates (Codex, serious) | Fixed: runs using any tool-only option (`--golden`, `--label`, `--impl-file`, `--json-out`, or a catalogue path) are never recorded; self-test covers it. |
| Only the `count_pairs` call was timed, in one process, so import-time precompute or memoisation across repeats beats the limits and inflates scores (Claude, moderate) | Fixed: each repeat runs in a fresh worker and the timed region is the entry's import plus the call ("time (import + count)"); the catalogue load stays outside. The C entry's first-ever compile lands once. |
| Fingerprints were taken after the run, so `race.toml` or source changed mid-run got the new hash (Codex, moderate) | Fixed: hashes taken before and after; a change marks the record `error` and `pass: null`, which the gates reject as stale. `source_hash` excludes `*.so`, `*.dylib`, `*.o` (the `.c` is hashed). |
| `RACE_RSS_CAP_GB` and `RACE_TIMEOUT_S` could be raised from the environment (Claude, moderate) | Fixed: clamped to at most 2.5 GB and 180 s. |
| Calibration time cached forever from one run, so a busy machine at the first submit inflates every later score (Claude, moderate) | Fixed: the calibration is re-timed on every submit (~20 s wall). |
| A failed hidden submission printed the per-bin table with the hidden golden counts, so a zero entry reveals the answer vector and a constant entry then passes (Codex, risk; design conflict with PLAN §4.5) | Fixed: hidden failures print only the failing-bin count and the largest difference, and point at `make check N=200000` for the public per-bin table. PLAN §4.5 amended. |
| TDD Level 2 refusal advised `git checkout -- <files>`, but the entry snapshot is of the working tree and Level 1 work is normally uncommitted, so the advice restores the stub and loses work (both, moderate) | Fixed: the L1→L2 post-unlock makes a "Level 2 start" commit and the refusal quotes `git checkout <hash> -- <files>`. Self-test extended. |
| Level 2 brief presented `sqrt(golden)` as the bin's real scatter; clustered pair counts scatter more and are correlated (Codex, moderate) | Fixed: described as a nominal Poisson yardstick adopted for the exercise; real scatter is larger, so the criterion is conservative. |
| Scores printed with one decimal show 0.0 for a slow pass, like a failure (Claude, risk) | Fixed: two decimals, never 0.00 for a pass. |
| `gatekit/README.md` §11 overstated the Speed Run's crypto gates (fixed check output, so the human answer is the only secret) (Claude, minor) | Fixed: stated in §11 and in the walkthrough. |
| `model_check.py` line contradicted the "which model am I" rule and goes stale after a power-up (Claude, minor) | Fixed: "this session started on X; /status shows the current model". |
| TDD Level 2 brief's "Where we are" named three client decisions before the interview (Claude, minor) | Fixed: examples dropped. |
| Walkthrough quoted the old 11.5 s cell-list time; README overstated what small-N runs check; no Level 1 hint for the `np.histogram` last-edge failure; direct `bench/harness.py` calls get a confusing frozen-path refusal; cKDTree compares squared distances so it may never be exact; test at 20k before 200k (Claude, minor) | Fixed in the briefs, hints, README, `CLAUDE.workshop.md` and walkthrough. |
| Intel Macs: no FMA contraction without `-mfma`, so the FMA trap does not fire (Claude, risk) | Accepted: Apple silicon assumed; noted in the walkthrough. |
| Literal persona: "Explain as you go" may pull Haiku into narrating design choices, weakening the TDD Level 0 "silent decisions" lesson (Claude, risk) | Accepted: the persona bans pointing out its own assumptions; to be watched in calibration. |
| Hint tier 3 opens at 10 minutes on a 7-minute level (Codex, risk) | Accepted: tiers are a gatekit constant; Level 0 rarely needs tier 3. |
| Code the harness runs can read the golden counts, pepper and keys (both) | Accepted: the documented structural limit (`gatekit/README.md` §11). |

## External review panel, round 2 (2026-10-12; verification of round 1, same reviewers, continued sessions)

Both reviewers confirmed every round-1 item resolved as implemented and found no serious new defects. New: `./race log` and the status line reported "0 bin(s) differ" for a failed hidden submission, because the verdict counted the per-bin `diff` that the fix now withholds (both; fixed: uses `fail_bins`). Codex: the participant `CLAUDE.md` demanded a per-bin table whenever counts differ, which a hidden failure cannot give (fixed: qualified to public runs). Claude, risks: a C entry that recompiles on every import now pays for it in every timed run, and the "no precomputation at import" wording could be read as forbidding compile-on-first-import (fixed: `CLAUDE.workshop.md` and the Level 3 brief say compile once and reuse the cached library; recompiling is timed); a `-g` build's `.dSYM` folder tripped the mid-run change check once (fixed: excluded from `source_hash`); the import overhead now inside small-N reference timings pulls the fitted exponent slightly below 2 (accepted; the self-test band holds).

## Facilitator and leader documentation (2026-10-13)

| Date | Area | Decision | Reason |
|---|---|---|---|
| 2026-10-13 | Roles and docs | Each exercise's `FACILITATOR-WALKTHROUGH.md` is the operating guide for both the facilitator (sections 1–2: build, rehearse, bundle) and the group leaders (section 3 onwards: laptop set-up from the bundle, running the session, levels, troubleshooting, reset). `README.md` "Run the workshop" is the facilitator's ordered checklist and links to it; `docs/00` keeps the lecture, roles, briefing, run-sheet and trial. | Leaders had no self-contained set-up path: the bundle line was only a comment, and trust, the `/hooks` checks and git identity appeared only in the facilitator's own set-up. |
| 2026-10-13 | Leader guide | The walkthroughs absorb the coaching material of `docs/02` §7 and `docs/04` §10 (opening script, questions by level, managing the group, time checkpoints), renumbered to the levels as built. Those design sections are marked superseded. | `docs/02` §7 used the five-level design; the built Speed Run has four. |
| 2026-10-13 | Master passphrase | The facilitator holds it and types it in the group's gate terminal for power-ups, skips and `./race install-solution`; a leader running without the facilitator present is told it (or given a repo built from a different passphrase file). Leaders' laptops never hold the passphrase file. | No document said who holds it; one passphrase opens every repo built from the same file. |
| 2026-10-13 | Distribution | Bundles are made from a freshly built or reset repo and checked (`git status`, `git log`, `git branch`) first. | `git bundle create --all` carries rehearsal commits and `attempt-*` branches. Verified 2026-10-13: both bundles clone with the `start` tag and pass `./preflight`, which initialises level-0 state. |
| 2026-10-13 | Reset | The walkthroughs' reset (`./gate reset`, then `git reset --hard start && git clean -fdx -e .venv -e .workshop`) is canonical; `docs/00` points to it. | The short form `git reset --hard start && ./gate reset` leaves untracked work (SPEC.md, new tests, results) in place. |
| 2026-10-13 | `docs/00` §5 | Condensed to the design intent and lecture points, with the as-built details left to `gatekit/README.md`. The section numbers are unchanged. | The repo layout, settings skeleton and key derivation no longer matched the build. |
| 2026-10-13 | Session timing | The `docs/00` run-sheet gives 45 minutes from Go to Stop (Stop at T = 63, show-and-tell 65–70), matching its own "At a Glance" table and the built exercises' time checkpoints; the session is about 70 minutes, and the README says so. A hard 60 shortens the lecture and show-and-tell, not the hands-on. | The run-sheet allowed 40 minutes, so Speed Run groups lost their race and TDD groups their Level 4. |

## Explorer (Exercise E) build (2026-10-13/14)

### Claude Code facts (verified 2026-10-13 against https://code.claude.com/docs, installed Claude Code 2.1.296)

| # | Item | Finding | Design consequence |
|---|---|---|---|
| 1 | Plan mode as the starting mode | `permissions.defaultMode` in project settings accepts `plan`. | The session starts in plan mode; Level 0 is planning only. |
| 2 | `/code-review` | A bundled skill that runs as a background subagent with a fresh context and writes its output to the conversation only. | Not used for the gate: its output cannot be captured into `REVIEW.md` by the group. It stays in the playbook for home use. |
| 3 | Subagents | They start fresh: their own prompt, the task and `CLAUDE.md`, not the conversation. | The shipped `reviewer` agent is a genuine fresh-context review. |
| 4 | `.claude/agents/*.md` | Frontmatter keys `name`, `description`, `tools`, `model` (an alias such as `sonnet`) and `permissionMode`. | `reviewer.md` sets `tools: Read, Grep, Glob, Bash` and `model: sonnet`: it has no Edit or Write tool and is told never to modify files (Bash could). |
| 5 | Stop hook | Exit code 2 blocks the stop; exit 1 does not. | Noted for the take-home notes; no Stop hook is shipped. |
| 6 | `UserPromptSubmit` | Stdout becomes context for the turn. | Unchanged from the other exercises: the level brief and persona are injected this way. |
| 7 | `Esc Esc` and `/rewind` | Restore the code and/or the conversation to an earlier point. | The playbook's "Recover" step names them. |
| 8 | Pausing between plan steps | There is no native "pause between plan steps". | The briefs ask for one step at a time; the Driver's `Esc` is the pause. |
| 9 | Model names | Aliases `haiku`, `sonnet`, `opus`; full ids of the form `claude-haiku-5-5`. | `models.default` and `allowed` use the alias `sonnet`. |

Rendering check (2026-10-14): the page built by the reference solution was opened in Chrome for both datasets. The 2D to 3D switch works, the colour bar is titled "log10 P0 (s)", hovering shows every column with units, and there were no console errors. The dimuon J/ψ and Z bands are visible with log axes.

### Deviations from `docs/05` and `exercises/explorer/PLAN.md`

| Date | Area | Decision | Reason |
|---|---|---|---|
| 2026-10-13 | Check paths | The manifest names the checks `.gatekit/exploretool/checks/levelN.py`, not `checks/levelN.py`. | The gate CLI resolves check paths relative to the repo root. |
| 2026-10-13 | Gatekit: last-level crypto gate | `tools/build.py` now sets `verify` for a crypto gate on the last level and fails the build if its token is missing; new gatekit unit test. | An exercise ending on a crypto gate could never complete: no later pack held the verify token. |
| 2026-10-13 | Gatekit: build wipe | The `tools/build.py` wipe tolerates a Finder `.DS_Store` and always restores a stashed `.venv`; new unit test. | A rebuild died on a `.DS_Store` with the venv stranded in the stash. |
| 2026-10-13 | `PLAN.md` template | The leader's note about the `Dataset:` line moved into an HTML comment above it. | A `<` on the `Dataset:` line would reach the shell through `make`. |
| 2026-10-13 | `make list` at Level 0 | The README and hint 1 ask Claude for the missing-value counts; `make list` is introduced as working from Level 1. | The tool does not exist at Level 0, so `make list` cannot work there. |
| 2026-10-13 | Level 1 keywords | Extra accepted forms: "the sun", "our sun", "the solar system", "the earth", "the solar neighbourhood" (both spellings), "the j/psi", "j/psi meson", "jpsi meson". | Keyword matching keeps articles and words; only case, spaces and punctuation are removed. |
| 2026-10-13 | HTML check | `scattergl` and `scatter3d` are searched for outside the embedded plotly.js. | plotly.js itself contains both strings, so a search of the whole file would always pass. |
| 2026-10-13 | Check order | The commit count is checked before the clean tree. | A group that has not committed enough would otherwise be told only that the tree is dirty; the commit sentence names the real fix. |
| 2026-10-13 | `on_reset` | `exploretool.on_reset` removes `out/`. | A stale page from the last group must not survive a reset. |
| 2026-10-13 | Template `.gitignore` | `out/` and `.coverage` added to the gatekit template `.gitignore` (harmless for the other exercises). | Generated pages and coverage files would otherwise show as untracked and dirty the tree. |
| 2026-10-13 | Persona length | Personas run 210–235 words, over PLAN's 150–200. | The "Explain as you go" paragraph and the never-list are kept in full, as in the Speed Run. |
| 2026-10-13 | Last-level note | The pre-reflection note after the final gate also mentions the reviewer agent. | The agent is part of what the group takes home with `PLAYBOOK.md`. |
| 2026-10-13 | Data | Pulsars: 4,503 rows (catalogue v2.9.0), not about 3,700. Pulsars without a distance (74) have `XX`, `YY`, `ZZ` blanked. Dimuons: trimmed to the first 60,000 rows. | The real catalogue size; psrcat places pulsars with no distance at the Sun, which would plant false points where the Level 1 question looks; 60,000 rows keep `dimuons.csv` at 7.9 MB (under 8 MB) and still exercise sampling. |
| 2026-10-13 | Reference solution | `build_page(payload, blob)` takes the serialised JSON. | The NaN variant (`solution_nan`) then overlays a single file. |
| 2026-10-13 | Dependencies | `plotly` 7.1.0 and `pytest-cov` 7.1.0 added to the venv beside numpy 2.3.2 and pytest 9.1.1 (installed 2026-10-13, approved by the facilitator). | The page needs plotly's bundled plotly.js; `make coverage` needs pytest-cov. |

## External review panel, round 1 for Explorer (2026-10-14; Codex gpt-6.1-sol high, Claude Opus 5.5 high, read-only via orchestrator, staggered parallel launch)

Every finding was verified in the code by the integrator before a fix was assigned. The Level 1 headless plan-mode probe and the Claude Code docs could not settle whether plan mode's own plan-file write passes through the `PreToolUse` guard, so the guard now allows it either way.

| Finding (reviewer) | Outcome |
|---|---|
| Level 3 required at least one FIX, so an honest short or clean review could not complete the exercise and invited a manufactured fix (Codex, serious) | Fixed: the gate needs three triaged findings with reasons and no FIX; the reviewer agent is asked for three to eight findings; briefs, walkthrough, docs/05 (§12 decision 14), PLAN.md and the self-test updated. |
| `tools/build.py` now enables a last-level crypto gate, but `gate unlock` on the last level derives the answer's slot secret and never checks it, so a graded final question would accept any answer (Codex, serious; Explorer's final gate has no question) | Fixed: the build refuses a last-level crypto gate with graded questions; unit test added; `gatekit/README.md` §3 says so. |
| Plan mode writes its plan file under `~/.claude/plans/`; the guard denies every Edit/Write outside the repo, so the session's first action might be refused (Claude, serious if confirmed; docs do not say whether that write goes through the Write hook) | Fixed defensively: `guard.py` allows edits under `~/.claude/plans` and `$CLAUDE_CONFIG_DIR/plans` only; unit test added. To confirm in the live calibration. |
| The README never said the controls must be static HTML with the options written by Python, while the check parses the file without running JavaScript (Claude, moderate) | Fixed: one sentence in the README; the three refusal sentences say "the check does not run JavaScript". |
| A REVIEW.md decision cell of "FIXED" or "FIX (done)" stopped counting at the last gate (Claude, moderate) | Fixed: the decision is matched by prefix. |
| The Level 1 question can be answered from the column file or from physics knowledge, but the walkthrough said it could only be answered in the browser (Claude, moderate) | Fixed: reworded as "prompts a look"; added to the honest limits in the walkthrough and docs/05 §12. |
| Hint 3 unlocked at 10 minutes on 8-minute levels, and the checkpoints told leaders to take it at 8 (both, moderate) | Fixed: tiers at 0, 3 and 6 minutes on Levels 0, 2 and 3 (0, 5, 10 on Level 1); checkpoints say "give hint 3's advice". |
| A FIX label is not evidence that anything was fixed; the self-test completes Level 3 with only REVIEW.md committed (Codex, moderate) | Accepted and documented as a human check (walkthrough honest limits, docs/05 §12). The design's gates check that the step happened, not that it was done well. |
| `docs/00` told facilitators to rehearse every exercise on Haiku and the calibration matrix starts on Haiku; Explorer allows only Sonnet (Codex, moderate) | Fixed: "the exercise's model"; the matrix note says runs 1–2 use Sonnet for Explorer. |
| The reference solution cannot select a numeric column called `none` (Codex, moderate) | Accepted: the sample REVIEW.md records it as ACCEPT, which is itself the lesson; any CSV is the promise, a column literally named `none` is the edge. |
| The Level 0 refusal said `tests/` opens at Level 1; it opens at Level 2 (Claude, minor) | Fixed. |
| A two-step plan passes Level 0 but Level 1 needs three commits (Claude, minor) | Fixed in wording: the refusal says "commit each working step or fix (three commits or more)". |
| Leaders' set-up omitted the Xcode Command Line Tools (`make`, `git`), and preflight's `make` failure hid the real error (Claude, minor) | Fixed: bullet added; `preflight_extra.py` reports `make`'s stderr. |
| Level 3 runs both datasets, which a tool with pulsar-only assumptions discovers in the last eight minutes (Claude, minor) | Fixed: a line in the Level 1 brief. |
| Five-person role row listed six people (Codex, minor) | Fixed: Coach and Scribe combine. |
| DECISIONS said the reviewer "cannot edit"; Bash could (both, minor) | Fixed: "has no Edit or Write tool and is told never to modify files". |
| docs/05 said `json.loads` rejects `NaN` by default; the check supplies `parse_constant` because the default accepts it (Codex, minor) | Fixed. |
| PLAN.md still quoted 3,734 rows; the self-test docstring claimed every refusal is provoked (Claude, minor) | Fixed: 4,503; "most". |
| PLAN.md numeric-column rule did not say a column needs at least one value; the palette sentence read as if it needed every column (Codex, open) | Fixed: both sentences reworded; README matches. |
| A Bash command with a write verb that also names `data/` is refused even when it only reads the data, for example `cp data/pulsars.csv /tmp/x.csv` (Claude, risk) | Accepted, existing gatekit behaviour: a troubleshooting row in the walkthrough. |
| Who types TESTS.md and REVIEW.md, given "all code goes through Claude" (Claude, open) | Fixed: the Level 2 and 3 briefs say the files are not code and may be typed directly or dictated. |
| Live Sonnet timing for Level 1 (both, risk) | Open: the calibration run in `PROGRESS.md`. Hooks do run inside subagents (docs verified 2026-10-14), so the guard covers the reviewer agent; it is read-only, so no change. |

## External review panel, round 2 for Explorer (2026-10-14; verification of round 1, same reviewers, continued sessions)

Both reviewers judged every round-1 item resolved or accepted on stated grounds, with no serious findings. Fixed from this round: the walkthrough still described the removed "no FIX" refusal (both; now says an all-ACCEPT/REJECT triage passes); a decision cell naming more than one verdict ("ACCEPT / REJECT") was counted by the prefix match (Codex; now refused as undecided); the Level 1 table in docs/05 still said "only visible in the browser" (Codex; now "prompts a look"). Accepted: three triaged findings remain mandatory (Codex, residual): the reviewer is asked for three to eight and REJECT is a valid triage, so a clean review completes. Still open: the live Sonnet calibration, and confirming the plan-mode write is accepted in a real session.

## Explorer facilitator feedback round (2026-10-14; group playthrough to Level 3)

Evidence: the playthrough transcript (main session and the `reviewer` subagent). The guard refused 29 Bash calls; replaying each through the guard's own rules showed 27 were harmless reads, scratch writes or commit messages.

| Feedback | Decision |
|---|---|
| Level 0: Claude could not commit `PLAN.md`; `./gate check` said "no commit since start" | Cause: Claude Code commits with `git commit -m "$(cat <<'EOF' … EOF)"`; the `$(` stopped message stripping, the `<…@anthropic.com>` counted as a `>` write and the message's `data/pulsars.csv` or `explorer` counted as a frozen path. Fixed in the guard (below). |
| Level 1: the plan had eight steps and took over an hour | Plans have two or three steps, each ending in something you can run and look at (user's choice: "at most three", two allowed). The README and PLAYBOOK *Plan* prompts ask for that, the template heading says it, and the Level 0 check refuses fewer than 2 or more than 3 top-level steps (sub-bullets do not count). Level 1 needs 2 commits (was 3). Every feature stays; the steps are bigger. |
| Level 1: the brief said `make list` when only step 1 existed | The brief no longer assumes a step order: "ask Claude what you can run now"; the Level 1 persona and CLAUDE.md tell Claude to name the command that works at this point. The README commands table says `make list` and `make explore` work once built. |
| Level 1 unlock: the question named both datasets; a wrong answer gave no hint | Two optional gatekit question fields. `text_from` (a `questions` function in the exercise tool) words the question for the `PLAN.md` dataset, falling back to the static prompt on any error; `wrong_hint` is printed after "Not quite" (a crypto gate prints the hints of every question asked, since it cannot tell which failed). The accept list and crypto tokens are unchanged, so either dataset's answer still opens the gate (existing honest limit). The tool is loaded lazily, inside the fallback, so a crypto gate without `text_from` never imports it. |
| Level 3: the reviewer hit many guard refusals and both agents reworded commands to get round them | Too strict, fixed in gatekit (all exercises). The guard now reads quotes, heredocs and redirects: a redirect is checked by its target only (lexically and resolved, so `../data/x` is caught); a quoted-heredoc body fed to `cat` is data, one fed to a shell is checked as a command, one fed to an interpreter is code; `python -c`/`node -e` count as writes only with a file-writing API; regex-only spellings inside quotes (`(.*?)`, `\.`, `.*word`) are not dot-globs, while bare `'.*'`/`'.v*'` still are; the pipe-into-python rule looks only outside quotes; the bare `node` and `mkdir` verbs are gone (`mkdir` cannot change a file; `node script.js` joins `python script.py`). Anything the scanner cannot read falls back to the old whole-text rules. Every refusal ends with "don't reword or split the command … tell the group … use another route"; CLAUDE.md and `reviewer.md` say the same, and the reviewer is told to read code and run only the tool and tests rather than build harnesses. Replay of the 29 refused calls: 28 now allowed at every level; the one still refused ran a personal skill under `~/.claude`, correctly. `out/**` is editable at every level for scratch files. |
| Level 3: triaging every finding is impractical; may Claude write tests? | Triage the top three to five; the rest may stay undecided (the check already counts only decided rows, at least three). Fixes come with a test that fails before and passes after (brief, persona, CLAUDE.md, PLAYBOOK, hint). |
| Briefs uneven in detail | Every level (Level 0 in the README) has the same shape: Where we are, What to do (five or six steps), If it goes differently (the forks: too many steps, a command not built yet, many findings, a failing test), What to watch for, Opening the gate. |

Accepted residual risks in the guard (cooperative Claude; participants can read everything themselves): a redirect to a `$VAR` target is not resolved; a script written to `out/` through a data heredoc and then run is not inspected (the Write tool always allowed the same); Python's `open('x...')` pattern can still over-match.

### External review panel, round 1 for the feedback round (2026-10-14; Codex gpt-6.1-sol high, Claude Fable 5.1 high, read-only via orchestrator, staggered parallel launch)

Every finding was checked against the code before acting; the guard fixes were then probed through a freshly built repo (24 reviewer examples, all correct) and the playthrough replay (28 of 29 allowed, as before).

| Finding | Decision |
|---|---|
| `sh -c '… > README.md'` and awk `print > "Makefile"` passed, because the `>` is inside quotes (Codex, serious) | Fixed: a shell run with `-c` falls back to whole-text rules; awk `print`/`printf` with `>` or `\|` outside awk strings is a write. |
| `timeout 30 python3 <<'EOF'` made an interpreter body data (Codex serious, Claude minor) | Fixed: `timeout`, `nice`, `caffeinate`, `stdbuf` are wrappers and their numeric arguments are skipped; only `cat`, `tee` and `git` make a quoted heredoc body data, any other reader's body is checked as code. |
| Node `openSync(…,'w')`/`writeSync` missed (Codex, serious) | Fixed, with Python's `'r+'` mode. |
| The parent-path check on redirect targets refused `> out/README.md` (Codex, moderate) | Fixed: path mentions are checked only for targets with a `..` component; resolved-path checks apply to all. |
| `\| python3 -m json.tool` refused with the package message (Claude, moderate) | Fixed: only a bare shell or interpreter reading stdin is refused, with its own message. |
| Quoted `s/=.*//` read as a dot-glob (Claude, moderate) | Fixed: a quoted `.*/` inside a word is masked; `ls .*/` and `find -path '.*/x'` are still refused. |
| Steps as `###` headings or an indented list counted as 0 (both, moderate) | Fixed: the shallowest list level counts, else level-3 headings; prose with no list gets "write the two or three steps as a numbered list"; the template heading says "a numbered list". |
| Sceptic rule required looking at a page before one exists (Codex, moderate) | Fixed: "once the page exists". |
| Stale docs/05, PLAN.md, sample-plan and leader-script wording (both) | Fixed. |
| Troubleshooting row lost the write-verb-plus-`data/` example (Claude, moderate) | Fixed: restored with the allowed redirect counter-example. |
| "Only someone who has looked can answer" (Codex, minor); "build step 1 first" (Claude, minor); the walkthrough's step split was not in the README (Claude, minor) | Fixed: reworded; the README now suggests the split. |
| The appeal sentence read oddly on Read/Write refusals (Claude, minor) | Fixed: "don't reword or retry it to slip past the guard". |
| `savetxt`/`to_csv`, sed `w` (Claude, minor/risk) | Accepted: not plausible for a cooperative Claude; the guard is a speed bump. |

### External review panel, round 2 for the feedback round (2026-10-14; verification of round 1, same reviewers, continued sessions)

Both confirmed the round-1 fixes. New findings, all fixed after checking them against the code: `### Step` headings with bullets under them counted the bullets, so a two-step plan read as four (Claude, moderate; headings now count first); `| bash -e` passed the narrowed pipe rule (both; flag-only shells and interpreters reading stdin are refused, `| python3 -m json.tool` and `-c '…'` still pass); the round-1 masking of a quoted `.*/` inside a word also masked `find -path './.*/settings.json'` (Codex; a preceding `/` no longer masks, so a rare `grep 'dir/.*/x'` is refused again, the safer side); a multi-line awk script escaped the awk output rule, and `print ($1 > 0)` was read as a redirect (Codex; the rule spans lines and skips parenthesised comparisons). Accepted: awk `print NR > 0` without parentheses still reads as output (Claude, risk; not a plausible command).

### External review panel, round 3 for the feedback round (2026-10-14; verification of round 2, narrow)

Neither reviewer found a serious problem; both confirmed the round-2 fixes. Three moderate false positives were fixed: the awk output rule could reach a `print` in a later pipeline stage (Claude; it now stays inside awk's single-quoted program, which also removes a quadratic worst case), `print (length($1) > 0)` was read as a redirect (Codex; one level of nested parentheses is skipped), and `sed 's/ .*//'` was read as a dot-glob (Claude; whitespace no longer blocks the quoted-regex mask). The panel was closed here: no serious findings remained, and the remaining edges are spellings a cooperative Claude does not use.

## Explorer: one dataset per audience (2026-10-14; facilitator feedback during a second playthrough)

The workshop runs twice, once for an astro audience and once for a particle audience, and each should work only with its own data. A dimuons group's Claude added pulsar runs to its plan, because the Level 3 gate ran the tool on both shipped datasets and the briefs (and a README suggestion added earlier this round) said so.

| Decision | Reason |
|---|---|
| Both datasets still ship; the `Dataset:` line chosen at Level 0 is the only one used afterwards. Level 3 now runs the tool only on the `PLAN.md` dataset; every "both datasets" or "other dataset" pointer in the README, briefs, hints and participant CLAUDE.md is gone, and CLAUDE.md tells Claude to work only with the named dataset. | Facilitator's choice over per-audience builds: one repo, and the leader locks the dataset in. |
| README rules a dataset never triggers (dimuons has no missing values or text columns) are tested at Level 2 with a small made-up CSV: one sentence in the Level 2 brief and one in its persona. | Facilitator's suggestion; fake fixtures for cases the real data lacks are normal testing practice, and it replaces the cross-dataset check without mixing physics. |
| The Level 1 keyword accept list still covers both datasets. | Harmless: the question asked is the group's own (`text_from`); recorded as an honest limit already. |

Review (Codex gpt-6.1-sol, Claude Fable 5.1, continued sessions): the Level 3 brief's gate paragraph still said "both datasets" (Codex serious, Claude moderate), as did three facilitator-doc rows and the walkthrough's step split; all fixed. The Level 1 static fallback prompt pointed at a question the brief no longer holds and its hint named both datasets (both, minor/moderate; reachable only if reading the `Dataset:` line fails after the check has validated it); now neutral, and the leader gives the question aloud. Confirmed fine: the gate and self-test change, and the Level 2 made-up-CSV suggestion.

Hints checked on the facilitator's question: the wrong-answer hints exist for both datasets (one each, chosen by the `Dataset:` line); the timed hints are shared and generic, except a Level 0 example criterion naming `P1` (pulsars only), now "choosing Z = none gives a 2D plot". The README's example `data.json` used pulsar columns; it now uses neutral ones (`E`, `theta`, `name`).

## Explorer: plans have exactly two steps (2026-10-14; facilitator solo run)

A solo speedrun of the whole exercise (dimuons, Sonnet) took 37 minutes with no reading or discussion; its plan had three steps, and the three steps always split the same way: the engine (command line, `--list`, `data.json`), the page, then a small extras step for the decisions and the initial view. The third step is not worth a stop-run-look-commit cycle. The Level 0 gate now requires exactly two top-level steps; the README, persona, hint, `CLAUDE.md`, briefs, sample plans, self-test and walkthrough all name the same split (the engine, then the page with the decisions and the initial view built in). `PLAYBOOK.md` keeps its generic "a few steps (two or three for a small job)", because it is take-home advice for any codebase. Level 1's two-commit minimum is unchanged and now equals the step count. Measured per level in that run: 5:00, 14:00, 9:17 and 8:22 against budgets of 8, 18, 8 and 8.

## Explorer: tightening for time (2026-10-14; facilitator solo run)

A solo speedrun of Explorer took 5:00, 14:00, 9:17 and 8:22 for Levels 0 to 3, against targets of 8, 18, 8 and 8 minutes. Levels 2 and 3 overran because Claude produced far more than was asked (a 29-test plan in five tables, 40 tests and 11 unasked mutation experiments; eight review findings, each with a reproduction), and each level needed one extra "now paste it into the file" round-trip. The plan stays at exactly two steps. Changes:

- **A. Capped output at Levels 2 and 3.** The Level 2 persona and walkthrough ask for a table of five to eight tests, one line each, plus two or three lines on coverage and what no test can cover, and no unasked experiments, coverage write-ups or extra tests. The reviewer agent now returns three to five findings and does not reproduce them with experiments (it runs the tool or the tests at most once and says "(not run)" otherwise). The Level 3 persona and `CLAUDE.workshop.md` match. Reason: Claude's volume, not the group's thinking, used the time.
- **B. One prompt writes the file.** The Level 2 and Level 3 brief prompts now tell Claude to write the plan or paste the findings into `TESTS.md` or `REVIEW.md` itself, and the hints quote the new prompts. Reason: removes one round-trip per level.
- **C. Level 3 fixes only the top FIX item** (more if the group asks, if there is time), with a test that fails before the fix. Reason: one fix with a failing test teaches the loop; eight did not fit in eight minutes.
- **D. Level 0 is one prompt, not three.** The Understand prompt, the missing-values question and the Plan prompt are merged into one; hint 1 is now a fallback. Reason: three prompts cost minutes of reading and waiting for no extra learning.
- **E. Level 1 play is one minute and gives one feature for the group** (not one each plus a favourite). The manifest reflection is "One feature the group would add.", the self-test matches it by `"would add."`, and `LOG.md` has "The feature we would add". Reason: saves two minutes at the busiest level.
- **F. A "Finished early" section in the Level 3 brief** replaces the "Time left?" bullet: a one-line lead-in and two bullets, a day/night button that switches the page between light and dark colours, and mouse selection of points (box or lasso, in the 2D view) showing how many were picked, with their labels if the dataset has them. Each is built the same way as the main steps (one step, run it, look, commit). Reason: gives fast groups something concrete without extending the timed levels; kept to two short bullets so it does not add reading.

`PLAYBOOK.md` is unchanged: it is generic take-home advice (for example, it still says to fix FIX items one at a time), and the exercise caps are a workshop time constraint.

### External review panel, round 1 for the tightening (2026-10-14; Codex gpt-6.1-sol high, Claude Opus 5.5 high, read-only via orchestrator, staggered parallel launch)

Neither reviewer found a correctness defect in `gates.py` or `selftest/run.py`. Findings and decisions:

| Finding | Decision |
|---|---|
| Level 3 hint 3 still ended "Then the next.", contradicting the one-fix brief and persona (both, serious) | Fixed: "Then the next, if there is time." |
| `docs/05` kept pre-tightening text: the two-minute play, the section 7 L2/L3 persona drafts, the section 8 reviewer copy without item 4, the Level 3 prompt without "paste into REVIEW.md" (both, moderate) | Fixed, minimally, in each place. |
| Walkthrough Level 2 made `make coverage` compulsory where the brief says "if there's time" (Codex, moderate) | Fixed: "if there's time". |
| The Level 1 feature led nowhere: the walkthrough and `docs/05` said a group "may build one" but Finished early offered only the two new ideas (Claude, moderate) | Fixed: the lead-in now says "the feature you agreed at Level 1, or one of these". |
| Finished early did not say to unlock first; building before `./gate unlock` inflates the Level 3 time and could fail the final gate on a dirty tree (Claude, moderate) | Fixed: "Unlocked with time to spare?". Verified the guard never reads the `complete` flag, so `explorer/` and `tests/` stay editable after the last unlock. |
| Plotly has no box or lasso select on `scatter3d` (Claude, minor) | Fixed: "in the 2D view". |
| "When the fix is in and the tests pass" contradicted "Nothing worth fixing: that's a fine result" (Claude, minor) | Fixed: "When `REVIEW.md` is triaged and the tests pass". |
| Build contract `exercises/explorer/PLAN.md` kept the old Level 1 reflection (both, minor) | Fixed. |
| Walkthrough overclaimed "in practice Sonnet's plans fall that way" from one three-step run (Claude, minor) | Fixed: the split matched; the count came from the cap. |
| Reviewer agent item 4: "at most once" ambiguous, "(not run)" may clutter (Claude, risk) | Reworded: `make test` and the tool once each; mark findings only read as "(not run)". |
| The old `(paste it here)` skip in `gates.py` is dead now the template says `(Claude writes it here)` (Claude, bloat note) | Removed. |

Accepted risks, to watch in calibration rather than add text now: step 2 is now the whole page, so "you know which step did it" is weaker; the merged Level 0 prompt removes the pause between summary and plan; a group using the playbook's generic prompt may hit one two-step refusal; Level 3 stays tight; the Level 3 persona's "top FIX item only" might make Claude hesitate over a Finished early feature when asked directly (unlikely).

### External review panel, round 2 for the tightening (2026-10-14; verification of round 1, same reviewers, continued sessions)

Both reviewers judged every round-1 finding resolved as the table says and found no new defect and no serious finding. Two minor facilitator-only mismatches were fixed: the walkthrough's description of the reviewer agent still said "at most once" (now "once each", matching the agent), and the walkthrough and `docs/05` said Finished early "offers two features" (now "after the unlock, the Level 1 feature or two others", matching the brief). Panel closed.

## Answer hints (2026-10-14; facilitator request)

Every level with a graded gate question now has a fourth hint, 3 minutes after the third (13 minutes), that gives the answer and a one-line reason: Speed Run Levels 0–2, TDD Ladder Levels 0, 3 and 4 (Levels 0 and 3 point at the group's own `./tdd score` output, since the answer is the group's), Explorer Level 1. Explorer's answer depends on the dataset, so gatekit hint tiers gained an optional `text_from` (an exercise-tool `hints` function, falling back to the static text on any error), mirroring the question field. Hints are logged, so the facilitator sees who took the answer. Level 0 hint files sit unencrypted in `.workshop/` (the guard refuses Claude's direct reads of it, but a Bash `grep -r` from the root reaches it: a soft limit); a human could read the Speed Run and TDD Level 0 answers there, a cheat that only costs the group its practice, consistent with the honest limits.

Verification (same reviewers): both found no remaining problems with the one-dataset change.

Review (Codex gpt-6.1-sol, Claude Fable 5.1): Claude found no problems and confirmed every answer against the gate ranges, the TDD validators and the shipped column file. Codex flagged that taking the answer hint writes its text to `LOG.md`, which Claude can read (serious in its view). Rejected: the text reaches the log only after a human has taken it from `./gate hint` and is about to type it, Claude can never run `./gate unlock`, and all hint tiers have always been logged for the show-and-tell.

Wording (facilitator): every answer hint opens "The gate unlock answer is …", so it reads correctly when a group takes it before reaching the gate question. A group that still cannot unlock, or hits a broken check, is moved on with `./gate skip --master` (facilitator passphrase, reason logged), as each walkthrough's troubleshooting table says.

## Release-readiness review (2026-10-14)

A release-readiness review of the three built exercises and gatekit (full findings and triage in `archive/REVIEW-2026-10-14-release-readiness.md`, kept outside the release tree), checked against Claude Code 2.1.299 and its current docs.

Verified against the Claude Code docs (2.1.299):

- The `Monitor` tool takes a free-form `command`. Bash permission allow and deny rules apply to it, but a `Bash` PreToolUse hook matcher does not fire for it, so the guard's matcher now lists `Monitor` and the guard treats it as Bash.
- The Grep tool is absent by default on macOS but present wherever an agent definition lists it (the Explorer reviewer agent does), so it stays in the matcher. The guard no longer applies dot-glob checks to Grep's regex `pattern`.

Fixes applied:

- `./tdd green` accepts a `pytest.raises` red (pytest's `Failed: DID NOT RAISE` is now recorded as an `AssertionError`).
- Explorer `sections()` ignores `#` lines inside code fences.
- `*.dSYM/` added to the template `.gitignore`, so `./race submit` is not blocked by clang debug folders.
- The guard denies `git clean -x` and `-X`: they delete `.workshop/`, `.tdd/` and `.venv/`, and the next `./gate status` or `./preflight` would silently re-initialise to level 0.
- `sed -E -i` is now a write verb.
- Relative redirect targets are resolved against the hook's `cwd` and a literal `cd`.
- zsh `>!` is a redirect.
- The build strips `accept`, `lo` and `hi` from crypto questions in the shipped manifest (verified gates keep them). The answers remain in the hint files and, for the Explorer, the tool source, so `gatekit/README.md` section 11 now calls the crypto answer a guard-protected soft secret.
- ruff B904 is ignored by policy.
- Documentation: reset command corrected in `docs/01` and `BUILD-SPEC.md`; status banner on `BUILD-SPEC.md`; top-level `PLAN.md` archived to `archive/PLAN.md` (gitignored); stale counts and scope in `CLAUDE.md` and the Explorer walkthrough; `model_lock` and crypto-gate limits in `gatekit/README.md`; the never-created `level1-start` tag in `docs/04` replaced by the Level 0 unlock's `start_from_stub` and `./tdd new-attempt`; the embedded reviewer agent copy in `docs/05` replaced by a pointer to the shipped file.

The implementation was reviewed by the same panel (Codex gpt-6.1-sol and Claude Opus 5.5, high effort, read-only, staggered parallel launches) over five rounds, each narrower than the last. Round 1 found that the first cwd-aware redirect check stripped the repo prefix before parsing (an absolute write into frozen `tests/` from a subdirectory `cwd` passed, and an absolute write into `src/` from `tests/` was refused), refused literal `cd` forms (a quoted path with a space, `~`, bare `cd`, a trailing slash, `-P`), positioned repeated redirect targets by their first occurrence, read quoted text as a `cd`, matched `-i` inside a quoted sed script, and that the sigma boundary fix used a blanket epsilon. All were fixed: the guard parses before the prefix strip, `Parsed` carries a quote mask, a `cd` argument is read as one shell word and is computed only when it contains `$`, a backtick or a glob, redirects are positioned per occurrence, the sed rule skips quoted arguments and counts `-ie`/`-i.bak`, and `allowed_shift` returns the nearest integer only when `sigma^2 * golden` is exactly its square. Rounds 2 to 5 closed the regressions each fix introduced (trailing tokens after a `cd` argument, a multi-line `-m` message, quoted or `=` option values before `-m`, and an unquoted option value swallowing `;`). The panel also removed bloat: a quote-aware line splitter, a duplicated `DID NOT RAISE` branch and an author-only build test. Each round's findings were reproduced in the main session before being accepted.

Dropped as low value after the external panel: the `.*` matcher, extra guard write verbs and path identity hardening, a bench-harness watchdog, Explorer value checks, all decompositions and simplifications, a new exercise-tool test tree, and splitting `BUILD-SPEC.md` and `DECISIONS.md`. The full list is in `archive/REVIEW-2026-10-14-release-readiness.md`.

## Four take-home skills (2026-10-15)

The workflow the Explorer teaches (plan, build in steps, test, review) is now also four generic Claude Code skills in `skills/` (`plan-code`, `style-code`, `test-code`, `review-code`), copied by the build into the participant repo of every exercise whose manifest lists them (`"skills": [...]`; Explorer lists all four) at `.claude/skills/<name>/SKILL.md`. Each is one Markdown file of about 55 lines, written for any project: they never mention this repository, an exercise, a gate, a level or the group ritual (the humans' own list before the agent's, the five-to-eight test plan, the three-to-five triaged findings, the `TESTS.md` and `REVIEW.md` headings). Those stay in the briefs, personas, hints and templates, which is where the exercise choreography belongs. The bridge is one rule in `plan-code` (if the project already has a `PLAN.md` template, keep its headings) and, for `TESTS.md`, the Level 2 prompt itself, which names the heading to write under. Drafted from the author's `implementation-plan`, `style-guide`, `code-review` and `code-simplifier` skills with the workflow machinery (slices, frozen contracts, receipts, launchers, lint script, C and Fortran notes) removed; `test-code` is new.

How the exercise uses them: every playbook prompt keeps its wording and names the skill ("Then, using the plan-code skill, propose a plan ..."; "Implement step 1 of PLAN.md only, following the coding guidelines in the style-code skill ..."; "Using the test-code skill, talk me through ..."; "Use the review-code skill to review the code since start against PLAN.md ..."). The prompts are instructions to the humans as much as to Claude, so the skill is named in the prompt rather than typed as a slash command. The skills are therefore model-invocable (no `disable-model-invocation`), and each persona and the participant `CLAUDE.md` carry one line telling Claude to invoke a named skill with the Skill tool and never to read `.claude/`. `review-code` runs with `context: fork` and `background: false`: a plain forked subagent, not the shipped `reviewer` agent, so what participants take home is what they used. The `reviewer` agent still ships as the Level 3 fallback (walkthrough section 6). The `manifest.json` take-home note, the Level 3 brief, the playbook's "Make it stick" and the walkthrough's opening now point at the skills. The TDD Ladder and Speed Run manifests do not list the skills yet: shipping `test-code` model-invocable into the TDD Ladder could undercut its Level 1 lesson (a literal persona told to "use TDD"), so each exercise opts in when its briefs are ready; see `PROGRESS.md`.

Verified against the Claude Code docs (<https://code.claude.com/docs/en/skills>, installed Claude Code 2.1.300): project skills load from `.claude/skills/<name>/SKILL.md`; frontmatter `name`, `description`, `context: fork`, `background: false` (2.1.218 or later); `disable-model-invocation: true` would make a skill user-only, so it is not set; the combined description and `when_to_use` are capped at 1,536 characters; a new skills directory needs a restart or `/reload-skills`; precedence on a name clash is enterprise, personal, project, which is why the names are `plan-code` and so on rather than `code-review`, a name the bundled skill and the author's own personal skill already use.

Verified at runtime in a built `dist/explorer` (headless `claude -p`, Sonnet, the shipped settings and hooks in force):

- The four skills are listed to Claude with their exact descriptions despite the `Read(./.claude/**)` deny rule and the guard's secret-directory rule: the harness loads them, Claude never reads them. (A `references/` file or script inside a skill would be refused, which is one reason each skill is a single file.)
- "Audit explorer/data.py using the style-code skill" made Claude call the Skill tool (`Launching skill: style-code`), read the file, look for a linter configuration and report findings against the guidelines without editing.
- "Use the review-code skill to review the code since start against PLAN.md ..." made Claude call the Skill tool, a forked subagent read `PLAN.md`, the diff and every changed file, the guard fired inside the subagent on a compound git command (it noted the refusal and carried on, as instructed), and the ranked findings table came back to the main session, which relayed it without editing anything. Two observations from that run: the reviewer produced eight findings (the skill sets no number on purpose, since a limit such as the exercise's three to five is the request's to set, and the Level 3 persona and brief set it); and it chose not to run the tests ("(not run)" on every row), which the skill asks for once and the persona's `make test` allowance supports, so the leader should expect it but not rely on it.

Not verified: an interactive session with the `/` menu (the walkthrough's section 3 check covers it on each leader's laptop), and whether `UserPromptSubmit` (the persona injection) fires for a forked skill's prompt; the headless run suggests it does not, which is why the Level 3 persona passes the base, the plan and the number as the skill's arguments.

External panel, round 1 (Codex gpt-6.1-sol and Claude Opus 5.5, high effort, read-only, staggered parallel launches through the orchestrator; every finding checked in the main session before acting). Both said REVISE. Fixed: `test-code` step 4 told Claude to break the code and revert for every new test, which contradicted the Level 2 persona ("no deliberate-bug experiments unless the group asks") and, with a whole-tree revert, could wipe uncommitted tests, so it now offers one small break and undoes that one edit by hand; the `skills/README.md` row for `test-code` still carried the rejected "must-not-break list, five to eight tests" choreography; the `style-code` audit told Claude to run a configured formatter, which can rewrite files, so it now asks for check-only mode; a `test-code` line discouraging "the same path twice with different numbers" would discourage scale and precision tests, deleted; "a browser, a GPU, a remote service" as things tests cannot cover became things the tests here cannot exercise; the four "Make it stick" sections repeated the README's installation text into every invocation (and, for `review-code`, into the forked reviewer's prompt), deleted and their two distinct tips moved to the README; `review-code`'s "After the review" section was addressed to the main session, which never sees a forked skill's body, deleted (the README's session walk-through keeps the triage advice); a duplicated test-naming line in `style-code`, deleted; the playbook's review prompt had been rewritten rather than extended, and its build prompt differed from the Level 1 brief, both aligned with the briefs; the decisions entry claimed a template rule in `test-code` that only `plan-code` has. Two structural fixes: the Level 3 persona now has Claude pass the base, the plan and "three to five findings" as the skill's arguments, because the fork does not see the persona, and that is what keeps a short honest review from failing the three-row gate; and the build now copies only the skills an exercise's manifest lists, because `test-code` shipped model-invocable into the TDD Ladder could answer "use TDD" for the literal persona and hide the Level 1 lesson. Rejected: dropping the skill line from the participant `CLAUDE.md` because the personas repeat it (the repo duplicates every standing rule in both places on purpose).

Round 2 (same panel, continuations of the round-1 sessions): every round-1 item confirmed fixed. Two one-line defects found and fixed: the `test-code` description still said "see every new test fail once", contradicting the revised step 4, and a round-1 sentence in this entry still described the old mechanism for the Level 3 finding count. Bloat removed: a README bullet that repeated the session walk-through. Codex kept one item open: a review with fewer than three findings cannot satisfy the three-row Level 3 gate; the gate is unchanged (it is the exercise's, and ACCEPT and REJECT rows count), and the Level 3 brief's "If it goes differently" now says to ask for the next most important findings, low severity included. No further round: neither reviewer reported a new serious finding, and Claude Opus said the remaining edits needed no re-review.

## Other agent harnesses (2026-10-16)

Some participants will bring their own agent (Codex, Cursor, Copilot, Antigravity, OpenCode). The full brief, with the findings, the rejected options and the review log, is `docs/HARNESS-PORTABILITY.md`; this entry records what was built and what was verified. Claude Code stays the recommended, unchanged path.

### Design

| Area | Decision |
|---|---|
| Instruction file | `workshop/AGENTS.workshop.md` (renamed from `CLAUDE.workshop.md`) is written to `AGENTS.md`: the canonical, harness-neutral rules, levels and "Never" list. |
| `CLAUDE.md` | Rendered by the build from the shared `gatekit/agents/CLAUDE.md`: an `@AGENTS.md` import plus a short Claude Code section (model line with `__MODEL_NAME__` from `models.default`, the PERSONA block, the Skill-tool rule). |
| `OTHER-AGENTS.md` | One shared page, `gatekit/agents/OTHER-AGENTS.md`, copied only when the manifest sets `"other_agents": true`. Explorer only. TDD Ladder and Speed Run are Claude Code only (their lessons arrive by hook) and say so in their walkthroughs. |
| Hooks | Not ported and the hook syntax is unchanged. Elsewhere the written rules in `AGENTS.md` are the fallback, by design (trust, not a fortress). `OTHER-AGENTS.md` carries an opt-out line for harnesses that import Claude Code hooks. |
| Skills | Stay in `.claude/skills/` only, with a read-the-file fallback; Explorer's `AGENTS.md` allows reading a shipped `SKILL.md` when a prompt names the skill. |
| Level changes | No PERSONA arrives on other harnesses; `OTHER-AGENTS.md` asks the group to have the agent run `./gate brief` at the start and after each unlock. Not in `AGENTS.md`, because Claude Code's subagents read it and never get a PERSONA, so a rule there would change the Claude path. |
| Wording | "The agent" replaces "Claude" in participant text and in Explorer's walkthrough; Claude Code keys and commands appear in brackets; "Claude Code" is kept where it names the product. The TDD Ladder and Speed Run walkthroughs keep "Claude": they describe a Claude Code run. |
| Build and gatekit | `tools/build.py` writes `AGENTS.md`, renders `CLAUDE.md`, copies `OTHER-AGENTS.md`, and fails if `workshop/AGENTS.workshop.md` is missing. `manifest.py` accepts an optional boolean `other_agents` and rejects other types. `hooklib.FROZEN_FILES` gained `AGENTS.md` and `OTHER-AGENTS.md`. Preflight checks that `AGENTS.md` and `CLAUDE.md` exist. |
| Documents | `gatekit/README.md` documents the instruction files and `other_agents`, and section 11 now says that fixed success lines make the crypto gates a casual-reading barrier only (Explorer's packs hold nothing secret). Walkthroughs and the top-level README gained one line each; Explorer's walkthrough has a "Groups on other agents" subsection. |

### Deviations from `docs/`

None of `docs/01`–`05` anticipated other harnesses. The participant instruction file is now `AGENTS.md` (with a thin `CLAUDE.md`), not `CLAUDE.md`; where `docs/` or `BUILD-SPEC.md` say the participant file is `CLAUDE.md` or `CLAUDE.workshop.md`, `AGENTS.md` and `AGENTS.workshop.md` win. `BUILD-SPEC.md` was updated to match.

### Verified facts

| Item | Finding | Source and version |
|---|---|---|
| Claude Code and `AGENTS.md` | Read only when no `CLAUDE.md` exists (v2.1.277 or later). | <https://code.claude.com/docs/en/memory>, installed Claude Code 2.1.301 |
| The `@AGENTS.md` import | The documented bridge; it never loads `AGENTS.md` twice. | Same |
| `.agents/skills` | Claude Code does not read it (it reads `.claude/skills`). | Same |
| Copilot CLI hooks | `copilot help config` documents `disableAllHooks` (default false); this is the opt-out in `OTHER-AGENTS.md`. | Copilot CLI 1.0.91, run locally |
| Cursor third-party import | The setting is named "Include Third-Party Plugins, Skills, and Other Configs". Documented, untested: Cursor is not installed here. | <https://cursor.com/docs/reference/third-party-hooks>, docs only |
| Other harnesses | Skills folders, plan or ask modes and `AGENTS.md` support are from the official docs read 2026-10-16. Untested. | Official docs, 2026-10-16 |

### Rehearsals and review

No rehearsal on another harness yet; the owner will rehearse. Until then "supported" means accommodated with documented fallbacks, and the Explorer timings are calibrated on Claude Code with Sonnet only. Review: two rounds on the brief with Codex gpt-6.1-sol, then an independent panel on the implementation (Codex gpt-6.1-sol and Claude Fable 5.1, high effort, read-only; both APPROVE WITH CHANGES, no serious issues). Every finding was checked and fixed; see `docs/HARNESS-PORTABILITY.md` section 9.

## Gate prompt wording and `contains` keyword matching (2026-10-16)

Deviations from `docs/01`–`05` and `BUILD-SPEC.md`, which are not edited.

- **Prompt punctuation and the reflection header.** Every gate prompt and reflection now ends in "?", ":" or ")" (never ".)"), several are reworded to match (for example the Explorer dimuons question now ends "In a word or two, which particle makes it?"), `./gate unlock` prints one "Quick reflection (saved to LOG.md, any answer is fine):" header before the reflection prompts and no longer prints "Logged to LOG.md.", and `./tdd abort` prints its "Answering no restores tests/ ..." aside before the yes/no question instead of inside it. `manifest.validate` now rejects a prompt or reflection that breaks the ending rule. Reason: prompts are printed with the cursor straight after them, and a trailing full stop or aside reads badly there.
- **`contains` for keyword questions.** An optional `contains` list canonicalises any typed answer whose canonical keyword includes a listed term (checked in list order) to that term; `accept` entries are canonicalised the same way and each term is also an accepted form, so the build still enumerates one slot per form. The shipped manifest keeps `contains` (runtime canonicalisation needs it), so the terms are readable, like the tool source. Reason: "J/psi" was too sensitive to how it was typed ("The J/ψ(1S) meson", "J/psi particle").
- **Explorer Level 1.** The question has `contains: ["meson", "psi", "charmonium"]` and the redundant jpsi/psi/meson `accept` entries are removed; pulsar answers stay in `accept`. Any answer containing meson, psi or charmonium passes for either dataset. Known consequence: "upsilon", "pion meson" or a bare "meson" also pass, a deliberate trade for generosity at a 70-minute workshop. The dimuons `wrong_hint` no longer says "meson" (it says "bound state"), so the hint does not give away an accepted word.

## Answers accepted when a group clearly knows them (2026-10-16; facilitator request)

Probes showed correct answers being refused for their form ("It's the Sun", "N(N-1)/2 = 499500", "500k", "c - the second only", "0.93%", "none - we killed all 16"). The facilitator asked for a simple solution that gets most of the way, so several larger ideas were dropped (see the last entry). Deviations from `docs/01`–`05` and `BUILD-SPEC.md`, which are not edited. Behaviour is in `gatekit/README.md` sections 4, 6 and 11.

- **Any number counts (numeric, numeric-log).** `answers.candidates(question, text)` returns one canonical form per number in the answer (the last 6, de-duplicated, order kept); `matches` is true if any candidate is accepted, and `gate unlock` tries every combination of candidates as slot secrets. Reason: results usually come last and groups show their working. A numeric answer with no number is still a format error with the old message; failed-attempt logging and hints are unchanged.
- **Six guesses per attempt (trade).** A typed answer can now carry up to 6 numbers, so a crypto gate gets up to 6 guesses per attempt. Reason: accepted for a learning scaffold whose crypto gates are already only as strong as the answer space (README section 11); a wrong 6-number answer costs about 6 x slots x 23 ms.
- **`%` and `k`/`M` suffixes.** `%` after a number divides by 100; `k`, `K` or `M` after a number multiplies by 1e3 or 1e6 unless a letter follows ("500 kB", "5 kpc" are untouched). Reason: "0.93%" and "500k" are correct answers.
- **Choice letter among words.** A leading single-letter token wins ("c - I think the second is a pass"); otherwise the only stand-alone one does ("I think c"); "i" is never an option; anything else remains a format error. Reason: groups type the option text as well as the letter. Known consequence: "both (not c)" reads as c.
- **Explorer Level 1.** `contains` is now `["meson", "psi", "charmonium", "sun", "solar", "earth"]`, `accept` is `["us", "sol"]` (the rest were redundant); 8 slots instead of 16. "galactic centre", "Sgr A*", "bulge", "black hole" and "Sagittarius" still fail. Known consequence, like the existing meson rule: "not the Sun" also passes. Reason: "It's the Sun", "the Sun's position", "Sun (solar system)", "Earth / the Sun" and "Sol" were refused.
- **Speed Run pairs widened.** L0 `pairs` is now `numeric-log`, 4 decimals, `lo` 499500, `hi` 500000, which accepts 499,402 to 500,092 (499,500, 500,000 and "500k" pass; 500,500, 999,000 and 1,000,000 fail). Reason: the facilitator asked to "widen a little"; numeric-log at 4 decimals is 6 slots instead of 501 and still rejects N(N+1)/2, N(N-1) and N^2. The Speed Run self-test's wrong answer 499501 is now accepted, so it uses "N(N+1)/2 = 500500" instead.
- **`_grid` alignment fix.** The grid now runs from `lo` rounded to `decimals` to `hi` rounded to `decimals`; before, it started at the unrounded `lo`, so a non-aligned `lo` (log10(499500) = 5.698535) could miss the top form (500000 gives 5.6990). The accepted forms of every existing numeric and numeric-log question (Speed Run matrix, TDD sigma, the test fixture) are unchanged.
- **TDD Ladder validators.** `spec_id_in_last_survivors` treats an answer with the word none or nil (or just "no" or "0") and no S-prefixed id as "none"; otherwise it collects all S-prefixed ids (falling back to `common.spec_id` for a bare number) and accepts if any is a survivor. `equals_last_acceptance_count` accepts any number in the answer equal to the count. Reason: "none - we killed all 16" was parsed as S16, and "sqrt(0.683*0.317/2500) = 0.0093" and "0.93%" were refused.
- **Dropped for simplicity.** A `unit` option for byte units, an `options` text mapping for choices, "thousand"/"million" words, superscript and `×10^-3` parsing, a "killed them all" rule and a cap on the number of spec ids. None is needed for the probe answers that matter, and each adds manifest fields and validation. The Speed Run matrix and perbin gates are unchanged.

## Group UX round: leader quickstarts, shorter docs, gentler gates, talk prompts (2026-10-21; facilitator request)

From the facilitator's Explorer playtest. Applies to all three built exercises unless stated. Deviations from `docs/00`–`05` (which still describe typed reflections) and `BUILD-SPEC.md`, which are not edited.

- **Leader quickstart.** Each exercise has `LEADER-QUICKSTART.md` beside its walkthrough: about 850 words covering set-up, the session, each level (goal, what good looks like, one nudge, the gate answer) and what to do when stuck. Like the walkthrough, it is sent with the bundle and never shipped. Reason: the leader material was buried in a 3,000–6,000-word walkthrough.
- **Shorter group docs.** Every README and brief was rewritten to one shape: Where we are, Do this, Watch for, The gate. Reference material stays where a level needs it. Group-facing words fell by roughly 25–50%. "Persona in force" is dropped from Explorer brief headers. Reason: the reading burden was too heavy for a 45-minute exercise.
- **Explorer `INTERFACE.md`.** The fixed tool interface moved word for word from the README into `level0/INTERFACE.md`. It is frozen at every level and named in the Level 0 prompt, the personas, `AGENTS.md` and `reviewer.md`. Reason: it is mostly for the agent, and it halved the README. Not called `SPEC.md`, because that is TDD Ladder's group spec.
- **Explorer side tasks warn but pass.** The following now print a `Note:` line and pass:
  - Level 0: fewer than three acceptance criteria, or a missing or blank decision line.
  - Level 2: "Our list" missing or under three items, or the agent's plan missing or empty.
  - Level 3: "Our guesses" missing or under two, or fewer than three triaged findings.
  - Still strict: commit counts and clean trees, exactly two plan steps, the `Dataset:` line, plan sections present and non-empty, tests, and tool output.
  - Notes go to the check's stderr; stdout is still `success_line`, so `answers.json` is unchanged.
  - Reason: the facilitator's request that a group not be blocked by a skipped side task. Version control stays strict, as a lesson in itself.
- **TDD Ladder and Speed Run gates unchanged.** `SPEC.md` (Level 2) and the mutation report (Level 5) are those levels' whole output, not side tasks. Speed Run's only human-written check is the `race.toml` justification, which is the correctness declaration itself.
- **No typed reflections.** The manifest keys `reflection`, `reflections` and `pre_reflection_note`, and the gate type `crypto-reflection`, are replaced by `talk` (printed under "Talk it over (30 seconds, nothing to type):"), `note` and `crypto`; `manifest.validate` rejects the old keys. Each `LOG.md` has a `### Talk it over: <prompt>` heading where the Scribe can note the answer. Reason: typing an answer stalled the group just as they wanted to move on.
- **Unlock screen.** It now shows, in order:
  - `PASS` and any notes;
  - the graded questions;
  - `Level N unlocked: <title> (about M minutes)` with a dash rule;
  - new files, other than `BRIEF.md`;
  - any post-unlock message;
  - `Next: swap the Driver, then <start>.` (from a new optional level field, `start`);
  - `Brief: BRIEF.md (or ./gate brief)`;
  - the gate note, then the talk prompts.

  The final screen is headed `Exercise complete. Well done.`. Dropped: `BRIEF.md` from "New files" (every level has one, and the Brief line names it) and Explorer's "Recorded commit …" line (plumbing). TDD's stub-reset message is shortened. Explorer `pass_message`s are worded so they stay true when notes are shown. Reason: the next action was buried.
- **A template must not satisfy a gate.** TDD's `LOG.md` template briefly gained a `## Mutation report` heading, which would have opened the Level 5 gate. It was removed, and the Level 5 brief now says to add the section.

### External review panel, round 1 (Codex gpt-6.1-sol high, Claude Opus 5.5 high)

Both returned REVISE, with no gate-code defects. Every finding was independently verified.

| # | From | Finding | Decision |
|---|---|---|---|
| 1 | Codex | The Explorer quickstart says to open the browser before the first commit, but step 1 has no page | Fixed: open it once the page exists, before committing it |
| 2 | Codex | The Explorer L3 brief tells every group to fix a FIX item, even when they marked none | Fixed: "If you marked a FIX:" |
| 3 | Claude | Briefs over-run the spec's shape limits; repeated closing lines | Fixed: Where we are, Watch for and The gate trimmed, and repeats removed. Load-bearing reference material kept. The 50% cut was a guideline, so exercises with exact numbers or rules keep them |
| 4 | Claude | `BRIEF.md` *is* copied to the repo root on unlock, so "hidden directory" was a false reason | Fixed: the screen says `Brief: BRIEF.md (or ./gate brief)`, and the reason is corrected above |
| 5 | Claude | The Explorer README gate line still lists "the four decisions" as required | Fixed: "every section filled in" |
| 6 | Claude | The Explorer walkthrough misquotes a note and names a source path | Fixed |
| 7 | Claude | Speed Run `LOG.md` bullets duplicate the talk headings | Fixed: bullets removed |
| 8 | Claude | The Speed Run README lists extra commands after its table | Fixed: sentence removed |
| 9 | Claude | Two `start` lines read "then … then" | Fixed |
| Q | Claude | The decision record says Speed Run has no human-written checks, but the `race.toml` justification is one | Wording corrected; it stays strict as the correctness declaration |

### One `./preflight`, and no assumed folders (2026-10-21; facilitator request)

- **`./preflight` sets itself up.** It checks that `.venv` is current: its python runs and every `==` pin is installed at its pinned version. If not, it prints one set-up line, creates `.venv` if it is missing or broken, and installs `requirements.txt`; then it runs the checks as before. A set-up failure shows as a `FAIL` line, and the checks still run. `--setup` forces the reinstall as a repair. A current `.venv` costs nothing and never touches the network.
  - Why: there was no case where a human wanted the checks without the set-up.
  - The agent was already able to run `./preflight --setup`, which installs only the pinned requirements, so this adds no new capability.
  - `BUILD-SPEC.md` and `docs/00`/`05` still describe the two-step form; they are historical designs.
- **No assumed folders.** The walkthroughs and quickstarts no longer name `~/Desktop`, `~/Downloads` or `~/opus-control`. The bundle is written in the current folder, and a comment says to copy it out, because a rebuild wipes `dist/<name>`. The clone runs wherever the bundle was saved. The master passphrase path is the project's documented config location and stays.
- **Panel round 3 on preflight** (Codex REVISE, Claude ACCEPT):
  - `--setup` now passes `--force-reinstall`, because plain pip skips satisfied pins.
  - A venv without pip is treated as broken and recreated.
  - With no `requirements.txt` there is nothing to set up, which avoids a misleading FAIL in the gatekit fixture.
  - Import-failure messages point to `./preflight --setup`.
  - The bundle comment warns that a reset deletes it too. The command stays as the facilitator asked: no folder assumed.
