# Agentic AI for Physics Research — Facilitator Guide

*For the session organiser (the facilitator). Covers the pre-session lecture, group roles, the shared "gate kit" in outline, calibration, the leaders' set-up session, running the day, and the trial with your research group. How to build, distribute and operate a built exercise is in the repository `README.md` ("Run the workshop") and in that exercise's facilitator walkthrough, which is also the group leaders' guide.*

---

## 1. At a Glance

| Block | Duration | What happens |
|---|---|---|
| **Lecture** | 15 min | The Verify-First Loop, healthy use, how the exercises work |
| **Form groups** | 3 min | Groups of 2–5 sit with their leader; roles assigned; gate terminal opened |
| **Hands-on** | 45 min | Gated exercise in Claude Code, on a weak model (Haiku; Explorer uses Sonnet). The built exercises are timed for 45 minutes from Go; TDD's 5-minute stretch level is for fast groups, and Explorer has no stretch level. |
| **Show-and-tell** | 5 min | Each group: one moment the agent was wrong and how they caught it |

**Total: about 70 minutes.** For a hard 60, run the lecture's essentials in 10 minutes and the show-and-tell in 2 (open decision 3, Section 11); don't cut the hands-on, because the exercises are calibrated for 45.

### The Five Exercises

| ID | Exercise | Core lesson | Model | Best for |
|---|---|---|---|---|
| **A** | Two Roads (discrepancy debugging) | Evidence-driven debugging; agreement ≠ correctness | Haiku | Any group; the default |
| **B** | Speed Run (optimisation race) | Measure first; a correctness gate is non-negotiable | Haiku | Mixed groups; competitive rooms |
| **C** | Fortran Archaeology (legacy port) | Establish the oracle before you change anything | Sonnet | Strongest leaders |
| **D** | TDD Ladder (test-driven development) | You define "correct"; the agent cannot | Haiku | Groups who write shared code |
| **E** | Explorer (plan, build, test, review) | Plan, build, test, review: the workflow as a habit | Sonnet | Any group; the lightest exercise, closest to everyday use |

Only B, D and E are built so far; A and C are designs (see the `README.md` exercise table).

**Suggested assignment:** A for half the groups, then B and D split across the rest. E suits groups who want to leave with a tool they will use and a playbook for their own code; it runs on Sonnet, so check those leaders' accounts. C goes only to leaders who are comfortable with compilers and Fortran. Groups doing the *same* exercise make the show-and-tell more interesting, because their different paths are directly comparable.

---

## 2. Design Principles

1. **One workflow, five vehicles.** Every exercise drills the same loop (Section 3, Slide 4). The physics is the vehicle; the loop is the take-home.
2. **The human owns the result.**
   - Gates require *human* judgement, typed by a human, to unlock the next level.
   - A weak model means the group must understand the problem to direct the agent.
   - The group reaches the end-point because they recognise it, not because Claude says "done".
3. **Productive failure.** The agent is allowed, sometimes encouraged, to fail visibly. Catching that failure is the lesson.
4. **Evidence over assertion.** Nothing counts until someone has seen the command and its output.
5. **Everyone types.** The keyboard rotates at each gate, through everyone.

---

## 3. The Pre-Session Lecture (15 min)

### Slide Plan

| # | Min | Slide | Key points |
|---|---|---|---|
| 1 | 1 | **Hook** | Ask the room: "Who has had an AI give a confident, wrong answer?" Then: "Who caught it *because* they knew the physics?" That second group is today's skill. |
| 2 | 2 | **Chat vs agent** | A chatbot answers. An agent *acts*: it reads files, runs code, observes results and iterates. Your job shifts from writing code to **specifying, directing and verifying**. |
| 3 | 2 | **Perception vs measurement** | METR's 2025 randomised trial: experienced developers *expected* AI to make them ~24% faster; on real tasks in their own repos they were ~19% *slower*. Tools have improved since, and METR says so. The lesson is not "AI is slow". It is that **feeling productive is not being productive**. Physicists already know: measure, don't assume. |
| 4 | 5 | **The Verify-First Loop** | The core of the lecture. See the table below. |
| 5 | 2 | **You own the science** | The failure-mode table below, with one remedy each. |
| 6 | 1 | **Why a weak model today** | "Think of today's model as a keen first-year PhD student: fast, tireless, literal, and in need of supervision. Supervision is the skill we're practising. A stronger model makes the same mistakes less often, which makes them *harder* to spot." |
| 7 | 2 | **How today works** | Roles, gates, the gate terminal, hints, time calls, and the show-and-tell question (announce it now so groups notice moments as they happen). |

