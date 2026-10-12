# Exercise C — Fortran Archaeology: Porting Legacy Code You Can Trust

| | |
|---|---|
| **One-liner** | Port the original Fortran 77 HALOFIT (Smith et al. 2003) to tested, modern Python, proving equivalence at every step. |
| **Core lesson** | **Establish the oracle before you change anything.** The reference is what you test against, not what anyone (including the agent) remembers. |
| **Model** | Sonnet (Haiku struggles with fixed-form Fortran; try Haiku for Level 1 only in the trial) |
| **Duration** | 40 min core + 8 min stretch |
| **Group size** | 2–5 (best with at least one person who has read Fortran before) |
| **Languages** | Fortran 77 (read and compile only), Python (numpy) |
| **Prep effort** | Moderate: `gfortran` on leader machines, linear P(k) inputs, golden outputs, licence check |

---

## 1. The Story

> HALOFIT has been cited thousands of times and lives on inside CAMB and CLASS, but your group's pipeline calls an old copy of the original Fortran through a fragile shell wrapper. Your task: produce a **Python port that is provably equivalent** to the original, so the Fortran can finally be retired.
>
> "Provably" means: you can show, for a set of cosmologies and redshifts, that your port reproduces the original's outputs to a tolerance you can justify. That includes the intermediate quantities, not just the final answer.

### Why HALOFIT

- It is recognisable to every cosmologist in the room.
- It is genuinely Fortran 77.
- It is **small**: the original archive is around 20 kB.
- It has well-defined intermediate quantities to test against: the non-linear scale k_σ, the effective spectral index n_eff, and the curvature C.
- **The built-in trap:** strong models know HALOFIT, and especially the later Takahashi et al. (2012) recalibration, from training data. An agent will happily "port" from memory, and the golden outputs will catch it.

### Licence Note

Before bundling the source, confirm the redistribution terms. If they are unclear, have leaders download the original archive from the authors' page (linked from the ASCL entry) during setup, via the preflight script, rather than shipping it in the repo.

---

## 2. Learning Objectives

1. **Build the oracle first:** compile and run the original, and freeze golden outputs before writing any new code.
2. Use the agent for **code archaeology**: mapping routines, COMMON blocks, implicit typing and precision. **Verify its claims against the source and the paper.**
3. **Instrument intermediates**, so a port can be tested routine by routine, not only end to end.
4. Distinguish **fidelity** (reproduce the original, including its quirks) from **improvement** (change behaviour deliberately, with its own tests), and do them in that order.
5. Justify an equivalence **tolerance** from first principles, e.g. single- versus double-precision arithmetic and the root-finder's tolerance.
6. Capture the workflow as a **reusable skill** for porting your own legacy code.

---

## 3. Repo Design

```
fortran-archaeology/
├── README.md                 # Level 0 brief
├── CLAUDE.md                 # teacher instructions
├── LOG.md
├── Makefile                  # make fortran | make golden | make test
├── gate
├── legacy/
│   ├── halofit.f             # ORIGINAL — read-only (guard.py blocks edits)
│   └── driver.f              # small F77 driver: reads inputs, calls halofit, writes outputs
├── inputs/
│   ├── cosmologies.txt       # 3–4 cosmologies (Ωm, ΩΛ, σ8 / normalisation, …)
│   └── plin_*.txt            # linear P(k) tables per cosmology (if halofit.f needs external input)
├── golden/                   # created at Level 0 (machine-checked against stored hashes)
├── instrumented/             # created at Level 2: a COPY of legacy/ with WRITE statements
├── port/
│   └── halofit.py            # the Python port (starts empty, with a docstring stating the goal)
├── tests/                    # created by the group
├── papers/                   # Smith et al. 2003 preprint, fetched by preflight from arXiv
└── .workshop/ … .vault/ … .claude/ …
```

### Build-Time Inspection (Do This First)

Read the actual `halofit.f` and fill in the bracketed placeholders throughout this doc:

- Routine names.
- Whether reals are default `REAL` (single precision) or `DOUBLE PRECISION`.
- The root-finding method and its tolerance.
- Whether it computes its own linear P(k) or needs an external table.
- Whether any COMMON blocks exist.

If `halofit.f` needs an external linear spectrum, ship fixed tables from a documented Eisenstein & Hu implementation. That keeps the port focused on the non-linear mapping.

---

## 4. Levels

