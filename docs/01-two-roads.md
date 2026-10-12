# Exercise A — Two Roads: Debugging a Discrepancy

| | |
|---|---|
| **One-liner** | Two ways of computing the same luminosity distance give different values of H₀. Find out why, fix the causes, and prove it. |
| **Core lesson** | Characterise before you hypothesise; experiments beat code-reading; **two methods agreeing doesn't make them correct**. |
| **Model** | Haiku (facilitator may grant a Sonnet power-up) |
| **Duration** | 42 min core + 8 min stretch |
| **Group size** | 2–5 |
| **Languages** | Python (numpy, scipy) |
| **Prep effort** | Moderate: you author a small package with planted bugs |

---

## 1. The Story (What Attendees See)

> Your collaboration's **standard-siren toolkit** infers H₀ from a catalogue of gravitational-wave events with redshifts. It has two distance engines:
>
> - **`quad`**: integrates 1/E(z) with `scipy.integrate.quad` for every event. Accurate, but slow.
> - **`grid`**: precomputes the comoving distance on a redshift grid once and interpolates. Fast, and used in production.
>
> A student noticed that the two engines give **different H₀** on the same catalogue. The difference is small but larger than the stated numerical tolerance, and at the level that matters for the Hubble tension. Your job: find out why, fix it properly, and leave the code in a state you'd trust.

`make sirens` prints something like this (illustrative numbers; set them during the build):

```
engine=quad   H0 = 70.12 ± 0.41 km/s/Mpc
engine=grid   H0 = 69.31 ± 0.40 km/s/Mpc
```

---

## 2. Learning Objectives

By the end, every group member should be able to:

1. **Characterise a discrepancy** (its shape as a function of the inputs) before guessing causes.
2. Get the agent to **rank hypotheses and propose distinguishing experiments**, instead of "fixing" on sight.
3. **Write a failing test first** that reproduces a bug, then fix the root cause.
4. Recognise **silent failure modes**: library defaults, stale state, order dependence.
5. Use **independent referees** (analytic limits) because agreement between two paths can hide a shared error.
6. Refuse to **widen a tolerance** without a physical reason.

---

## 3. Repo Design

```
two-roads/
├── README.md               # Level 0 brief
├── CLAUDE.md               # teacher instructions (Section 5)
├── LOG.md                  # Scribe template
├── Makefile                # make sirens | make test | make ratio
├── gate                    # gate kit CLI
├── sirens/
│   ├── cosmology.py        # FlatLCDM / LCDM parameters, E(z), shared helpers
│   ├── engine_quad.py      # direct integration
│   ├── engine_grid.py      # precomputed grid + interpolation + cache
│   ├── distances.py        # transverse comoving distance, D_L (shared by both engines)
│   └── infer.py            # chi² grid over H0 (and Ωm in joint mode); --engine, --joint, --order
├── data/
│   └── sirens_mock.csv     # ~60 events, z ∈ [0.05, 3.0], D_L ± σ
├── tests/
│   └── test_smoke.py       # passes; deliberately weak (tolerance rtol=1e-2)
├── .claude/ …              # settings + hooks (see facilitator guide)
├── .workshop/ …
└── .vault/level{1..5}.pack
```

**Design notes:**

- **No comment or name points at a bug.** The code should look like competent research code.
- The **existing smoke test passes** because its tolerance is loose. That is itself a planted lesson: *"the tests pass"* means nothing about a 1% effect.
- **Runtime:** `make sirens` should finish in under 5 seconds on a laptop, so experiments are cheap and nobody waits.

---

## 4. Levels

| Level | Title | Minutes | Gate: machine check | Gate: human question |
|---|---|---|---|---|
| 0 | Reproduce and orient | 5 | Both engines run; numbers recorded | ΔH₀ between engines (2 d.p.) |
| 1 | Characterise | 8 | `results/ratio.csv` matches the checker's own computation | Shape of the ratio R(z) |
| 2 | First cause | 7 | R(z) = 1 to 10⁻⁶ for z < 2 | Size of the offset |
| 3 | Silent failure | 10 | R(z) = 1 to 10⁻⁶ up to z = 3; out-of-range raises | Which library behaviour caused it |
| 4 | Order matters | 12 | Joint inference identical under all scan orders and both engines | What the cache must be keyed on |
| 5 | *Stretch:* Common-mode error | 8 | Analytic-limit suite passes | Which universe exposed it, and why both engines agreed |