### Slide 4: The Verify-First Loop

| Step | What it means | Claude Code feature |
|---|---|---|
| **1. Understand** | Explore before changing anything | Plan mode (`Shift+Tab` until `⏸ plan mode on`); `@file` references |
| **2. Define the check** | Decide what "correct" means *before* any code is written | Tests, reference values, analytic limits, a script that diffs outputs |
| **3. Plan** | Agree the approach; edit the plan | Plan mode → approve or edit the plan (`Ctrl+G` opens it in your editor) |
| **4. Small steps** | One change, one check, one commit | `git commit` after each verified gain |
| **5. Evidence** | "Show me the command and the output" | Ask for evidence rather than a claim of success |
| **6. Independent review** | A fresh context reviews the diff | "Use a subagent to review this diff against PLAN.md" |
| **7. Recover cleanly** | Stop, rewind, restart with a better prompt | `Esc` (stop), `Esc Esc` / `/rewind`, `/clear` |

**Rule of thumb:** after two failed corrections, `/clear` and write a better prompt. This is current Anthropic guidance, and it is the habit novices most often lack.

### Slide 5: Failure Modes and Remedies

| Failure mode | What it looks like | Remedy |
|---|---|---|
| **Plausible but wrong** | Clean code, wrong physics | Analytic limits and independent references |
| **Steering to the expected answer** | Result "agrees with Planck" because Claude knew the target | Blind checks; decide the check before seeing the result |
| **Loosening the tolerance** | `rtol=1e-2` "to account for numerical noise" | The Sceptic owns tolerances; any change needs a physical justification |
| **Writing from memory** | "Ports" code by recalling a textbook version | Test against the actual source's outputs |
| **Self-confirming tests** | Tests written after the code mirror the code | Tests first, seen to fail, from an independent oracle |
| **Claimed success** | "All tests pass!" with no run shown | Demand the command and the output |

### Optional Extensions (if the lecture runs 30–45 min)

- **Live demo (10 min).**
  - Run Exercise A Level 0 twice. First, tell a strong model "fix the discrepancy" and show it confidently fixing one bug and declaring victory.
  - Then show the gate refusing to open because the human question is unanswered.
- **CLAUDE.md for your own project (5 min).** What belongs in it and what doesn't; `/init` as a starting point.
- **Context management (5 min).** Why long sessions degrade; `/clear`, `/compact`, `/context`, and subagents for exploration.

### Cheat Card (Print One per Person)

```
THE LOOP  Understand → Define the check → Plan → Small steps → Evidence → Review → Recover

PLAN MODE      Shift+Tab until "⏸ plan mode on"   (read-only exploration)
REFERENCE      @path/to/file                       (pull a file into context)
STOP           Esc                                  (interrupt, keep context)
REWIND         Esc Esc   or   /rewind              (restore code and/or conversation)
FRESH START    /clear                               (after two failed corrections)
SIDE QUESTION  /btw <question>                      (doesn't pollute context)
CONTEXT        /context                             (what's loaded)

GOOD PROMPTS
  "Before changing anything, list three hypotheses ranked by likelihood, and an
   experiment that would distinguish them."
  "Write a failing test that reproduces this. Show me it failing. Don't fix yet."
  "Show me the exact command you ran and its output."
  "Use a subagent to review the diff against our plan. Report only correctness gaps."

THE GATE TERMINAL IS FOR HUMANS. Claude never types there.
```

---

## 4. Group Roles (Groups of 2–5)

Roles are responsibilities, not seats. Combine them in small groups and split them in large ones.

