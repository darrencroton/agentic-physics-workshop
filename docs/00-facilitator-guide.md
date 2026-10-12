# Agentic AI for Physics Research — Facilitator Guide

*For the session organiser. Covers the pre-session lecture, the shared "gate kit" that all four exercises use, setup, running the day, and the trial with your research group.*

---

## 1. At a Glance

| Block | Duration | What happens |
|---|---|---|
| **Lecture** | 15 min | The Verify-First Loop, healthy use, how the exercises work |
| **Form groups** | 3 min | Groups of 2–5 sit with their leader; roles assigned; gate terminal opened |
| **Hands-on** | 45–50 min | Gated exercise in Claude Code, on a weak model |
| **Show-and-tell** | 5 min | Each group: one moment the agent was wrong and how they caught it |

### The Four Exercises

| ID | Exercise | Core lesson | Model | Best for |
|---|---|---|---|---|
| **A** | Two Roads (discrepancy debugging) | Evidence-driven debugging; agreement ≠ correctness | Haiku | Any group; the default |
| **B** | Speed Run (optimisation race) | Measure first; a correctness gate is non-negotiable | Haiku | Mixed groups; competitive rooms |
| **C** | Fortran Archaeology (legacy port) | Establish the oracle before you change anything | Sonnet | Strongest leaders |
| **D** | TDD Ladder (test-driven development) | You define "correct"; the agent cannot | Haiku | Groups who write shared code |

**Suggested assignment:** A for half the groups, then B and D split across the rest. C goes only to leaders who are comfortable with compilers and Fortran. Groups doing the *same* exercise make the show-and-tell more interesting, because their different paths are directly comparable.

---

## 2. Design Principles

1. **One workflow, four vehicles.** Every exercise drills the same loop (Section 3.4). The physics is the vehicle; the loop is the take-home.
2. **The human owns the result.**
   - Gates require *human* judgement, typed by a human, to unlock the next level.
   - A weak model means the group must understand the problem to direct the agent.
   - The group reaches the end-point because they recognise it, not because Claude says "done".
3. **Productive failure.** The agent is allowed, sometimes encouraged, to fail visibly. Catching that failure is the lesson.
4. **Evidence over assertion.** Nothing counts until someone has seen the command and its output.
5. **Everyone types.** The keyboard rotates. The leader coaches rather than drives.

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
| **Driver** | Types prompts into Claude Code. **Rotates every ~12 minutes** (or at each gate). |
| **Navigator** | Owns the plan and scope; says "stop, that's out of scope"; watches the clock. |
| **Sceptic** | Owns the check. Nothing is committed and no gate is attempted until the Sceptic has seen the evidence. |
| **Scribe** | Keeps `LOG.md`: prompts that worked, prompts that failed, the "caught it" moment. |
| **Coach** | Always the leader. Asks questions rather than giving answers; steps in on tooling problems. |

| Group size | Allocation |
|---|---|
| **2** | Leader: Coach + Navigator. Other: Driver + Sceptic + Scribe. Swap Driver at each gate (the leader drives the gate attempts). |
| **3** | Driver (rotating), Sceptic, Coach + Navigator + Scribe |
| **4** | Driver (rotating), Navigator, Sceptic, Coach + Scribe |
| **5** | Driver (rotating), Navigator, Sceptic, Scribe, Coach. Optional: split Sceptic into **Physics Sceptic** and **Code Sceptic**. |

**Rotation rule:** the Driver role rotates through everyone except the leader, so every non-leader types at least once. The leader drives only if the group has two people or a technical problem needs fixing.

**The "hands off the code" rule:** humans read, think, discuss and type *prompts*. All code changes go through Claude. Physicists who would rather fix it themselves are exactly who most needs this rule.

---

## 5. The Gate Kit (Shared Infrastructure)

All four repos share one small toolkit, written in Python using only the standard library. Build it once and reuse it.

### 5.1 Goals

- The group cannot reach Level N+1 until it has solved Level N **and** a human has demonstrated understanding.
- Claude acts as a *teacher*: it runs experiments the group designs, but doesn't hand over answers.
- Progress is logged, so you can measure timings in the trial and on the day.
- Everything works offline and needs no third-party packages.