| Level | Title | Min | Gate: machine | Gate: human |
|---|---|---|---|---|
| 0 | Build the oracle | 8 | `golden/` matches stored hashes | Input/output units |
| 1 | Archaeology | 10 | `MAP.md` exists with required sections | Precision of reals; root-find tolerance |
| 2 | Instrument intermediates | 7 | `golden/intermediates.txt` matches the checker | A specific intermediate value |
| 3 | Port with fidelity | 15 | End-to-end and intermediates within 10⁻⁴ (relative) | Largest relative difference (order of magnitude) and its cause |
| 4 | *Stretch:* Make it yours | 8 | Skill file exists; vectorised port still passes | (free text) |

### Level 0 — Build the Oracle (8 min)

**Brief:** "Before anyone writes a line of Python: compile the original, run it on every input, and freeze the outputs into `golden/`. Record the compiler version and flags in `LOG.md`."

**What the group does:**

- Directs Claude to inspect `Makefile` and `driver.f`, compile with `gfortran` using the flags given, and run `make golden`.
- The Sceptic checks that the outputs are deterministic: run twice and diff.

**Typical behaviour:** Claude may suggest "improving" the compile flags (adding `-O3`, `-ffast-math`). The persona brief warns against it. The Sceptic should ask: *would that change the oracle?* (Yes: `-ffast-math` permits reassociation.)

**Gate:**

- *Machine:* `golden/*.txt` hashes match the stored values (the outputs are rounded to 6 significant figures before hashing, to absorb harmless platform noise).
- *Human:* "What units does the program use for k?" (keyword: `h/Mpc`; **confirm from source**).

**Teaching point:** without a frozen oracle, "the port works" is unfalsifiable. Compiler flags are part of the oracle.

### Level 1 — Archaeology (10 min)

**Brief:** "Have Claude produce `MAP.md`: every routine, its inputs and outputs, shared state (COMMON blocks), variable precision, any iteration or root-finding (method and tolerance), and which equation in Smith et al. (2003), Appendix C, each block implements. Then **verify at least three of its claims yourselves** against the source or the paper."

**Required `MAP.md` sections** (machine-checked by heading): Routines · Data flow · Shared state · Precision · Numerical methods · Equation map · Fortran hazards.

**Fortran hazards** to look for, depending on what's actually in the code:

| Hazard | Why it matters for a port |
|---|---|
| **Implicit typing** | Variables starting I–N are integers unless declared otherwise; this can cause silent integer division |
| **Default `REAL`** | Single precision (~7 significant figures) sets the achievable equivalence tolerance |
| **Mixed-precision literals** | `1.0` versus `1.0d0` |
| **Fixed form** | Column 6 continuation; **anything past column 72 is silently ignored** |
| **COMMON blocks** | Hidden shared state |
| **`SAVE` / uninitialised locals** | State that persists between calls |
| **1-based, column-major arrays** | Index translation errors |
| **`GOTO`-structured loops** | Control flow is easy to misread |

**Typical behaviour:** Sonnet produces an excellent-looking map. It may also **confidently attribute equations from the Takahashi (2012) version**, or describe the code as double precision when it isn't. The verification step is the point of this level.

**Gate:**

- *Machine:* `MAP.md` contains all required sections and names every routine in `halofit.f`. The checker parses routine names from the source.
- *Human:*
  - "Precision of the code's floating-point variables, in bits?" (**32 or 64; confirm from source**).
  - "Convergence tolerance of the k_σ root-find?" (numeric; **confirm from source**).

**Teaching point:** agents are excellent archaeologists *and* confident fabulists. Spot-check claims against the primary source.

### Level 2 — Instrument Intermediates (7 min)

**Brief:** "End-to-end comparison tells you *that* the port differs, not *where*. Make a **copy** of the legacy code in `instrumented/` and add `WRITE` statements to output k_σ, n_eff and C (and anything else `MAP.md` says is a key intermediate) for every input. Never modify `legacy/`."

**What the group does:**

- Directs Claude to copy the code, add output statements and recompile.
- Confirms that the instrumented final outputs still match `golden/` exactly: instrumentation must not change behaviour.
- Freezes `golden/intermediates.txt`.

**Typical behaviour:** Claude may try to edit `legacy/halofit.f` directly; `guard.py` blocks it with a teaching message. It may also print intermediates with a format that loses digits (e.g. `F8.3`). The Sceptic should insist on full precision.

**Gate:**

- *Machine:* the intermediates match the checker's stored values, and the instrumented final outputs match `golden/`.
- *Human:* "k_σ for cosmology A at z = 0, to 3 significant figures, in h/Mpc?" (numeric).

**Teaching point:** test at the seams. Intermediates turn a single "wrong answer" into "routine X is wrong".