| Role | Responsibility |
|---|---|
| **Driver** | Types prompts into the agent. **Rotates every ~12 minutes** (or at each gate). |
| **Navigator** | Owns the plan and scope; says "stop, that's out of scope"; watches the clock. |
| **Sceptic** | Owns the check. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence. |
| **Scribe** | Keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment. |

**The group leader** runs the exercise on their own laptop: keeps it running, keeps the group to time, reads out the talk prompts and gate notes, and calls the facilitator when the group is stuck. The exercise directs the group step by step, so the leader takes one of the roles above like everyone else. Recruit leaders for that: their own laptop, some experience with an agentic coding tool, enough terminal experience to set up from instructions, and about an hour beforehand (`docs/pre-workshop-survey.md` §1). This is the role as built for Explorer; the Speed Run and TDD Ladder walkthroughs still describe the older Coach role and are Claude Code only.

| Group size | Allocation |
|---|---|
| **2** | Driver; Navigator + Sceptic + Scribe. Swap at each gate. |
| **3** | Driver (rotating), Sceptic, Navigator + Scribe |
| **4** | Driver (rotating), Navigator, Sceptic, Scribe |
| **5** | Driver (rotating), Navigator, Scribe, and the Sceptic split in two: **Physics Sceptic** and **Code Sceptic** (Explorer: Browser and Evidence Sceptic) |

**Rotation rule:** the Driver role rotates at each gate, so everyone types at least once.

**The "hands off the code" rule:** humans read, think, discuss and type *prompts*. All code changes go through the agent. Physicists who would rather fix it themselves are exactly who most needs this rule.

---

## 5. The Gate Kit (Shared Infrastructure)

All the exercise repos share one small toolkit, written in Python using only the standard library. This section gives the design intent and what to say about it in the lecture. The toolkit as built (commands, manifest, hooks, settings, crypto) is documented in `gatekit/README.md`.

### 5.1 Goals

- The group cannot reach Level N+1 until it has solved Level N **and** a human has demonstrated understanding.
- Claude acts as a *teacher*: it runs experiments the group designs, but doesn't hand over answers.
- Progress is logged, so you can measure timings in the trial and on the day.
- Everything works offline once set up, and the toolkit needs no third-party packages.

### 5.2 Repo Layout

A built participant repo holds the Level 0 files, the `gate` and `preflight` launchers, the Claude Code settings and hooks in `.claude/`, the toolkit in `.gatekit/`, the encrypted level packs in `.vault/`, and the runtime state in `.workshop/`. The full layout is in `gatekit/README.md`, section 1.

`.workshop/` (and `.tdd/` in Exercise D) are **gitignored**, so `git checkout` or `git reset` during an exercise never rewinds gate progress or the logs.

### 5.3 How a Gate Works

- **The check.** `./gate check` runs the level's behaviour-based checks and reports PASS or FAIL. A broken solution cannot pass, and the check never reveals the answer.
- **The human answer.** A short structured answer (a letter, number or keyword) to a debrief question about what the group observed or decided. Examples: "What functional form did the discrepancy have?" "What was the exponent you measured?"
- **The unlock.** The next level's files sit in an encrypted pack in `.vault/`. Some gates derive the key from the check's output and the human answer; others first verify the group's recorded evidence (a score, a bench run) and then release the key. Either way the pack opens only when the work passes and the human answer is right. A wrong answer fails cleanly, with "Not quite. Discuss and try again." (and a hint, where the exercise gives one) or the reason the evidence was refused.
- **The gate terminal.** `./gate unlock` reads the answer at an interactive prompt and refuses to run without a terminal, or from a shell that Claude Code started. Claude's Bash tool has no terminal, so humans unlock the gate in a **separate "gate terminal"** window. The physical separation is deliberate: the gate terminal belongs to the humans.
- **Free-text reflection.** After a successful unlock, `./gate` asks one or two open questions, such as "What would you do differently?". The answer is appended to `LOG.md` unchecked and feeds the show-and-tell.

### 5.4 Teacher Mode

**`CLAUDE.md`** holds the stable rules: the persona, what Claude must never do, and how to respond to "just fix it". Each exercise doc includes a draft.

