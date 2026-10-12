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