### Level 0 — Reproduce and Orient (5 min)

**Brief:** "Run `make sirens`. Read `README.md`. Before you touch anything, write down in `LOG.md` what each engine does in one sentence each, *in your own words*."

**What the group does:**

- Runs the command and reads the code with Claude in **plan mode**.
- The Navigator writes the one-sentence descriptions; the Scribe records both H₀ values.

**Typical Haiku behaviour:** Claude summarises the code well, and may offer immediately to "fix" the difference. The persona brief tells it to decline and ask for a plan.

**Gate:**

- *Machine:* `./gate check` re-runs both engines and confirms the repo is unmodified.
- *Human:* "What is H₀(quad) − H₀(grid), to 2 d.p.?" (numeric, ±0.02).

**Teaching point:** reproduce before you reason. Writing your own description forces understanding that Claude's summary does not.

### Level 1 — Characterise (8 min)

**Brief:** "A single number (ΔH₀) is a symptom. Characterise it. Produce `results/ratio.csv` containing R(z) = D_L^grid / D_L^quad at the Planck-like fiducial cosmology, for z from 0.01 to 3.0 (at least 300 points), plus a plot. Do not change any code in `sirens/`."

**What the group does:**

- Directs Claude to write a small *characterisation script*, not a fix.
- Looks at the plot together. The Sceptic asks: *what shapes would different bug classes produce?*

**Expected discovery:** R(z) is **slightly above 1 and constant** for z < 2, then **drops sharply** above z ≈ 2. That is two features, so there are at least two causes.

**Typical Haiku behaviour:**

- It may try to "fix" the engines while writing the script. The `teacher_context` brief for this level forbids edits to `sirens/`, and `guard.py` blocks them.
- It may plot D_L rather than the ratio, hiding the 0.07% offset. The Sceptic should catch this ("we can't see anything at this scale").

**Gate:**

- *Machine:* the checker recomputes R(z) itself from the current (still buggy) code and compares it with the group's CSV.
- *Human:* "Which best describes R(z)? (a) constant ≠ 1 everywhere, (b) grows smoothly with z, (c) ≈ 1 then falls sharply above some z, (d) constant ≠ 1, *and* falls sharply above some z." **Answer: d.**

**Teaching point:** the *shape* of a discrepancy is diagnostic.

| Shape of R(z) | Likely cause |
|---|---|
| Constant offset | Prefactor or unit constant |
| Smooth trend | Integrand or physics difference |
| Sharp feature | Grid edge or range handling |
| Noise | Resolution or precision |
| Changes between runs | State or order dependence |

**Hints:**

1. "Plot the ratio, not the distances."
2. "Look at R(z) on two separate axes ranges: z < 2 and z > 2."
3. "There are two separate features. Treat them as two separate bugs."

### Level 2 — First Cause: the Constant Offset (7 min)

**Brief:** "Explain and remove the constant offset. First write a **failing test** that pins down the correct behaviour, show it failing, *then* fix."

**Planted bug 1:** `engine_grid.py` defines its own speed of light as `3.0e5` km/s. `cosmology.py` has the exact `299792.458`. The resulting ratio is 1.000692 at all z.

**What the group should do:**