### Level 3 — Port With Fidelity (15 min)

**Brief:** "Port `halofit.f` to `port/halofit.py`, **routine by routine**. For each routine: first write a test against the golden intermediates and show it failing; then port; then show it passing; then commit. Finish with end-to-end tests against `golden/`. Reproduce the original's behaviour, including its algorithm and tolerances, even where you'd do it differently. Improvements come later."

**The tolerance decision:**

- The Fortran likely runs in single precision; the Python port runs in double. The two **cannot** agree bit-for-bit.
- The group must decide, and write down *before* comparing, what tolerance is justified and why. For example: float32 relative precision ~10⁻⁷, amplified by the root-find tolerance and integration error, gives roughly 10⁻⁵–10⁻⁴.
- **The gate requires ≤ 10⁻⁴ relative.** Groups that justify a tighter tolerance and meet it get a mention at the show-and-tell.

**Planted trap (inherent, not planted):** if Claude writes from memory instead of from the source, typical tells are:

- Takahashi coefficients instead of Smith's.
- A different spectral-index definition.
- A different integration scheme for σ(R).

The per-routine tests catch these, usually at **high k and high n_eff** where the versions diverge most. The group must then decide whether the port or the oracle is "right". **The oracle defines right for a fidelity port.**

**Typical behaviour:** Sonnet may port all routines in one pass ("here's the complete port!"). The Navigator should stop this and insist on one routine, one test, one commit. Use `Esc` and redirect.

**Gate:**

- *Machine:* all intermediates and end-to-end outputs within 10⁻⁴ relative for every test cosmology and redshift. The checker also runs one hidden cosmology not in `inputs/`.
- *Human:*
  - "Order of magnitude of the largest relative difference you observed?" (exponent, e.g. −6; accept −8 to −4).
  - Free text: "What causes it?"

**Teaching point:** porting is **behaviour preservation**. Fidelity first; improvements later, as separate, deliberate, tested changes.

### Level 4 — *Stretch:* Make It Yours (8 min)

**Two options; pick one or both.**

1. **Turn the workflow into a skill.**
   - Have Claude write `.claude/skills/legacy-port/SKILL.md`, capturing *your* workflow: oracle, archaeology, instrumentation, routine-by-routine fidelity, tolerance justification, then improvement.
   - Edit it until it reads like your group's method, not generic advice.
   - Each member can copy it into their own projects. This is the take-home artefact.
2. **Improve deliberately.**
   - Vectorise the port over k with NumPy, keeping all fidelity tests passing.
   - Add one physics property test, e.g. Δ²_NL → Δ²_L as k → 0.

**Gate:**

- *Machine:* the skill file exists with frontmatter; the port still passes Level 3's checks.
- *Human:* free text: "Which step would you skip next time, and why wouldn't you?"

---

## 5. Teacher Instructions (Draft `CLAUDE.md`)

```markdown
# Workshop: Fortran Archaeology

You are assisting physicists porting a legacy Fortran 77 code to Python. The goal is a
port that is provably equivalent to the ORIGINAL SOURCE in legacy/, not to any version
you may remember. The current level's rules are injected with each prompt.

## Always
- Base every statement about the code on the source file, citing line numbers. If you
  are recalling HALOFIT from memory rather than reading the source, say so explicitly.
- Base equation attributions on papers/ (Smith et al. 2003), citing equation numbers.
- Report comparisons with the command, the output and the maximum relative difference.
- Port one routine at a time: failing test → port → passing test → commit. Stop after
  each routine and report.

## Never
- Edit anything in legacy/ or golden/. Change compiler flags used for golden outputs.
- Use coefficients, equations or algorithms that are not in legacy/halofit.f.
- Loosen a comparison tolerance; the group decides tolerances and records the reasoning.
- Read .vault/, run ./gate unlock, or install packages.
```

---

## 6. Answer Key (Facilitator Only)

*Complete after inspecting the source.*

| Item | Value |
|---|---|
| Routines in `halofit.f` | [list] |
| Real precision | [REAL / DOUBLE PRECISION] |
| k_σ root-find method and tolerance | [method, tol] |
| σ(R) integration method | [method, points] |
| Linear P(k) source | [internal EH no-wiggle / external table] |
| COMMON blocks | [names / none] |
| Expected max relative difference (port vs golden) | [measure with the reference port] |
| Known memory-port tells | Takahashi coefficients; n_eff/C definitions; integration scheme |

---

## 7. Group Leader Guide

### Before the Session