### 5.2 Repo Layout

```
exercise-repo/
├── CLAUDE.md                     # teacher instructions (always loaded)
├── README.md                     # Level 0 brief for humans
├── LOG.md                        # Scribe's log (template)
├── gate                          # CLI: status | check | unlock | hint (python3, stdlib)
├── .claude/
│   ├── settings.json             # model, permission mode, deny rules, hooks
│   └── hooks/
│       ├── teacher_context.py    # UserPromptSubmit: injects current level brief + persona
│       ├── guard.py              # PreToolUse: blocks .vault access, gate unlock, pip, etc.
│       └── model_lock.py         # PreModelSwitch: enforces the allowed model(s)
├── .workshop/
│   ├── state.json                # current level, timestamps, hints used (written by ./gate)
│   └── levels/                   # unlocked level briefs appear here
├── .vault/
│   ├── level1.pack               # encrypted level packs (brief, checks, data, hints)
│   ├── level2.pack
│   └── ...
└── src/, tests/, data/           # exercise content
```

`.workshop/` (and `.tdd/` in Exercise D) are **gitignored**, so `git checkout` or `git reset` during an exercise never rewinds gate progress or the logs.

### 5.3 How a Gate Works

```
  Level N work ──► ./gate check ──► machine token T  (derived from correct outputs)
                                         │
  Human answers gate question ──► A      │
                                         ▼
                         key = SHA-256(T ‖ normalise(A) ‖ salt)
                                         │
                         decrypt .vault/level{N+1}.pack  ──► .workshop/levels/N+1/
```

- **Machine token T.** `./gate check` runs the level's behaviour-based checks and, only if they pass, prints a short token derived from the *correct* outputs. A broken solution cannot produce it.
- **Human answer A.** This is a short structured answer (a letter, number or keyword) to a debrief question about what the group observed or decided. Examples: "What functional form did the discrepancy have?" "What was the exponent you measured?"
- **Key.** The key is derived from T and A together. Packs are encrypted with a SHAKE-256 keystream and authenticated with HMAC-SHA-256, all from Python's standard library. A wrong answer fails authentication cleanly, with the message "Not quite. Discuss and try again."
- **TTY requirement.** `./gate unlock` reads the answer with `getpass` and refuses to run without an interactive terminal. Claude's Bash tool has no TTY, so humans unlock the gate in a **separate "gate terminal"** window. The physical separation is deliberate: the gate terminal belongs to the humans.
- **Free-text reflection.** After a successful unlock, `./gate` asks one open question, such as "What would you do differently?". The answer is appended to `LOG.md` unchecked and feeds the show-and-tell.

### 5.4 Teacher Mode

**`CLAUDE.md`** holds the stable rules: the persona, what Claude must never do, and how to respond to "just fix it". Each exercise doc includes a draft.

**`teacher_context.py`** (a `UserPromptSubmit` hook) injects a short, level-specific brief on every prompt. It covers the current level, the persona mode for that level, and any constraints. Its plain stdout is added to Claude's context. This keeps a weak model on track as the conversation grows.

**Persona modes** are set per level:

| Mode | Behaviour |
|---|---|
| `literal` | Does what is asked, literally. Volunteers no best practice. Used where the lesson is seeing what happens without discipline (TDD Levels 0–1). |
| `coach` | Executes the group's experiments and reports evidence. Answers "just fix it" by asking for the group's hypothesis. Never names the bug or the fix first. Offers at most one leading question per turn. |
| `collaborator` | Normal helpful behaviour, still evidence-first. Used in later "free" levels (Exercise B's open race). |

### 5.5 Guardrails

**`.claude/settings.json` (shared skeleton):**

```json
{
  "model": "haiku",
  "permissions": {
    "defaultMode": "plan",
    "deny": [
      "Read(./.vault/**)",
      "Edit(./.vault/**)",
      "Edit(./.workshop/state.json)",
      "Bash(./gate unlock *)",
      "Bash(pip *)",
      "Bash(pip3 *)",
      "Bash(python3 -m pip *)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python3",
                     "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/teacher_context.py"] } ] }
    ],
    "PreToolUse": [
      { "matcher": "Read|Edit|Write|Bash|Grep|Glob",
        "hooks": [ { "type": "command", "command": "python3",
                     "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.py"],
                     "onFailure": "block" } ] }
    ],
    "PreModelSwitch": [
      { "matcher": ".*",
        "hooks": [ { "type": "command", "command": "python3",
                     "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/model_lock.py"] } ] }
    ]
  }
}
```

**Notes:**

- **`defaultMode: "plan"`** starts every session in read-only exploration, which reinforces *Understand* first. The Driver switches out with `Shift+Tab` once a plan is agreed.
- **`guard.py`** blocks tool calls that touch `.vault/` or `state.json`, Bash commands containing `gate unlock`, and package installs. It exits with code 2 and a teaching message, e.g. "The vault is for humans to unlock. Ask the group what they observed."
- **`model_lock.py`** reads the allowed models from `.workshop/state.json`, so a facilitator can grant a "Sonnet power-up". It denies any other switch.
- **`onFailure: "block"`** makes a crashing guard fail *closed*. It requires a recent Claude Code version; pin the version (see Section 7).
- **Verify before relying on it:** that the `"haiku"` alias is accepted in `settings.json` on the pinned version, and the exact canonical model names that `PreModelSwitch` matches against.

### 5.6 Honest Limits

This is a **learning scaffold, not an exam proctor.**

**Hard to bypass:**

- **Encrypted packs.** No content is visible without T and A.
- **The TTY requirement.** Claude can't type into the gate terminal.

**Soft (instructions and hooks Claude is asked to respect):**

- The teacher persona.
- Path guards on Bash. Hook `if` filtering on Bash is best-effort by design, which is why the vault is encrypted rather than merely hidden.

**Bypassable by a determined human:**

- A human could launch with `claude --model opus`. A launch flag isn't a mid-session switch, so `PreModelSwitch` doesn't see it.
- A human could ask Claude to reverse-engineer a gate.

Say this openly in the lecture: *"You can cheat. You'd be cheating yourselves out of the one hour of practice you get today."* If a group tries, treat it as a teachable moment rather than a disciplinary one.

### 5.7 Hints, Logging and the Master Key

- **`./gate hint`** reveals tiered hints for the current level, three per level: *nudge → direction → near-answer*. Hints are time-locked: tier 2 opens after 5 minutes on the level and tier 3 after 10. Every hint is logged.
- **`state.json`** records the level start time, unlock time, hints used and failed unlock attempts. This is your trial data.
- **`./gate skip --master`** (prompts for a facilitator passphrase) unlocks the next level for a stuck group. Use it sparingly, and log why.
- **`./gate status`** prints the level, time on level and hints used. Leaders call this out at time checks.

### 5.8 Building Level Packs

- Keep a **private answer-key repo** containing the plaintext packs, reference solutions and `gate pack` tooling.
- `gate pack <level-dir> --token-from <reference-solution> --answer <A>` runs the checks against the reference solution to derive T, then encrypts the next level's directory.
- The public exercise repo contains only Level 0 plaintext plus the encrypted packs.
- Tag the starting state `start`, so `git reset --hard start && ./gate reset` restores a clean state between trial runs.

---

## 6. Building and Calibrating the Exercises

### Build Checklist (per Exercise)

- [ ] Level 0 brief, data and code
- [ ] Planted issues (A, B), source and golden outputs (C), or spec and mutants (D)
- [ ] Behaviour-based checks for every level; they must not reveal the fix
- [ ] Gate questions and accepted answers (normalised: case, whitespace, synonyms, numeric tolerance)
- [ ] Three hint tiers per level
- [ ] `CLAUDE.md` teacher instructions and per-level persona briefs
- [ ] Reference solution path (to derive tokens and test end-to-end)
- [ ] `./preflight` script
- [ ] Facilitator answer key (private)

### Calibration Matrix

Run each exercise in four ways before the trial:

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

- Confirm each leader's **Claude Pro** account can run Claude Code with **Haiku** and **Sonnet**.
- Measure **usage consumed** per exercise in the trial. Haiku should stretch the allowance further, but confirm it.
- Hold **one or two spare accounts** on a facilitator laptop for groups whose leader hits a usage limit.

### Leader Machines (macOS)

- [ ] Xcode Command Line Tools (`xcode-select --install`): provides `git` and `clang`
- [ ] Python 3.11+ with `numpy` and `scipy` installed **in advance** (agents can't install packages during the session; the deny rules block `pip`)
- [ ] Exercise C only: `gfortran` (e.g. via Homebrew `gcc`), compile-tested in preflight
- [ ] Claude Code installed, version **pinned** to the one you calibrated against (`claude --version`)
- [ ] Repo cloned; **`./preflight` passes**. It checks Python, packages, compilers, git identity, that hooks fire, the model setting and the TTY gate.
- [ ] **Workspace trust accepted:** open `claude` in the repo once and accept the trust dialog. Project hooks and some settings wait for trust.
- [ ] Two terminal windows arranged: **Claude** (large) and **Gate** (small)
- [ ] An external screen or TV per group if the room allows. Otherwise the group gathers behind the leader's laptop.

### Leaders' Briefing (45 min, a few days before)

1. **(10 min)** Goals and principles (Section 2). Their role is *Coach*, not Driver.
2. **(10 min)** The leader walks through their exercise's Levels 0–1 themselves.
3. **(10 min)** The gate kit: gate terminal, hints, `./gate status`, what to do when something breaks.
4. **(10 min)** Group management: roles by size, rotation, the "hands off the code" rule, handling the expert who wants to take over.
5. **(5 min)** Preflight on their own machine; resolve any failures on the spot.

### Day Before

- Re-run `./preflight`, then `git reset --hard start && ./gate reset`.
- Charge laptops; confirm power at tables.
- Confirm nothing needs the network except Claude Code itself.

---

## 8. Running the Day

### Run-Sheet

| T (min) | Action |
|---|---|
| 0 | Lecture starts |
| 15 | Groups form; leaders allocate roles (card on table); gate terminal opened |
| 18 | **Go.** Everyone reads the Level 0 brief (`README.md`) together |
| 30 | Time call: "You should be past Level 1. If not, take a hint." |
| 45 | Time call: "Core levels should be done by 55. Scribes, start capturing your 'caught it' moment." |
| 58 | Stop. Scribes finalise `LOG.md` |
| 60 | Show-and-tell: 45 seconds per group, maximum |

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
4. How confident are you to use this workflow on your own code next week? (1–5 scale)
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
| Environment failure (Python, compiler, hooks) | Medium | Preflight; pinned versions; leaders' briefing; spare configured laptop |
| Haiku leaks answers despite teacher mode | Medium | Per-turn persona injection; calibration Run 1; answers are useless without the human gate answer anyway |
| Haiku too weak for a level | Medium | Facilitator Sonnet power-up; calibration Run 2 |
| Group finishes too early | Low–Medium | Stretch level in every exercise |
| Group stalls on Level 0–1 | Medium | Time calls; tiered hints; master skip |
| Leader dominates | Medium | Coach role; rotation rule; facilitator roaming |
| Group bypasses gates or switches model | Low | Name it in the lecture; encrypted packs; treat it as a teaching moment |
| Wi-Fi is poor | Low–Medium | Everything bundled; only Claude Code needs the network |

---

## 11. Open Decisions for You

1. **Exercise mix:** all A, or A/B/D split? (Recommended: A plus one other, so the show-and-tell compares two lessons.)
2. **Model policy:** strict Haiku with facilitator power-ups, or Sonnet available from a given level onwards?
3. **Lecture length:** 15 minutes as planned, or a 10-minute live demo added?
4. **Competition:** run the Speed Run leaderboard as a room-wide event, or keep it within groups?
5. **Take-home:** offer a public, ungated version of each repo afterwards for people to revisit?