- Ask Claude for ranked hypotheses for a *constant* offset: units, constants, h-scaling, a factor of (1+z) error (which wouldn't be constant). Then ask for an experiment to distinguish them.
- Write a test asserting R(z) = 1 to 10⁻⁶ for z < 2 (it fails), then fix by **importing the shared constant**, not by editing the number.

**Typical Haiku behaviour:** it may "fix" by multiplying by a fudge factor, or change the test tolerance to 10⁻³. **This is the key "you own the science" moment.** The Sceptic must reject both.

**Gate:**

- *Machine:* R(z) within 10⁻⁶ of 1 for z < 2, *and* `engine_grid` contains no physical constants of its own (a lint-style check).
- *Human:* "How large was the offset, in parts per 10⁴?" (≈ 6.9; accept 6–8).

**Teaching point:** fix the root cause (a duplicated constant), not the symptom. One source of truth.

**Hints:**

1. "A constant ratio means something multiplies the whole answer."
2. "Compare the constants used by each engine."
3. "`grep` for the speed of light."

### Level 3 — Silent Failure Above z = 2 (10 min)

**Brief:** "Explain the drop above z ≈ 2. Your fix must ensure that the code **can never silently return a wrong distance** for any redshift."

**Planted bug 2:** the grid is built on z ∈ [0, 2] (`Z_MAX = 2.0` in a config default). `np.interp` returns the **endpoint value** outside the grid range, so D_L is frozen at its z = 2 value for higher z. A handful of high-z sirens drag H₀ down.

**What the group should do:**

- Hypothesise a range issue from the sharp feature. Ask Claude to *read the `np.interp` documentation* for out-of-range behaviour; don't accept its memory of it.
- Write two tests: R(z) = 1 up to z = 3, and **a request outside the grid range either extends the grid or raises `ValueError`**.
- Decide as a group which of those two behaviours they want, and why. Either is accepted; silent clamping is not.

**Typical Haiku behaviour:** it may simply raise `Z_MAX` to 5. That fixes the symptom but leaves the silent-failure mode in place for z > 5. The second test catches this.

**Gate:**

- *Machine:* R(z) within 10⁻⁶ of 1 for z ≤ 3, *and* the checker probes z = 50, accepting either a correct value or a raised exception.
- *Human:* "Which function's default behaviour caused this?" (keyword: `interp`).

**Teaching point:** library defaults are design decisions you didn't make. Make failures **loud**.

**Hints:**

1. "What happens to an interpolator outside its data range?"
2. "Find where the grid's upper limit is set."
3. "`np.interp` doesn't extrapolate and doesn't warn."

### Level 4 — Order Matters (12 min)

**Brief (unlocked):** "With both fixes in place, single-cosmology distances agree. Now run the **joint** (H₀, Ωm) inference in two ways: `make sirens JOINT=1 ORDER=h0-outer` and `make sirens JOINT=1 ORDER=om-outer`. Same data, same model. Explain the results."

**Planted bug 3:** `engine_grid` caches its dimensionless χ(z) grid in a module-level dict **keyed on H₀**. The intent was efficiency, but χ in units of c/H₀ depends on **Ωm, not H₀**. In a joint scan, whichever Ωm is evaluated first for each H₀ gets cached and silently reused. The posterior therefore depends on the scan order, and the quad engine (no cache) disagrees with both.

**What the group should do:**

- Notice that the grid engine's answer depends on run order. This is the "run two ways" moment.
- Build a **minimal reproducer**: two calls with different Ωm at the same H₀ return identical distances.
- **Reason physically** about what the cache key *should* be. Here the physicists' knowledge beats the agent's: χ·H₀/c is a function of z and Ωm only.
- Fix, test that every scan order gives identical results, and test against the quad engine.

**Typical Haiku behaviour:**

- It may disable the cache entirely. That works, but costs the speed that motivated the grid engine. Coach the group to ask "what's the *right* key?"
- It may propose `functools.lru_cache` keyed on all parameters. That is correct but wasteful; a fine discussion point.

**Gate:**

- *Machine:* the joint posterior means are identical (to 10⁻⁹) across `h0-outer`, `om-outer` and `random` orders, and match the quad engine to 10⁻⁶.
- *Human:* "Which parameter(s) must the χ(z) cache be keyed on?" (keyword: Ωm; accepts `om`, `omega_m`, `omegam`, `Ωm`; rejects any answer that includes H₀).

**Teaching point:** state and caching are a classic source of irreproducibility. A result that depends on execution order is a bug even when each individual call "looks right".

**Hints:**

1. "Run the same call twice with only Ωm changed. Do you get different distances?"
2. "Look for anything that persists between calls."
3. "Does the dimensionless comoving distance depend on H₀?"

### Level 5 — *Stretch:* the Common-Mode Error (8 min)

**Brief (unlocked):** "Both engines now agree perfectly. Does that mean they're right? Test both against **three analytic universes**: Einstein–de Sitter, de Sitter, and Milne (empty, open)."

| Universe | Parameters | D_L(z) |
|---|---|---|
| Einstein–de Sitter | Ωm = 1 | (2c/H₀)(1+z)(1 − 1/√(1+z)) |
| de Sitter | ΩΛ = 1 | (c/H₀) z (1+z) |
| Milne | Ωk = 1 | (c/H₀) z (1 + z/2) |

**Planted bug 4 (common mode):** the shared `distances.transverse_comoving()` uses `sin` where it should use `sinh` for open geometry (Ωk > 0). Flat models, including the entire siren analysis, are unaffected. Both engines call the same helper, so **they agree with each other and are both wrong** for open universes.

**What the group should do:**

- Have Claude derive or look up the analytic results, and **check the derivations themselves**. They are physicists.
- Write parametrised tests. EdS and de Sitter pass; Milne fails in both engines.
- Fix the shared helper; all tests pass.

**Gate:**

- *Machine:* the analytic suite passes for both engines, including a closed-universe case that the checker adds.
- *Human:* "Which universe exposed the error?" (keyword: `milne` / `empty`). Then free text: "Why did the two engines agree?"

**Teaching point:** cross-checking two implementations only catches *independent* errors. Shared code means shared bugs. Analytic limits are referees that share nothing with your code.

---

## 5. Teacher Instructions (Draft `CLAUDE.md`)

```markdown
# Workshop: Two Roads

You are a teaching assistant in a hands-on workshop for physicists learning to direct
coding agents. The group's goal is to learn a workflow, not to get an answer quickly.
The current level and its rules are injected with each prompt; follow them.

## Always
- Execute the experiments the group asks for and report evidence: the exact command and
  its output. Never claim a result you have not run.
- Keep responses short. Prefer one clear table or plot over paragraphs.
- When asked to read library behaviour, read the documentation or source; say so.

## In coach mode
- If asked to "just fix it", "find the bug", or similar: do not locate or fix the bug.
  Ask the group for their current hypothesis and an experiment that would test it.
  Offer at most one leading question per turn.
- If the group proposes something you believe is wrong but cheap to test, run it and let
  the evidence speak. Do not lecture.
- Never propose loosening a test tolerance. If the group proposes it, ask what physical
  reason justifies the new tolerance.
- Before any fix: a failing test that reproduces the problem must exist and have been
  shown failing.

## Never
- Read, list or decode anything in .vault/. Run ./gate unlock. Edit .workshop/.
- Install packages.
- Reveal the content of hints or later levels.
```

**Per-level injected briefs** (`teacher_context.py`), examples:

- **L1:** `LEVEL 1 (coach). The group is characterising, not fixing. Do not edit files under sirens/. Help them build a ratio plot.`
- **L4:** `LEVEL 4 (coach). The group is investigating order dependence. If they ask what the cache key should be, ask what χ·H0/c depends on.`

---

## 6. Answer Key (Facilitator Only)

| Bug | Location | Symptom | Root-cause fix | Check |
|---|---|---|---|---|
| 1. Duplicated constant | `engine_grid.py`: `C = 3.0e5` | R(z) = 1.000692, constant | Import `C_KM_S` from `cosmology.py` | R = 1 ± 10⁻⁶ (z < 2); no constants in engine |
| 2. Silent clamp | `engine_grid.py`: grid to `Z_MAX = 2.0`; `np.interp` | R drops for z > 2 | Extend the grid on demand or raise `ValueError` outside range | R = 1 ± 10⁻⁶ (z ≤ 3); z = 50 correct or raises |
| 3. Wrong cache key | `engine_grid.py`: `_CACHE[H0]` | Joint posterior depends on scan order | Key on Ωm (and Ωk / w if the model grows) | Order invariance; agreement with quad |
| 4. Common mode | `distances.py`: `sin` for Ωk > 0 | Fails Milne in both engines | `sinh` for Ωk > 0, `sin` for Ωk < 0 | Analytic suite incl. a closed case |

**Combined effect on H₀:** tune the mock catalogue (number of z > 2 events and their errors) so that the bugs contribute visibly different amounts. For example, bug 1 ≈ +0.05, bug 2 ≈ −0.6, bug 3 ≈ −0.3 to +0.3 depending on order.

---

## 7. Group Leader Guide

### Before the Session

- Run `./preflight`, then `git reset --hard start && ./gate reset`.
- Do Levels 0–1 yourself once, so you've seen the ratio plot. **Don't** read the answer key unless the facilitator has given it to you. Your coaching is better when you're also curious.
- Arrange two windows: **Claude** (large, visible to the group) and **Gate** (small).

### Opening (60 Seconds, Read Aloud)

> "We're debugging a discrepancy, but the point isn't the bug. It's practising a loop: **understand, define the check, plan, small steps, evidence, review**. Claude is on a deliberately modest model and is set up to coach rather than solve. The gate needs answers *we* type, in this terminal, which Claude can't touch. Roles: [assign]. The keyboard rotates at each gate. Rule: all code changes go through Claude; we read, think and decide."

### Coaching by Level

| Level | Watch for | Ask the group |
|---|---|---|
| 0 | Skipping straight to "fix it" | "Can each of you explain what `grid` does without looking?" |
| 1 | Plotting distances instead of the ratio; editing code | "What would a units bug look like on this plot? A range bug?" |
| 2 | Fudge factors; widened tolerances | "What *physical* reason justifies that tolerance?" (Sceptic) |
| 3 | Raising `Z_MAX` and moving on | "What happens at z = 6 now? Who decides what the code should do there?" |
| 4 | Disabling the cache without thinking | "What does χ·H₀/c depend on? So what should the key be?" |
| 5 | Trusting Claude's analytic formulae | "Derive Milne on paper. Does Claude's formula match yours?" |

### Managing the Group

- **2 people:** you are Coach + Navigator; the other person is Driver + Sceptic + Scribe. Swap the Driver at each gate.
- **5 people:** split the Sceptic into Physics Sceptic (is the result physically sensible?) and Code Sceptic (did the test fail first, was the command shown?).
- **The expert who wants to fix it by hand:** "Great, you've spotted it. Now direct Claude to prove it with a failing test, *without telling it where the bug is*. Can you write a prompt that leads it there?" This is harder and more instructive than fixing it.
- **The quiet member:** give them the Sceptic role at Level 2. It is the highest-leverage role in that level.
- **Correction spirals:** if Claude has been corrected twice on the same issue, call `/clear` and help the Driver write a better prompt including what was learned.

### Time Checkpoints

| T (since Go) | Expected position | If behind |
|---|---|---|
| 13 min | Level 1 underway | Take a Level 1 hint |
| 25 min | Level 3 underway | Take hints freely; keep the loop, not the pace |
| 40 min | Level 4 underway or done | Ask the facilitator for a skip to Level 5 if Level 4 is stuck (Level 5's lesson is worth seeing) |
| 55 min | Stop; Scribe finalises `LOG.md` | |

### If Things Break

| Problem | Action |
|---|---|
| Hook errors | Run `/hooks` to confirm they're loaded, then call the facilitator |
| Usage limit hit | Switch to the facilitator's spare account |
| Gate rejects an answer you're sure of | Check spelling and units; then call the facilitator, who can inspect `state.json` |

---

## 8. Show-and-Tell Prompts

- "At which level did Claude want to fix it before you understood it? What did you do?"
- "Did anyone propose loosening a tolerance? Who stopped it?"
- "Which hypothesis did the evidence kill?"

---

## 9. Build Notes

1. Write the clean package first, with all four bugs absent, and its full test suite. This is the private reference solution.
2. Introduce the bugs **one per commit** in the private repo, so you can derive each level's starting state.
3. Generate the mock catalogue from the clean code (fiducial H₀ and Ωm of your choice), with realistic fractional errors (5–10%) and around 10–15% of events at z > 2.
4. Tune effect sizes so ΔH₀ at Level 0 is around 0.5–1 km/s/Mpc: larger than the quoted tolerance, smaller than the statistical error. Very realistic.
5. **Behaviour-based checks only.** No check should grep for the specific buggy line, except the Level 2 "no local constants" lint, which tests a principle rather than the location.

**Calibration (see facilitator guide, Section 6):**

- Confirm that a naive "fix the discrepancy" with Haiku fixes at most one bug and fails a later check.
- Confirm the Level 4 order dependence is reproducible on every run (it should be deterministic per order).

---

## 10. Open Questions for Iteration

1. Is the gravitational-wave framing right for your audience, or should the story be a pure cosmology one (e.g. SN Ia distance moduli)? The bugs transfer unchanged.
2. Five levels in 42 minutes is ambitious. If the trial runs long, merge Levels 0 and 1.
3. Should Level 5 be core rather than stretch? It carries the strongest single lesson ("agreement ≠ correctness").
4. Make `ORDER=random` part of Level 0's output, so the order dependence is visible from the start, as a mystery to keep in mind?
