# Brief: supporting other agent harnesses and models

Status: **implemented** (2026-10-16). This is the design record; what shipped, what changed in implementation review (§9, Implementation review) and what was rehearsed are in `docs/DECISIONS.md`.

## 1. Goal and principles

The workshop repos assume Claude Code and Claude models throughout. Some experienced participants will bring their own harness (Codex CLI, Cursor, GitHub Copilot, Antigravity, OpenCode) and model. The goal is to accommodate them where it is simple to do so, without making the experience worse for the majority on Claude Code.

Principles, from the repo owner:

1. **User experience comes first.** Smooth and effective beats rigid. No bloat, and no engineering for edge cases.
2. **The Claude Code path does not change in behaviour.** Most groups will use it, and it works well. Claude Code and Claude models stay the recommended setup.
3. **Trust, not a fortress.** This is a learning tool for scientists. Where a hook cannot run in another harness, the fallback is the written rule (the "Never" list) that the hook was enforcing anyway. We do not port hooks.
4. **KISS and DRY.** One source of truth per rule. Generalise the shared machinery (`gatekit`, `tools/build.py`, wording) for every exercise, even where an exercise stays Claude-only.
5. **Content for the minority lives in one place.** Briefs, READMEs, personas and hints stay short. Where a Claude Code key or command is named, it is phrased generally with the Claude Code form in brackets, for example "stop the agent (Esc in Claude Code)". Anything more goes in a single `OTHER-AGENTS.md`, linked once from the README.

"Supported" in this brief means **accommodated with documented fallbacks**: a group on another harness can complete the exercise by following `OTHER-AGENTS.md`. It does not mean every harness has been rehearsed. The harnesses actually rehearsed are named in `docs/DECISIONS.md`.

## 2. What we found

The review (three subagents, each claim checked in the main session) found the coupling narrower than the word counts suggest.

**Already harness-neutral.** Everything the humans run in the gate terminal: `./preflight`, `./gate`, the level checks (`checks/levelN.py`, `exploretool/gates.py`), the packs, state, hints, `LOG.md` and the git evidence. It is stdlib Python and reads nothing from Claude Code (no `~/.claude`, transcripts, model names or `CLAUDE.md` content).

**Claude-specific mechanics** (designed for Claude Code; see §3 for harnesses that import some of them):

| Mechanism | File | Role | Outside Claude Code |
|---|---|---|---|
| Guard (PreToolUse) | `.claude/hooks/guard.py`, `hooklib.py` | No reading hidden folders; edits only where the level allows; no human-only commands, installs or pty tricks | Not run (or imported with untested behaviour, §3). The "Never" list in the instructions file is the fallback. |
| Persona per prompt (UserPromptSubmit) | `.claude/hooks/teacher_context.py` | Injects the level banner and `persona.txt` | Not run. Explorer's instructions file repeats the level rules; `BRIEF.md` names the level. The Level 3 persona adds review arguments the instructions file lacks (§4.2). |
| Model lock and check | `model_lock.py` (PreModelSwitch), `model_check.py` (SessionStart), settings `model` | Holds the session on the exercise's model | Not run. Model choice is the participant's. |
| Plan mode at start | settings `permissions.defaultMode: "plan"` | Level 0 is "plan, no code" | Participant uses their agent's own plan or ask mode, if it has one. |
| Permission denies | settings `permissions.deny` | Duplicates the guard | Not run. |
| Instruction file | `CLAUDE.workshop.md` → `CLAUDE.md` (`tools/build.py:148`) | Standing rules, levels, "Never" list | Most other harnesses read `AGENTS.md`, not `CLAUDE.md`. |
| Skills | `.claude/skills/<name>/SKILL.md`; `review-code` has `context: fork` | Take-home workflow, used at each level | Several harnesses read `.claude/skills/`; others can read the file directly. Only Claude Code (and VS Code Copilot, experimentally) forks. |
| Reviewer agent | `.claude/agents/reviewer.md` | Level 3 fallback reviewer | Cursor reads `.claude/agents/`; others ignore it. |
| Human-only commands | `tty.py` (`CLAUDECODE` check plus isatty) | Keeps the agent off `./gate unlock` | Only the isatty check applies. |

**Textual assumptions.** Participant-facing material has:

- about 180 "Claude" mentions, about 20 of them printed by `./gate`;
- about 50 Claude Code UI instructions: Shift+Tab, Esc, `/clear`, `/rewind`, `/status`, `/model`, `/reload-skills`, and the slash forms for skills;
- about 25 model names;
- about 45 mentions of `.claude/` paths and `CLAUDE.md`.

Facilitator docs have more. `docs/`, `BUILD-SPEC.md` and `DECISIONS.md` have about 400, which stay.

**One rename is code-coupled:** Explorer's Level 2 `TESTS.md` heading `## Claude's plan` and its `(Claude writes it here)` placeholder are looked up by `exploretool/gates.py:381-386`. They are also used by the self-test (`selftest/run.py:403`) and its populated fixture (`selftest/solution/TESTS.md:9`).

## 3. Verified facts this design relies on

Claude Code (docs checked 2026-10-16, installed 2.1.301; <https://code.claude.com/docs/en/memory>):

- Claude Code reads `AGENTS.md` (v2.1.277+) **only when no `CLAUDE.md` exists** in the working directory or above it.
- A `CLAUDE.md` whose first line is `@AGENTS.md` imports it, then adds anything below. This is the documented bridge, and it never loads `AGENTS.md` twice.
- Claude Code does **not** read `.agents/skills/` or `.agents/agents/`; it reads `.claude/skills/` and `.claude/agents/`.
- `CLAUDECODE=1` is still set in tool shells.

Other harnesses (official docs read 2026-10-16 by a research subagent and the Codex reviewer; **not tested here**). Locally installed: Codex CLI 0.160.0, Copilot CLI 1.0.91, OpenCode 1.18.34, Qwen Code 0.24.7. Cursor and Gemini CLI are not installed.

| | Reads `.claude/skills/` | Plan or ask mode | Imports `.claude/settings.json` hooks |
|---|---|---|---|
| Codex CLI | no (`.agents/skills`) | `/plan` | no (has its own hooks) |
| Cursor | yes | Shift+Tab | **yes**, on by default, with tool-name translation |
| Copilot CLI | yes | Shift+Tab | **yes** |
| Copilot in VS Code | yes | Plan agent | only with `chat.useClaudeHooks` |
| Antigravity | no (`.agents/skills`) | yes (unconfirmed) | no |
| OpenCode | yes | `plan` agent | no |

All six read `AGENTS.md` (VS Code Copilot with a setting). Two consequences:

- `AGENTS.md` plus a `CLAUDE.md` import reaches every harness listed.
- Cursor and Copilot CLI may **run our Claude hooks**. The outcome is unknown: the hooks may work, may block every call, or may silently do nothing.
  - The guard expects Claude's tool names and fields (`guard.py:73`).
  - Our hooks use the exec form (`"command": "python3", "args": [...]`, `settings.json:74`).
  - Copilot documents `args` for its `exec` field and treats `command` as a shell fallback.

  This is a credible risk, not a demonstrated failure. It is settled by the Copilot smoke test (§7). Cursor stays "documented, untested".

## 4. Design

### 4.1 One instruction file: `AGENTS.md`, with a thin `CLAUDE.md`

**`AGENTS.md`.** Rename each `exercises/<name>/workshop/CLAUDE.workshop.md` to `AGENTS.workshop.md`, and have the build write it to `dist/<name>/AGENTS.md`.

- Its content becomes harness-neutral (§4.3). It keeps the full standing rules, the levels and the "Never" list, which is the fallback for every hook.
- Two small generic changes:
  - **Reading `.claude/`.** The "Never read" line keeps `.claude/`, with one exception: "except a shipped skill's `SKILL.md` when a prompt names that skill". Without this exception, `OTHER-AGENTS.md`'s skill fallback would contradict the rules. Claude Code's stricter rule is in its own section (below), and its guard still denies the read.
  - **Level changes.** ~~"If no PERSONA block arrives ..., run `./gate status` and `./gate brief` ..."~~ Dropped in implementation review: Claude Code's own subagents (the forked review, the reviewer agent) read `AGENTS.md` and never get a PERSONA block, so the line changed the Claude path. `OTHER-AGENTS.md` asks the group to have the agent run `./gate brief` at the start and after each unlock instead (`./gate brief` shows `README.md` at Level 0).

**`CLAUDE.md`.** The build writes it from one shared template, `gatekit/agents/CLAUDE.md`. The `gatekit/agents/` folder sits outside `gatekit/templates/` because the build copies every file under `templates/` unconditionally (`build.py:125`).

```markdown
@AGENTS.md

