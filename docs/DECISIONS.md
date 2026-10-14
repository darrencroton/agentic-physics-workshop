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

Every level with a graded gate question now has a fourth hint, 3 minutes after the third (13 minutes), that gives the answer and a one-line reason: Speed Run Levels 0–2, TDD Ladder Levels 0, 3 and 4 (Levels 0 and 3 point at the group's own `./tdd score` output, since the answer is the group's), Explorer Level 1. Explorer's answer depends on the dataset, so gatekit hint tiers gained an optional `text_from` (an exercise-tool `hints` function, falling back to the static text on any error), mirroring the question field. Hints are logged, so the facilitator sees who took the answer. Level 0 hint files sit unencrypted in `.workshop/` (which Claude cannot read); a human could read the Speed Run and TDD Level 0 answers there, a cheat that only costs the group its practice, consistent with the honest limits.

Verification (same reviewers): both found no remaining problems with the one-dataset change.

Review (Codex gpt-6.1-sol, Claude Fable 5.1): Claude found no problems and confirmed every answer against the gate ranges, the TDD validators and the shipped column file. Codex flagged that taking the answer hint writes its text to `LOG.md`, which Claude can read (serious in its view). Rejected: the text reaches the log only after a human has taken it from `./gate hint` and is about to type it, Claude can never run `./gate unlock`, and all hint tiers have always been logged for the show-and-tell.

Wording (facilitator): every answer hint opens "The gate unlock answer is …", so it reads correctly when a group takes it before reaching the gate question. A group that still cannot unlock, or hits a broken check, is moved on with `./gate skip --master` (facilitator passphrase, reason logged), as each walkthrough's troubleshooting table says.