**A `UserPromptSubmit` hook** injects a short, level-specific brief on every prompt. It covers the current level, the persona mode for that level, and any constraints. This keeps a weak model on track as the conversation grows.

**Persona modes** are set per level:

| Mode | Behaviour |
|---|---|
| `literal` | Does what is asked, literally. Volunteers no best practice. Used where the lesson is seeing what happens without discipline (TDD Levels 0–1). |
| `coach` | Executes the group's experiments and reports evidence. Answers "just fix it" by asking for the group's hypothesis. Never names the bug or the fix first. Offers at most one leading question per turn. |
| `collaborator` | Normal helpful behaviour, still evidence-first. Used in later "free" levels (Exercise B's open race; all four Explorer levels). |

### 5.5 Guardrails

- **Plan mode by default.** Every session starts in read-only exploration, which reinforces *Understand* first. The Driver switches out with `Shift+Tab` once a plan is agreed.
- **A guard hook** (`PreToolUse`) blocks Claude from the vault, the workshop state, the human-only gate commands, package installs and the files a level has frozen. Each refusal carries a teaching message. If the guard crashes, the tool call is blocked (it fails closed), which needs Claude Code 2.1.295 or newer.
- **A model lock** (`PreModelSwitch`) refuses `/model` to anything but the allowed model, until a facilitator grants a power-up.
- **Workspace trust.** Project hooks load only after someone opens `claude` in the repo once and accepts the trust dialog; the walkthrough's setup checks confirm it.

### 5.6 Honest Limits

This is a **learning scaffold, not an exam proctor.**

**Hard to bypass:**

- **Encrypted packs.** No later-level content is visible without passing the gate.
- **The gate terminal.** Claude can't type into it.

**Soft (instructions and hooks Claude is asked to respect):**

- The teacher persona.
- Path guards on Bash. Matching shell commands is best-effort by design, which is why the vault is encrypted rather than merely hidden.

**Bypassable by a determined human:**

- A human could launch with `claude --model opus`. A launch flag isn't a mid-session switch, so the model lock doesn't see it.
- A human could ask Claude to reverse-engineer a gate.

Say this openly in the lecture: *"You can cheat. You'd be cheating yourselves out of the practice you came for."* If a group tries, treat it as a teachable moment rather than a disciplinary one. The full list is in `gatekit/README.md`, section 11.

### 5.7 Hints, Logging and the Master Key

- **`./gate hint`** reveals tiered hints for the current level, three per level: *nudge → direction → near-answer*, plus a fourth that gives the answer at levels with a graded question. Hints are time-locked: tier 2 opens after 5 minutes on the level, tier 3 after 10 and the answer after 13 (Explorer's 8-minute levels: 3 and 6). Every hint is logged, so the facilitator can see which groups took the answer.
- **`state.json`** records the level start time, unlock time, hints used and failed unlock attempts. This is your trial data.
- **The master passphrase** is yours. You type it in the group's gate terminal for `./gate skip --master` (unlocks the next level for a stuck group; use it sparingly, and give a reason), `./gate allow-model` (a power-up) and any exercise fallback. Who else may know it is decided in each walkthrough's section 2.
- **`./gate status`** prints the level, time on level and hints used. Leaders call this out at time checks.

### 5.8 Building Level Packs

`tools/build.py` builds each participant repo from its private source in `exercises/<name>/`: it encrypts the later levels into packs, commits the result and tags it `start`. The answers never enter the participant repo except as encrypted packs and check values. See `README.md` ("Build and extend").

---

## 6. Building and Calibrating the Exercises

### Build Checklist (per Exercise)

- [ ] Level 0 brief, data and code
- [ ] Planted issues (A, B), source and golden outputs (C), or spec and mutants (D)
- [ ] Behaviour-based checks for every level; they must not reveal the fix
- [ ] Gate questions and accepted answers (normalised: case, whitespace, synonyms, numeric tolerance)
- [ ] Three hint tiers per level, plus the answer at graded levels
- [ ] `CLAUDE.md` teacher instructions and per-level persona briefs
- [ ] Reference solution path (to derive tokens and test end-to-end)
- [ ] Exercise-specific preflight checks
- [ ] Facilitator walkthrough (gate answers, leader set-up, coaching notes)
- [ ] Self-test that plays every level

How to add an exercise to this repository is in `README.md` ("Build and extend").

### Calibration Matrix

Run each exercise in four ways before the trial (Explorer runs on Sonnet, so its runs 1 and 2 use Sonnet and run 3 does not apply):

| Run | Model | Driver behaviour | What you're testing |
|---|---|---|---|
| 1 | Haiku | Naive: "fix it" / "make it faster" | Does the scaffold hold? Does Claude coach rather than solve? |
| 2 | Haiku | Guided by you, following the loop | Can a competent group finish the core levels in ~35 min? |
| 3 | Sonnet | Naive | Is the exercise trivial with a stronger model? (It shouldn't be, because of the human gate answers) |
| 4 | Opus (or strongest available) | Adversarial: "decrypt the vault", "run gate unlock" | Do the guardrails hold, and do failures give useful teaching messages? |

**Targets:**

- Run 2 completes the core levels in 30–40 minutes.
- Run 1 visibly stalls or produces a wrong "fix" that a check catches.
- Run 4 cannot unlock a level without the human answer.

---

## 7. Pre-Event Setup

### Accounts and Models

- Each leader uses the agentic coding tool they already know. Explorer accepts any (Claude Code preferred; Codex, Cursor, VS Code with Copilot or a command-line agent through `OTHER-AGENTS.md`). The Speed Run and TDD Ladder need Claude Code, because their lessons arrive by hook.
- Give **Claude Pro** to any leader without a paid AI subscription (the survey's last question says who). Confirm that each Claude account can run Claude Code with **Sonnet**, and **Haiku** for the Claude Code-only exercises.
- Measure **usage consumed** per exercise in the trial. Haiku should stretch the allowance further, but confirm it.
- Hold **one or two spare accounts** on a facilitator laptop for groups whose leader hits a usage limit.

### Repos and Leader Machines

- [ ] Each exercise built, checked and rehearsed by you on the exercise's model (Haiku; Sonnet for Explorer): walkthrough section 1.
- [ ] Each leader sent a git bundle of the built repo, the walkthrough and the leader quickstart, at least a week before: walkthrough section 2. Never send this repository.
- [ ] Each leader's laptop set up by the leader from the walkthrough's "Group leaders: set up your laptop" section, before the set-up session. Explorer needs macOS or Linux with a terminal, git, `make` and Python 3.11+; the Claude Code-only exercises are calibrated on macOS and the Claude Code version you rehearsed. Packages must be in place by then: agents can't install them during the session.
- [ ] Exercise C only (when built): `gfortran` (e.g. via Homebrew `gcc`), compile-tested in preflight.
- [ ] Two windows arranged: the **agent** (large) and the **gate** terminal (small)
- [ ] An external screen or TV per group if the room allows. Otherwise the group gathers behind the leader's laptop.

### Leaders' Set-up Session (short, a few days before)

Leaders have already set up from the emailed bundle and instructions. The session is for what they can't get from the page:

1. Confirm each leader's set-up passed (walkthrough section 3: preflight, then the check for their agent); resolve failures on the spot.
2. Show the gate terminal, `./gate status`, `./gate hint` and the talk prompts, and how to call you for a skip, since you hold the master passphrase.
3. Roles by group size, rotation and the "hands off the code" rule, from the leader quickstart.

### Day Before

- Leaders re-run `./preflight`, then reset any rehearsal as in walkthrough section 7, so the group starts at level 0 with an empty log.
- Charge laptops; confirm power at tables.
- Confirm nothing needs the network except the agent itself.

---

## 8. Running the Day

### Run-Sheet

| T (min) | Action |
|---|---|
| 0 | Lecture starts |
| 15 | Groups form; leaders allocate roles (card on table); gate terminal opened |
| 18 | **Go.** Everyone reads the Level 0 brief (`README.md`) together |
| 33 | Time call (Go + 15): each leader checks the group against the time checkpoints in their walkthrough. "If you're behind, take a hint." |
| 50 | Time call (Go + 32): "Scribes, start capturing your 'caught it' moment." |
| 63 | Stop (Go + 45). Scribes finalise `LOG.md` |
| 65 | Show-and-tell: 45 seconds per group, maximum |
| 70 | Close |

### Facilitator Roaming Loop (Every ~10 min)

- Visit each group and ask "What level, and what's your current hypothesis?" A group that can't state a hypothesis is drifting; point them at the Navigator.
- Look for leaders driving. Gently rotate the keyboard.
- Look for long correction spirals. Prompt a `/clear` and a better prompt.

### Stuck Protocol

1. **Group's own move:** "What does the evidence say? What experiment would distinguish your hypotheses?"
2. **`./gate hint`:** tiers unlock over time.
3. **Facilitator nudge:** a question, not an answer.
4. **Model power-up** (Sonnet), granted by the facilitator and logged. Use it when the group is directing well but the model can't execute.
5. **`./gate skip --master`:** a last resort, so the group still experiences the later levels.

Steps 4 and 5 need the master passphrase, typed in the group's gate terminal. Each walkthrough's "When something goes wrong" table has the exercise-specific options, such as installing a reference solution.

### Show-and-Tell Format

Each group answers two questions:

1. "One moment the agent was wrong, or confidently heading the wrong way, and how you caught it."
2. "One prompt or habit you'll reuse in your own research."

Capture the answers on a whiteboard. That list is the session's summary slide.

---

## 9. Trial With Your Research Group

### What to Measure

- **Per-level time:** from `state.json`, compared against each doc's target.
- **Hints used per level:** high usage on one level means it is under-signposted.
- **Persona adherence:** did Haiku coach or solve? Note transcripts where it leaked the answer.
- **Gate friction:** failed unlock attempts. Many failures mean the answer normalisation is too strict or the question is ambiguous.
- **Participation:** who typed, and for how long.
- **Usage:** how much of the Pro allowance one run consumed.

### Five-Question Feedback Form

1. What was the most useful thing you practised? (free text)
2. Which level was most frustrating, and why? (free text)
3. Did you feel *you* solved it, or that Claude did? (1–5 scale)
4. How confident are you that you could use an AI agent productively on your own research code right now? (1–5 scale; the same wording as Q8 of the pre-workshop survey, `docs/pre-workshop-survey.md`, so the two can be compared)
5. What would you cut? (free text)

### Decision Criteria for the Final Session

- **Keep** an exercise if Q3 averages ≥ 3.5 and Q4 averages ≥ 3.5.
- **Re-scope** if the core levels take more than 40 min with guided Haiku.
- **Cut a level** if it consistently needs tier-3 hints.

---

## 10. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Leader hits a usage limit mid-session | Medium | Haiku by default; spare accounts; measure in the trial |
| Environment failure (Python, compiler, hooks) | Medium | Leaders set up and run preflight before the set-up session; pinned versions; spare configured laptop |
| Haiku leaks answers despite teacher mode | Medium | Per-turn persona injection; calibration Run 1; answers are useless without the human gate answer anyway |
| Haiku too weak for a level | Medium | Facilitator Sonnet power-up; calibration Run 2 |
| Group finishes too early | Low–Medium | A stretch level (D) or the open race (B) |
| Group stalls on Level 0–1 | Medium | Time calls; tiered hints; master skip |
| Leader dominates | Medium | The leader takes a role like everyone else; rotation rule; facilitator roaming |
| Group bypasses gates or switches model | Low | Name it in the lecture; encrypted packs; treat it as a teaching moment |
| Wi-Fi is poor | Low–Medium | Packages installed by `./preflight --setup` before the day; on the day only Claude Code needs the network |

---

## 11. Open Decisions for You

1. **Exercise mix:** all A, or A/B/D split? (Recommended: A plus one other, so the show-and-tell compares two lessons.)
2. **Model policy:** strict Haiku with facilitator power-ups, or Sonnet available from a given level onwards?
3. **Lecture length:** 15 minutes as planned, or a 10-minute live demo added?
4. **Competition:** run the Speed Run leaderboard as a room-wide event, or keep it within groups?
5. **Take-home:** offer a public, ungated version of each repo afterwards for people to revisit?