## Claude Code

- The workshop starts on __MODEL_NAME__. You cannot reliably tell which model you are from the inside. If someone asks, say you cannot be sure, and that `/status` (or the status line) shows the model that is really running. Do not guess or argue.
- The current level and its rules also arrive with each prompt as a PERSONA block; follow it.
- When a prompt names a shipped skill, invoke it with the Skill tool. Never read `.claude/`, including the skills.
```

- These are the only Claude-specific lines, and every exercise shares them.
- The model paragraph keeps the existing "don't guess your model" behaviour (added after a facilitator incident; `docs/DECISIONS.md:122`). "Starts on" fits both Explorer (fixed model) and the exercises with power-ups.
- The Skill-tool line keeps `review-code` running as a forked subagent rather than being read inline, which would lose the fresh context. The guard still denies reading `.claude/` under Claude Code, so the `AGENTS.md` exception changes nothing there.

Add `AGENTS.md` and `OTHER-AGENTS.md` to `hooklib.FROZEN_FILES`; `CLAUDE.md` stays frozen.

The result is that Claude Code reads the same rules as now, plus the Claude section, and behaves as now. Every other harness reads `AGENTS.md`.

### 4.2 One page for other agents: `OTHER-AGENTS.md`

**How it ships.**

- One shared source, `gatekit/agents/OTHER-AGENTS.md`. The build copies it when the manifest says `"other_agents": true` (an optional boolean, default false; other types are rejected).
- A supporting exercise's participant `README.md` gains one line where it sets up the agent window: "Not using Claude Code? Read `OTHER-AGENTS.md` first." Nothing else in the participant content mentions other harnesses.
- A Claude-only exercise's README gets one line instead: "This exercise needs Claude Code."

**Content: one screen.** A short introduction, then the few exceptions:

> **Using another agent.** These exercises are built for Claude Code, which enforces the rules with hooks. Your agent gets the same rules from `AGENTS.md` but won't be held to them, so please keep to them; the gates still check the work. Before you start, ask your agent "What may you not do in this repo?" It should list the Never items from `AGENTS.md`. Use a fast, capable mid-tier coding model: the timings were set on Claude Sonnet.
>
> - **Plan (Level 0).** Discuss the plan in your agent's plan or ask mode, if it has one. Once you approve it, leave that mode and ask the agent to save and commit `PLAN.md` only, without starting the build.
> - **After each unlock.** Tell your agent the level has changed and ask it to run `./gate brief`.
> - **Skills.** They are in `.claude/skills/`. If your agent doesn't list them, ask it to read `.claude/skills/<name>/SKILL.md` and follow it.
> - **Review (Level 3).** The review needs fresh eyes. If your agent can't run the review skill in a fresh context, open a second, new session in this same folder and paste in: *"Read `.claude/skills/review-code/SKILL.md` and follow it to review the commits since the start tag against `PLAN.md` and `README.md`: three to five findings, ranked. Don't edit anything."* Paste its findings back to your main session for `REVIEW.md`.
> - **Commits.** The gates count commits. If your agent can't commit, the Driver commits in the gate terminal.
> - **If every command is refused with a hook error** (Cursor, Copilot), turn off your agent's import of Claude Code hooks: [setting per harness]. The skills fallback above still works.
>
> | | Plan mode | Stop |
> |---|---|---|
> | Codex, Cursor, Copilot, Antigravity, OpenCode rows from §3 | | |

The last bullet and its per-harness setting names depend on §7. The review prompt carries the scope and count that Claude Code's Level 3 persona passes to the forked skill, and that the brief's prompt leaves out. Use the same folder so the reviewer sees the current files, and a new session so it doesn't carry the author's conversation history. The native skill folders per harness belong in the take-home `skills/README.md` (§4.4), not here.

### 4.3 Neutral wording, everywhere participants and facilitators read

This applies to every exercise, because the wording is shared style and some strings come from `gatekit`.

**Naming the agent.**

- "Claude" becomes "the agent" where it means the assistant: "ask the agent to commit", "decisions the agent made", "the agent's plan", "Agent window (large)".
- Use judgement: "your agent" is fine where it reads better.
- Keep "Claude Code" where it names the recommended product, as in the facilitator setup steps.

**UI keys and commands.** Use a general phrase with the Claude Code form in brackets, once per place:

- "Make sure the agent is out of plan mode (Shift+Tab in Claude Code)";
- "the Driver stops it (Esc in Claude Code)";
- "start a fresh session (`/clear` in Claude Code)".

**Models.**

- The exact Claude model lives in `CLAUDE.md` (§4.1). Participant text names it in general terms.
- Keep model-specific observations accurate rather than sweeping. The Speed Run "Haiku will want to optimise" stays as written, because that exercise is Claude-only and the line describes Haiku.

**Persona files** (`levels/*/persona.txt`).

- Same renames.
- The Skill-tool sentence becomes "When a prompt names a shipped skill, use it". The Claude-specific instruction now lives in `CLAUDE.md`.
- Personas keep their deliberate repetition of the standing rules (`docs/DECISIONS.md:422`).

**`gatekit` strings.**

- `cli.py:457`: "Switch with /model in Claude Code."
- `tty.py:31`: "This shell was started by your agent; open a fresh Terminal window for the gate."
- `preflight:187`: "Open your agent in this folder. In Claude Code, accept the workspace trust dialog so the hooks load."

**The README's commit rule** (`level0/README.md:80`): "All code changes, and all commits, go through the agent" stays. `OTHER-AGENTS.md` carries the one exception.

**The code-coupled heading.** In one change, rename `## Claude's plan` to `## The agent's plan` and `(Claude writes it here)` to `(the agent writes it here)`. The change covers:

- `levels/2/TESTS.md` and `gates.py:381-386`;
- the Level 2 brief, persona and hints;
- the manifest reflection prompts;
- `selftest/run.py:403` and `selftest/solution/TESTS.md:9`.

### 4.4 Skills

Keep one location: `.claude/skills/`.

- Copilot, Cursor and OpenCode read it natively.
- For Codex and Antigravity, the fallback is to read the `SKILL.md` directly, which §4.1's exception allows.
- No copy in `.agents/skills/`: one shipped copy is enough, and a second copy confuses participants.
- The guard needs no change.

If a participant turns off Cursor's third-party import, which may also hide imported skills, the read-the-file fallback still works.

Take-home material:

- **`skills/README.md`:**
  - The install section becomes a small table of skill folders per harness: `.claude/skills/` for Claude Code, Cursor, Copilot and OpenCode; `.agents/skills/` for Codex and Antigravity; plus the user-level equivalents.
  - The slash forms become "name the skill in your prompt (in Claude Code you can also type `/plan-code`)".
  - The Stop-hook example is labelled "Claude Code example".
- **`skills/plan-code/SKILL.md`:** read "the project's agent instructions (`AGENTS.md`, or `CLAUDE.md` if there is none)". This keeps other harnesses from pulling in Claude-specific lines.
- **`skills/style-code/SKILL.md`:**
  - "`CLAUDE.md`" becomes "the project's agent instructions file".
  - The slash-command line becomes "or ask for a style audit of the changed files".
- **`skills/review-code/SKILL.md`:** keep `context: fork` and `background: false`. Other harnesses ignore unknown frontmatter, and the body is already neutral.
- **`PLAYBOOK.md`:** same treatment as the briefs (§4.3). "Put the project's facts in `AGENTS.md`" replaces the `CLAUDE.md` and `/init` advice, followed by "(Claude Code: a `CLAUDE.md` that imports it; `/init` drafts one)".

### 4.5 Hooks, settings and model lock: unchanged

The guard, persona hook, model check, model lock, plan-mode default and permission denies stay exactly as they are. We do not port them, and we do not change the shared hook syntax to suit another harness. The only exception would be a fix that the §7 test shows to be tiny and to leave Claude Code's behaviour unchanged. If imported hooks misbehave in Copilot or Cursor, the answer is the opt-out line in `OTHER-AGENTS.md`. The written rules in `AGENTS.md` are the fallback. Manifests keep their `models`, which only Claude Code enforces.

### 4.6 Which exercises support other agents

- **Explorer: supported** (`"other_agents": true`).
  - The rules are all in `AGENTS.md`.
  - `OTHER-AGENTS.md` covers the plan-mode transition, the fresh review and commits.
  - The Level 1 question is a teaching moment rather than a secret.
  - The gates still check the real work: the tool runs, the tests pass, the commits exist, and `PLAN`, `TESTS` and `REVIEW` have content.
- **TDD Ladder: Claude Code only.** The literal-versus-coach persona, the Haiku lesson and the per-phase context are the exercise, and all of them arrive by hook.
- **Speed Run: Claude Code only.** It is a race between groups, and the Haiku lesson is central.

Both Claude-only exercises still get the shared changes (`AGENTS.md` with a `CLAUDE.md` import, neutral wording, `gatekit` strings), so the core stays one design.

### 4.7 Facilitator material

**Walkthroughs.** Each keeps its Claude Code setup steps, the recommended path, and gains one short subsection, "Groups on other agents".

- **Supporting exercise:**
  - what is lost: hooks, persona injection, model lock, the plan-mode default, and the fork;
  - `OTHER-AGENTS.md` covers the participant side;
  - the timings are uncalibrated;
  - which harnesses were rehearsed.
- **Claude-only exercise:** it needs Claude Code.

**Top-level `README.md`.** The "Run the workshop" checklist gains one line: groups bringing their own agent can do Explorer.

**`gatekit/README.md`:**

- Document the `AGENTS.md`/`CLAUDE.md` split, `gatekit/agents/` and the `other_agents` key.
- Correct §11. Where a check prints a fixed success line, the crypto gates stop casual reading, not a determined agent. For Explorer the packs hold nothing secret, so that is acceptable.

**Builder instructions.** The top-level `CLAUDE.md` says the participant file is `workshop/CLAUDE.workshop.md` (line 25). Update it to `AGENTS.workshop.md`.

## 5. Change list

### Required (structure and code)

1. `tools/build.py`:
   - write `AGENTS.workshop.md` to `AGENTS.md`;
   - render `CLAUDE.md` from `gatekit/agents/CLAUDE.md`, with `__MODEL_NAME__` set to the manifest's default model, capitalised (`Sonnet`, `Haiku`);
   - copy `gatekit/agents/OTHER-AGENTS.md` when `other_agents` is true.
2. `gatekit/agents/CLAUDE.md` and `gatekit/agents/OTHER-AGENTS.md`: new.
3. `gatekit/gatekit/manifest.py`: accept the optional boolean `other_agents`; reject other types.
4. `gatekit/gatekit/hooklib.py`: add `AGENTS.md` and `OTHER-AGENTS.md` to `FROZEN_FILES`.
5. `exercises/*/workshop/CLAUDE.workshop.md` and the build-test fixture `gatekit/tests/fixture_exercise/workshop/CLAUDE.workshop.md` → `AGENTS.workshop.md` (git mv). Reword per §4.3, add the two lines in §4.1, and drop the lines now in the `CLAUDE.md` template ("Which model am I?", the Skill-tool line, "injected with each prompt as a PERSONA block").
6. The Explorer `TESTS.md` heading, everywhere listed in §4.3, in one change.
7. `exercises/explorer/manifest.json`: `"other_agents": true`; reword the reflection prompts.
8. Tests:
   - `gatekit/tests/test_build.py`:
     - `AGENTS.md` is written;
     - `CLAUDE.md` starts with `@AGENTS.md` and names the model;
     - `OTHER-AGENTS.md` ships for `true` and not for `false` or a missing key.
   - `gatekit` manifest tests: a non-boolean `other_agents` is rejected.
   - `test_hooks.py`: `AGENTS.md` and `OTHER-AGENTS.md` are frozen.
   - Explorer self-test: the renamed heading and fixture; the shipped files list.
   - Preflight checks that name the instruction file.

### Flexible (wording only)

9. Participant content for all three exercises: `level0/README.md`, `LOG.md`, `PLAYBOOK.md`, `levels/*/BRIEF.md`, `hints.json`, `persona.txt`, the `guard.json` messages, and the strings printed by `./gate` and `./tdd` from the exercise tools.
10. `gatekit` printed strings (§4.3).
11. `skills/` (§4.4).
12. Facilitator material and the builder `CLAUDE.md` (§4.7).
13. `docs/DECISIONS.md`: one entry recording this design, the verified facts in §3 and what was rehearsed.

## 6. Considered and not doing

| Idea | Why not |
|---|---|
| Port the guard to Codex, Cursor, Copilot, Antigravity or OpenCode | Five schemas, several fail-open defaults, and little benefit in a cooperative workshop. The written rules are the fallback. |
| Change the shared hook syntax to suit Cursor or Copilot | Risks the Claude path. Use the opt-out line unless §7 finds a tiny, behaviour-preserving fix. |
| A git-diff check in every gate that changed files match the level's allowed paths | It would back up the guard for any harness, but adds false-failure risk and code to a trust-based tool. Revisit only if needed. |
| `./gate context` printing the persona for agents without the hook | `AGENTS.md` carries the level rules, `BRIEF.md` names the level, and `OTHER-AGENTS.md` carries the one piece the persona added (the review prompt). |
| Copy skills to `.agents/skills/` too | One shipped copy is enough; a second confuses. |
| More environment markers in `tty.py` | Names unverified. The "Never run `./gate unlock`" rule is the fallback. |
| Ask the reflection question before saving the unlock (`cli.py:328`) | Out of scope here. Advance-then-reflect also affects interrupted human sessions, so it belongs in a separate `gatekit` change if wanted. |
| Per-harness notes in briefs or READMEs | Bloat for the majority. They go in `OTHER-AGENTS.md`. |
| Move skills to a neutral folder | Claude Code reads only `.claude/skills/`. |

## 7. Verification plan

A short acceptance checklist, not a test framework.

1. **Receipts.** The `gatekit` unit tests on Python 3.14 and 3.9; the three self-tests; ruff. Same receipts as `PROGRESS.md`.
2. **Claude Code regression.**
   - In Explorer:
     - `/memory` shows `CLAUDE.md` and the imported `AGENTS.md`;
     - the persona block arrives, and plan mode is on;
     - an allowed and a denied action behave as before;
     - "Use the review-code skill ..." still forks;
     - "Which model are you?" gets the don't-guess answer.
   - In TDD Ladder or Speed Run: the starting model and a facilitator power-up still work.
3. **Codex, one complete Explorer path** (installed; headless where possible, with the gate driven from a terminal):
   - the rules load ("What may you not do in this repo?");
   - the plan is discussed in `/plan`, then the agent leaves it, saves and commits `PLAN.md`;
   - one unlock, then a reread of `BRIEF.md`;
   - a skill is read from its file;
   - the fresh-session review prompt from `OTHER-AGENTS.md` works;
   - the commit works (or the human fallback is needed).
4. **Copilot CLI** (installed), the rules and hooks check:
   - do our `.claude/settings.json` hooks load, and do they work, block everything, or do nothing?
   - The answer decides the opt-out bullet in `OTHER-AGENTS.md` and its setting names.
5. **Cursor** is not installed here. Label it "documented, untested" in `DECISIONS.md` and the walkthrough.

## 8. Decisions

**Defaults adopted** (from the owner's direction or agreed in review; change any of them by saying so):

- `AGENTS.md` is the canonical instruction file, and `CLAUDE.md` is a thin import plus a shared Claude Code section.
- Content for other agents lives only in `OTHER-AGENTS.md`, which ships with Explorer alone. The other exercises say in one line that they need Claude Code.
- Hooks are not ported, and the hook syntax is not changed. The written rules are the fallback, with an opt-out line if imported hooks misbehave.
- "The agent" is the generic name, with "Claude Code" kept where it names the product.
- Skills stay only in `.claude/skills/`, with a read-the-file fallback.
- Cursor is "documented, untested".

**Open for the owner:**

1. **When to implement relative to the upcoming workshop.** The change is mostly wording, plus a small build change, and every self-test reruns. It does touch Explorer's calibrated participant text and the Level 2 gate heading.
   - **Before the workshop:** implement, run the receipts, then do the Explorer calibration run (already pending, `PROGRESS.md` item 2) on the new text.
   - **After the workshop:** run the current build unchanged, and do this afterwards.

   Recommendation: before, if the calibration run has not happened yet, because one run then covers both. Otherwise after.
2. **Rehearsal scope.** §7 asks for one complete Codex path and a Copilot hooks check, about an hour together. Cutting it to the Copilot hooks check alone would still catch the one failure that would hurt participants: every command refused.

## 9. Review log

**Round 1.** Codex gpt-6.1-sol, high effort, read-only. Verdict: APPROVE WITH CHANGES. It endorsed the architecture: `AGENTS.md` plus a thin `CLAUDE.md`, one `OTHER-AGENTS.md`, one skills location, Explorer-only support, and no hook ports. All six findings were checked against the repo and accepted:

1. **The skill fallback contradicted "never read `.claude/`".** Fixed with a narrow exception in `AGENTS.md`; `plan-code` now prefers `AGENTS.md`.
2. **Imported hooks in Cursor and Copilot.** The outcome is unknown, and silent non-enforcement is also possible. "Only Claude Code runs them" was inaccurate. Now: the Copilot test settles it, Cursor is labelled untested, the answer is an opt-out rather than a syntax change, and the opt-out also leaves the skills fallback working.
3. **"Plan mode until committed" deadlocks.** Plan in the mode, then leave it to save and commit `PLAN.md` only.
4. **The review choreography lost the persona's arguments** (scope, `README.md`, three to five findings). `OTHER-AGENTS.md` now carries the exact fresh-session prompt, plus "reread `BRIEF.md` after each unlock".
5. **The Claude addendum dropped the don't-guess-your-model behaviour.** Restored in the shared template as "starts on", which also covers power-ups.
6. **Verification exercised discovery, not the workflow.** Fixed:
   - the build copies `templates/` unconditionally, so the new templates moved to `gatekit/agents/`;
   - the self-test fixture and the builder `CLAUDE.md` were added to the change list;
   - the manifest flag validation is tested;
   - there is a full Codex path, and the Claude regression covers power-ups.

Also taken from round 1:

- the `OTHER-AGENTS.md` outline is cut to one screen;
- the reflection-order rationale is corrected;
- "change the hook syntax" is moved to §6;
- the Speed Run Haiku line stays accurate rather than being genericised.

**Round 2.** Same Codex session. Verdict: APPROVE WITH CHANGES, "ready for implementation after the small corrections", with no owner decisions. Round-1 findings 2 to 5 were resolved, and 1 and 6 partly. Five small corrections were checked and applied:

1. The skill-read exception no longer asks the agent to judge its harness's capabilities: it now applies "when a prompt names that skill".
2. The no-PERSONA instruction uses `./gate brief`, which shows `README.md` at Level 0, instead of assuming `BRIEF.md`.
3. The build-test fixture `CLAUDE.workshop.md` was added to the rename.
4. The fresh-session explanation was corrected: same folder for the files, new session for no history.
5. The skills column was dropped from the `OTHER-AGENTS.md` table, and the regression checks are now scoped per exercise.

Status: **agreed with the reviewer and ready for the owner to read**. The timing of implementation (§8) is the owner's call.

**Implementation review.** Independent panel on the implemented change: Codex gpt-6.1-sol and Claude Fable 5.1, high effort, read-only. Both said APPROVE WITH CHANGES and found no serious issues. Every finding was checked and accepted:

- **The no-PERSONA line (medium).** It was read by Claude Code's subagents, so it moved to `OTHER-AGENTS.md`.
- **The `SKILL.md` read exception.** Dropped from the TDD Ladder and Speed Run, which ship no skills.
- **Playbook recovery keys and set-up tip.** The recovery keys are now all qualified for Claude Code. The `AGENTS.md` tip now says Claude Code reads it when there is no `CLAUDE.md`, replacing an inaccurate import suggestion.
- **Skills install table.** It no longer implies the user-level folder for Cursor, Copilot and OpenCode.
- **Level 2 hint.** It now quotes the heading.
- **Explorer facilitator walkthrough.** Its narrative now uses "the agent" (the read-aloud script included). The Claude Code set-up and calibration notes keep the product name. "every harness reads" became "these harnesses read". The Claude-only exercises' walkthroughs keep "Claude", because they describe a Claude Code run.