- `./preflight` must confirm `gfortran` compiles `driver.f` + `halofit.f` and that `make golden` reproduces the stored hashes. **Don't skip this.** Compiler issues are the main risk for this exercise.
- Skim `halofit.f` and the paper's Appendix C for 10 minutes, so you can point people to the right place.
- Arrange the windows: **Claude**, **Gate**, and an editor or viewer with `legacy/halofit.f` open for humans to read alongside Claude.

### Opening (60 Seconds)

> "We're retiring a famous Fortran code by porting it, and we must *prove* the port is equivalent. The rule is: **oracle first**. We don't write Python until we've frozen the original's outputs. Claude knows HALOFIT from training. That's a trap, not a help: we port what's in *this* file. Roles: [assign]. The keyboard rotates at each gate."

### Coaching by Level

| Level | Watch for | Ask |
|---|---|---|
| 0 | "Improving" compile flags | "Would that flag change the oracle?" |
| 1 | Accepting `MAP.md` wholesale | "Pick three claims. Show me the line numbers. Show me the equation." |
| 2 | Editing `legacy/`; low-precision `WRITE` formats | "How many digits does that format keep? Is that enough to test against?" |
| 3 | One-shot full ports; tolerance chosen *after* comparing | "Navigator, one routine at a time. Sceptic, what tolerance did we commit to *before* running?" |
| 4 | A generic skill file | "Would a new student follow this and get it right? What did *we* learn the hard way?" |

### Managing the Group

- **Fortran-literate member:** natural Level 1 Sceptic, verifying Claude's archaeology claims. Don't let them become the sole archaeologist; they should *check*, not *do*.
- **Nobody has read Fortran:** that's fine. Claude explains, and the group verifies one claim against the paper rather than the code.
- **2 people:** you are Coach + Navigator; the partner is Driver + Sceptic.
- **5 people:** at Level 3, assign one person to each routine as its *owner*. They review that routine's test and port before the commit.

### Time Checkpoints

| T (since Go) | Expected | If behind |
|---|---|---|
| 8 min | Golden frozen | Facilitator help with compilation; don't let this eat the session |
| 18 min | `MAP.md` verified | Accept a thinner map; verify at least two claims |
| 25 min | Intermediates frozen | Take hint 2 (a ready-made `WRITE` format) |
| 40 min | Port passes | A partial port with passing per-routine tests is a good outcome; skip to the skill if time is short |

### If Things Break

| Problem | Action |
|---|---|
| `gfortran` missing or failing | Facilitator's spare laptop, or a provided pre-compiled binary plus golden outputs (the lesson survives) |
| Usage limits (Sonnet is heavier) | Encourage `/clear` between routines; the spare account is the fallback |
| Claude insists the original has a bug | Great discussion! The answer for *this* exercise: port it faithfully, record it in `LOG.md` as a candidate improvement, and test it later. |

---

## 8. Show-and-Tell Prompts

- "Which of Claude's archaeology claims turned out to be wrong?"
- "Did the port ever reproduce a version of HALOFIT that *isn't* this file? How did you notice?"
- "What tolerance did you commit to, and how did you justify it?"

---

## 9. Build Notes

1. Obtain the source and confirm the licence. Inspect it and fill in Sections 3 and 6.
2. Write `driver.f` (small, clear F77) and choose 3–4 cosmologies spanning n_eff and C (e.g. vary Ωm and σ8), plus one **hidden** cosmology for the Level 3 checker.
3. Fix compiler flags (`-O0` or `-O1`; no fast-math) and record the `gfortran` version used for the golden outputs.
4. Write your own reference port, to set the achievable tolerance and fill in the expected maximum difference.
5. **Calibrate with Sonnet:**
   - Does a naive "port this to Python" produce a memory-based port that the golden outputs catch? (Test both with and without `legacy/` in context.)
   - Does guided work reach a passing port by about 40 minutes?
6. If the trial shows the full port is too long, ship a **partially ported** Python file (e.g. the σ(R) integration already done and tested) so Level 3 is about porting the remaining routines.

---

## 10. Open Questions for Iteration

1. Is HALOFIT the right target, or would a GW-flavoured legacy code suit your audience better? Candidates are a small post-Newtonian waveform or a Fisher-matrix code. The Eisenstein & Hu C code is a further option, and has documented code-versus-paper discrepancies that make a rich Level 1.
2. Sonnet throughout, or Haiku for Levels 0–2 (archaeology on a weak model is a strong lesson) and Sonnet for the port?
3. Should Level 4's skill file be compulsory? It's the most transferable artefact of all four exercises.
