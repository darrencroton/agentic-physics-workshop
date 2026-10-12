# Exercise D — The TDD Ladder: From "Just Build It" to Tests You Can Trust

| | |
|---|---|
| **One-liner** | Implement one small feature several times, climbing from naive agent use to disciplined, physics-aware test-driven development, with an objective score showing how good your tests really are at each rung. |
| **Core lesson** | **You define "correct"; the agent cannot.** Tests are only as good as the decisions and oracles behind them. |
| **Model** | Haiku (its literalness makes specification gaps very visible) |
| **Duration** | 44 min core + 5 min stretch |
| **Group size** | 2–5 |
| **Languages** | Python (numpy, pytest pre-installed) |
| **Prep effort** | Moderate: a small repo, a client spec, ~16 mutant implementations, the `./tdd` tool |

---

## 1. The Story

> Your group's small H(z) analysis package (`hzbin`) plots cosmic-chronometer-style Hubble-rate measurements. A collaborator asks:
>
> *"Can you add a function to bin our measurements and give us the weighted mean and error in each bin? We need it for the H(z) plot."*
>
> That's the entire request. It sounds trivial. It contains at least ten decisions nobody has made.

The feature is `binned_weighted_mean(x, y, sigma, edges)`. Binning noisy data with error bars is universal across cosmology, GW and dark-matter work, and it is full of choices physicists have opinions about:

- edge conventions;
- empty bins;
- what the error *means*;
- where to plot the point.

---

## 2. Learning Objectives

1. Experience **why naive agent-written tests are weak**, measured objectively rather than asserted by the facilitator.
2. **Surface ambiguity before testing:** have the agent interview *you*, and make the decisions yourselves.
3. Run a **genuine red–green–refactor cycle**: one behaviour per cycle, red seen for the right reason, tests frozen during green.
4. Write tests with **independent oracles** (hand calculations, analytic cases), never values computed by the code under test.
5. Use **physics and statistics** in tests: invariants, limiting cases, coverage of error bars.
6. **Test the tests:** mutation testing as the honest measure of test-suite strength.

---

## 3. How TDD Goes Wrong (Especially With an Agent)

This catalogue is the backbone of the exercise. The "Exposed at" column shows where each anti-pattern typically surfaces in the levels below.

### A. Process

| # | Anti-pattern | What it looks like with an agent | Why it's harmful | Exposed at | Remedy |
|---|---|---|---|---|---|
| 1 | **Tests after code** | "Implement it and add tests": tests are written by reading the implementation | Tests confirm the code, bugs included; they can't disagree with it | L0 | Tests first, from the spec |
| 2 | **Never seeing red** | Tests and implementation arrive in one turn; first run is all green | A test never seen failing might not be able to fail | L1 | Run tests before the implementation exists |
| 3 | **Red for the wrong reason** | Failure is `ImportError` or `NameError`, not an assertion | Proves nothing about behaviour | L3 | Stub raising `NotImplementedError`; check the failure *type* |
| 4 | **Big-bang cycles** | Ten tests written, then everything implemented at once | Failures don't localise; no design feedback | L1, L3 | One behaviour per cycle |
| 5 | **Editing tests to go green** | "Fixed the failing test" by changing its expected value | The spec silently changes to match the bug | L1, L3 | Freeze tests during green; changing a test means going back to red, *on purpose* |
| 6 | **Skipping refactor** | Green, move on; duplication accumulates | Design rots; future tests get harder | L3 | Refactor step with tests frozen |
| 7 | **No commit at green** | A long chain of uncommitted changes | No safe point to return to | L3 | Commit at every green |
| 8 | **Skip / xfail to pass** | `@pytest.mark.skip` appears "temporarily" | Hides failures permanently | L1 | Treat skip as a failure; ban it in review |

### B. Oracles (Where Expected Values Come From)

| # | Anti-pattern | What it looks like | Why it's harmful | Exposed at | Remedy |
|---|---|---|---|---|---|
| 9 | **Snapshot oracle** | Expected values obtained by running the implementation | Freezes current bugs as "correct" | L0, L1 | Hand-computed values on tiny inputs |
| 10 | **Mental-arithmetic oracle** | The agent "computes" 1/√(Σw) in its head and writes 0.4472 | Plausible-looking wrong numbers | L1 | Humans compute small cases; or exact fractions |
| 11 | **Tautological test** | Test reimplements the formula: `assert mean == np.sum(w*y)/np.sum(w)` | Same misconception in test and code | L1, L3 | Concrete numbers, analytic cases, invariants |
| 12 | **Over-loose tolerance** | `pytest.approx(x, rel=1e-2)` "to be safe" | Lets real bugs through (e.g. 1/σ vs 1/σ² can hide) | L3, L4 | Justify every tolerance |
| 13 | **Brittle exact float equality** | `assert err == 0.1` where rounding legitimately differs | False failures erode trust in the suite | L3 | `approx` with a *justified* tight tolerance |

### C. Specification

| # | Anti-pattern | What it looks like | Why it's harmful | Exposed at | Remedy |
|---|---|---|---|---|---|
| 14 | **Silent assumption** | The agent picks edge conventions, empty-bin behaviour and NaN handling without asking | Decisions are made by default, invisibly | L0–L2 | Agent interviews you; numbered decisions in a spec |
| 15 | **Happy path only** | No empty bins, edge values, bad input or extremes | Bugs live at the boundaries | L0–L3 | Enumerate boundaries from the spec |
| 16 | **Over-specification** | Asserting *how* (e.g. "calls `np.histogram`"), mocking numpy | Correct refactors break tests | L1, scorecard | Test behaviour through the public interface |
| 17 | **Testing the wrong thing** | Tests pass; the client's needs aren't met | Green is meaningless | L0–L2 | Client acceptance tests; spec review |

### D. Test Design

| # | Anti-pattern | What it looks like | Why it's harmful | Exposed at | Remedy |
|---|---|---|---|---|---|
| 18 | **Assertion-free test** | Calls the function and prints the result | Can only fail by crashing | L0 | Every test asserts behaviour |
| 19 | **Many behaviours per test** | One test checks mean, error, counts and NaN handling | A failure doesn't say what broke | L3 | One behaviour per test; descriptive names |
| 20 | **Unseeded randomness** | Monte Carlo test without a seed | Flaky; ignored after the first false failure | L4 | Fixed seed; statistically justified bounds |
| 21 | **Overly broad exception check** | `pytest.raises(Exception)` | Passes for the wrong error (e.g. a `TypeError` from a typo) | L3 | Specific exception type and message match |
| 22 | **Order-dependent tests** | Shared mutable fixtures | Pass alone, fail together (or the reverse) | L3 | Fresh data per test |
| 23 | **Slow suite** | 30-second Monte Carlo in every run | People stop running the tests | L4 | Small, fast statistical tests; mark the slow ones |

### E. Agent-Specific

| # | Anti-pattern | What it looks like | Why it's harmful | Exposed at | Remedy |
|---|---|---|---|---|---|
| 24 | **Special-casing test inputs** | `if len(x) == 3: return …` or other overfitting | Passes the tests, fails reality | L3 | Property tests; mutation and acceptance scores |
| 25 | **Quietly weakened asserts** | Asked to "make the tests pass", it relaxes them | Spec erosion | L1, L3 | Tests frozen during green (hook-enforced) |
| 26 | **Claimed green** | "All 12 tests pass ✅" without having run them | False confidence | L0–L3 | Demand the pytest output |
| 27 | **Coverage theatre** | 40 shallow tests, high line coverage | Volume isn't strength | Scorecard | Mutation score, not test count |
| 28 | **Context drift** | Forgets spec decision 4 by cycle 9 | Regressions against the spec | L3 | `SPEC.md` referenced with `@`; `/clear` between phases |

---

## 4. The Quality Ladder

| Rung | Name | Characteristics | Typical outcome (calibrate) |
|---|---|---|---|
| 0 | **Vibe coding** | "Add the function." Few or no tests. | Plot looks fine; acceptance ~40–60%; mutants killed ~10–25% |
| 1 | **Tests after** | Agent writes the code, then tests by reading the code | All green; mutants ~25–40%; some false alarms (tests encode guesses) |
| 2 | **TDD in name only** | "Use TDD": tests and code in one turn; red never seen; tests edited to pass | Like Rung 1, with more false confidence |
| 3 | **Mechanical red–green** | Real cycles, but snapshot or mental-arithmetic oracles; happy path | Mutants ~50–65% |
| 4 | **Spec-driven red–green–refactor** | Humans own the decisions; hand-computed oracles; tests frozen during green | Mutants ~75–85%; zero false alarms |
| 5 | **Physics- and property-aware** | Invariants, limiting cases, statistical coverage, precision | Mutants ~90–100% |
| 6 | **Tests tested** | Mutation testing; survivors reviewed; redundant tests pruned | ~100%, with a lean suite |

---

## 5. The Objective Scorecard

`./tdd score` (humans run it in the gate terminal) prints three numbers:

| Measure | How it's computed | What it tells you |
|---|---|---|
| **Acceptance** | Hidden client acceptance tests run against *your implementation* | Does the code do what the client needed? |
| **Mutants killed** | Your test suite run against **16 hidden mutant implementations**, each violating one spec decision or physics principle | How strong are your *tests*? |
| **False alarms** | Your test suite run against a hidden **correct** implementation | Do your tests reject correct code (over-specification or wrong expectations)? |

### Example Output

```
ACCEPTANCE      7/12 client tests pass on your implementation
MUTANTS KILLED  4/16
  surviving mutants violate: S1 (×2), S3, S4 (×2), S5, S6, S7, S8, S9, S10 (×2)
FALSE ALARMS    3 of your tests fail on a correct implementation
  test_empty_bin_returns_zero          (conflicts with S6)
  test_midpoint_x                      (conflicts with S5)
  test_drops_nan_silently              (conflicts with S7)
```

### Design Choices

- Surviving mutants are reported **by spec decision only, never by code**. This lets the group target gaps without "teaching to the mutants".
- Scores are logged per level, so the group sees its own ladder at the show-and-tell. **The rising curve is the exercise's punchline.**

---

## 6. Repo Design and Phase Enforcement

```
tdd-ladder/
├── README.md                 # Level 0 brief (the client's one-line request, verbatim)
├── CLAUDE.md                 # teacher instructions with persona modes
├── LOG.md
├── tdd                       # CLI: status | red | green | refactor | done | score (TTY for transitions)
├── gate
├── src/hzbin/
│   ├── data.py               # loads data/hz_mock.csv
│   ├── plot.py               # make plot — uses binned_weighted_mean
│   └── binning.py            # stub: binned_weighted_mean raises NotImplementedError
├── tests/                    # empty except conftest.py
├── data/hz_mock.csv          # ~40 H(z) points, heteroscedastic errors, a few at bin edges
├── .tdd/
│   ├── phase                 # none | red | green | refactor
│   └── cycles.jsonl          # one record per cycle: behaviour, red-observed, failure type, timings
└── .workshop/ … .vault/ … .claude/ …
```

### Phase Rules (From Level 3)

| Phase | Editable | Frozen | Entry condition (checked by `./tdd`) |
|---|---|---|---|
| `red "<behaviour>"` | `tests/` | `src/` | Previous cycle done; all tests currently pass |
| `green` | `src/` | `tests/` | New tests **committed**; ≥ 1 test fails; failures are assertion errors or `NotImplementedError` (**not** import, syntax or name errors); previously passing tests still pass |
| `refactor` | `src/` | `tests/` | All tests pass; `tests/` unchanged since `green` began |
| `done` | — | — | All tests pass; changes committed |

### Enforcement Layers

- **Hard:** `guard.py` (a `PreToolUse` hook) blocks `Edit`/`Write` on frozen paths. Its message to Claude reads: *"Tests are frozen in GREEN. If a test is wrong, the group must decide to return to RED."*
- **Backstop:** `./tdd` transitions use `git diff` to detect Bash-based edits to frozen paths, and refuse the transition with an explanation.
- **Humans own the cycle:** transitions (`red`, `green`, `refactor`, `done`) require a TTY, so the humans run them in the gate terminal. Claude runs tests; humans change phase.

---

## 7. Levels

| Level | Title | Min | Persona | Gate: machine | Gate: human |
|---|---|---|---|---|---|
| 0 | Just build it | 5 | literal | `./tdd score` run on result | Acceptance score; two silent decisions (logged) |
| 1 | "Use TDD, please" | 6 | literal | `./tdd score` run | Was red ever seen? Where did the expected values come from? (logged) |
| 2 | Decide before you test | 10 | coach | `SPEC.md` with ≥ 6 numbered decisions | How many client decisions did you anticipate? |
| 3 | Red, green, refactor, for real | 15 | coach | ≥ 5 valid cycles; 0 false alarms; ≥ 9/16 killed | Which spec decision still has a surviving mutant? |
| 4 | Think like a physicist | 8 | coach | ≥ 14/16 killed; 0 false alarms | Binomial σ of a coverage fraction |
| 5 | *Stretch:* Test the tests | 5 | collaborator | Mutation report in `LOG.md` | (free text) |

*Levels 0, 1 and 2 have **reflection gates**: the machine check confirms the work was done, and the human answer is logged for the debrief rather than graded. Levels 3 and 4 have **understanding gates**.*

### Level 0 — Just Build It (5 min) · Rung 0–1

**Brief:** "Paste the client's request into Claude exactly as written. Accept what it gives you. Run `make plot`. Then run `./tdd score` in the gate terminal."

**Persona `literal`:** Claude does what is asked, makes reasonable assumptions *silently*, and doesn't volunteer process advice. This is a deliberate handicap so the anti-patterns are visible. Say so openly in the debrief.

**What happens:**

- A plausible function appears, possibly with a couple of tests. The plot looks fine.
- Then the scorecard lands, typically showing middling acceptance, few mutants killed and several false alarms.

**Gate:**

- *Machine:* the score has been run.
- *Human:* "How many client acceptance tests passed?" (read from the score). Then free text: "Name two decisions Claude made that nobody asked you about."

**Debrief point:** a plot that *looks* right is not evidence. Every unasked question was answered by default.

### Level 1 — "Use TDD, Please" (6 min) · Rung 2

**Brief:** "`git checkout level1-start` (stub restored, tests cleared). Same request, plus: *'Use test-driven development.'* Watch closely. Did any test fail before code existed? Where did the expected numbers come from?"

**What typically happens with Haiku in literal mode:**

- Tests and implementation arrive together, and the first run is all green.
- Expected values were computed by running the code, or "in its head".
- At least one test may be adjusted after a failure.

`.tdd/cycles.jsonl` records that red was never observed (the `./tdd` tool watches test runs even outside phase mode).

**Gate:**

- *Machine:* the score has been run; the run log exists.
- *Human:*
  - "Did any test fail before the implementation existed? (y/n)"
  - "Where did the expected values come from? (a) human hand calculation, (b) Claude's mental arithmetic, (c) running the implementation, (d) independent reference."
  - Both are logged.

**Debrief point:** saying "TDD" doesn't make it TDD. The discipline must be *structural*: phases, frozen tests, observed red.

### Level 2 — Decide Before You Test (10 min)

**Brief:** "Switch to coach mode. Ask Claude to **interview you** about this feature until every behavioural decision is explicit, using its question tool. Make the decisions *as a group*. Then have it write `SPEC.md` with numbered decisions. No code, no tests."

**Suggested prompt (on the brief card):**

> *"We need to implement binned_weighted_mean(x, y, sigma, edges). Interview us about every behavioural decision: inputs, edge cases, conventions, errors, outputs. Ask about the hard parts we may not have considered. Don't suggest answers. Then write SPEC.md with numbered decisions."*

**What the group does:**

- Debates, physicists being physicists, whether the bin's x-position should be the midpoint or the weighted mean, and what the error bar means (the error on the weighted mean, or the scatter).
- The Scribe records the decisions.

**Gate:**

- *Machine:* `SPEC.md` exists with ≥ 6 numbered decisions.
- *Human:* after unlocking, the group reads **`CLIENT_SPEC.md`** (Section 8) and answers: "How many of the client's 10 decisions did your SPEC address, whatever you chose?" (logged).

**Then reconcile:** adopt the client's spec where it differs. The client is the customer. Note any decision you think the client got wrong; that is a conversation to have with the client, not something to override silently in code.

**Debrief point:** most groups anticipate 5–8 of the 10. The rest would have been silent guesses. **Ambiguity is cheapest to resolve before the first test.**

### Level 3 — Red, Green, Refactor, for Real (15 min) · Rung 3 → 4

**Brief:** "Phase enforcement is now on. Start from the stub. Implement `CLIENT_SPEC.md` one behaviour at a time."

**Rules for each cycle:**

1. **`./tdd red "<behaviour>"`** (gate terminal). Claude writes **one** test for that behaviour.
2. **The expected value comes from a human.** The Sceptic computes it by hand on a tiny input (2–4 points; exact fractions where possible). No numbers from Claude.
3. Commit the test. Then **`./tdd green`**. The tool checks that the test fails *for the right reason*.
4. Claude writes the **minimum** code to pass. Tests are frozen; the hook enforces this.
5. Green → commit. Every few cycles, **`./tdd refactor`**.

**Suggested cycle order:**

1. Single bin, equal σ → arithmetic mean.
2. Unequal σ → inverse-variance weighting.
3. Error = (Σw)^−½.
4. Two bins and the edge convention (S1).
5. Out-of-range points and `n_dropped` (S2).
6. Empty bin (S6).
7. Invalid inputs (S7–S9).
8. x_eff (S5).
9. Inputs unchanged (S10).

**Typical Haiku behaviour:**

- It writes three tests when asked for one. The Navigator says no.
- It tries to edit a test during green. The hook blocks it, with a message that becomes a group discussion.
- It special-cases a test input. The scorecard's acceptance tests catch this later.
- It proposes `pytest.approx(…, rel=1e-3)`. The Sceptic asks why.

**Gate:**

- *Machine:* ≥ 5 cycles logged with red observed for the right reason; 0 false alarms; ≥ 9/16 mutants killed.
- *Human:* "Which spec decision still has a surviving mutant?" (read from the score; checks that the group engages with the report).

**Debrief point:** the discipline feels slow, and it is: until the scorecard shows what it bought.

### Level 4 — Think Like a Physicist (8 min) · Rung 5

**Brief:** "Example tests check points. Physics gives you *properties*. Add tests that would catch whole classes of error."

**Menu (pick at least three):**

| Property test | Kills mutants like… |
|---|---|
| **Permutation invariance:** shuffle the inputs; results unchanged | Order-dependent accumulation |
| **Uniform-σ limit:** equal σ gives the arithmetic mean and err = σ/√n exactly | 1/σ weighting (M05); missing √ (M08) |
| **Affine equivariance:** y → a·y + b gives mean → a·mean + b and err → \|a\|·err | Scatter-based error (M07) |
| **Bin merging:** combining two adjacent bins' weighted means equals binning with the edge removed | Weighting errors; x_eff errors |
| **Coverage:** Monte Carlo with a fixed seed. Draw y ~ N(μ, σ) and check that the fraction of bins with \|mean − μ\| < err is ≈ 0.683, within a *binomially justified* bound | Wrong error definitions (M07, M08), wrong weights (M05) |
| **Precision:** float32 input with a large offset (y ≈ 10⁶ + small signal); result matches the float64 computation | float32 accumulation (M15) |

**Gate:**

- *Machine:* ≥ 14/16 mutants killed; 0 false alarms; suite runtime < 10 s.
- *Human:* "For a coverage test with 2,500 independent bin-trials and true coverage 0.683, what is the standard deviation of the measured coverage fraction?" (√(p(1−p)/N) ≈ 0.0093; accept 0.0090–0.0096).

**Debrief point:** statistical tests need *statistically justified* tolerances. That is the physicist's home advantage over the agent.

### Level 5 — *Stretch:* Test the Tests (5 min) · Rung 6

**Brief:** "Have Claude, via a subagent, generate its own mutants of *your* implementation: small deliberate bugs. Run your suite against each. Review any survivors. Are they real gaps or equivalent mutants? Then ask which of your tests are redundant."

**Gate:**

- *Machine:* a mutation report section exists in `LOG.md`.
- *Human:* free text: "One test you'd delete and why."

---

## 8. Client Spec (Facilitator; Unlocked After Level 2)

`binned_weighted_mean(x, y, sigma, edges) -> BinnedResult(x_eff, mean, err, n, n_dropped)`

| ID | Decision |
|---|---|
| **S1** | Bins are half-open [eₖ, eₖ₊₁), except the **last bin, which is closed** [eₙ₋₁, eₙ]. |
| **S2** | Points outside [e₀, eₙ] are excluded; their number is returned as `n_dropped`. |
| **S3** | Weights are w = 1/σ². |
| **S4** | mean = Σwy / Σw; err = (Σw)^−½ (the uncertainty of the weighted mean, not the scatter). |
| **S5** | x_eff = Σwx / Σw within the bin (not the bin midpoint). |
| **S6** | Empty bins give x_eff, mean, err = NaN and n = 0. |
| **S7** | Any non-finite value in x, y or σ raises `ValueError`. No silent dropping. |
| **S8** | Any σ ≤ 0 raises `ValueError`. |
| **S9** | `edges` must be strictly increasing with length ≥ 2; x, y and σ must be 1-D and of equal length. Otherwise `ValueError`. |
| **S10** | Inputs are not modified; lists are accepted; outputs are float64 arrays (n and `n_dropped` integer); accumulation is in float64 even for float32 input. |

### Mutants (Hidden; Each Violates Exactly One Decision)

| ID | Mutation | Violates |
|---|---|---|
| M01 | Last bin half-open (point at eₙ dropped) | S1 |
| M02 | Bins left-open (eₖ, eₖ₊₁] | S1 |
| M03 | Out-of-range points clipped into end bins | S2 |
| M04 | `n_dropped` counts only points below e₀ | S2 |
| M05 | w = 1/σ | S3 |
| M06 | Unweighted mean | S3/S4 |
| M07 | err = std(y)/√n | S4 |
| M08 | err = 1/Σw (missing square root) | S4 |
| M09 | x_eff = bin midpoint | S5 |
| M10 | Empty bin returns 0 | S6 |
| M11 | NaN in y silently dropped | S7 |
| M12 | σ = 0 accepted (infinite weight) | S8 |
| M13 | Decreasing edges accepted | S9 |
| M14 | Sorts x in place | S10 |
| M15 | float32 accumulation | S10 |
| M16 | Off-by-one bin index | (any; the "everyone kills this" baseline) |

---

## 9. Teacher Instructions (Draft `CLAUDE.md`)

```markdown
# Workshop: The TDD Ladder

You are part of a workshop teaching physicists test-driven development with agents.
Your behaviour depends on the PERSONA injected with each prompt. Follow it exactly.

## Persona: literal (Levels 0–1)
- Do what is asked as a capable, literal assistant.
- Make reasonable assumptions without asking. Do not volunteer process advice.
  (This is deliberate: the group is observing what happens without discipline.)

## Persona: coach (Levels 2–4)
- When asked to interview the group, ask one focused question at a time about
  behaviour; never suggest the answer.
- Write ONE test per cycle, for the behaviour named in the current RED phase.
- Never invent expected numerical values. Ask the group for them, or derive them
  symbolically and show the derivation for the group to check.
- In GREEN, write the minimum code to pass. Never modify tests. If you believe a test
  is wrong, say so and stop; the group decides whether to return to RED.
- Never special-case inputs to satisfy a test.
- Always show the pytest command and its output. Never claim tests pass without
  running them.
- Never loosen a tolerance; ask what justifies it.

## Persona: collaborator (Level 5)
- Normal helpful behaviour; evidence-first.

## Never
- Read .vault/ or the mutants, run ./tdd transitions, ./tdd score or ./gate unlock,
  or install packages.
```

---

## 10. Group Leader Guide

### Before the Session

- `./preflight` (checks pytest, the hooks, the `./tdd` TTY transitions, git identity).
- Read Sections 3 and 4 of this doc. **Don't** read Section 8 in detail; you'll coach Level 2 better if you also discover the decisions.
- Arrange the windows: **Claude** (large) and **Gate** (used for `./tdd` and `./gate`). Make sure everyone can see the scorecard output when it appears.

### Opening (60 Seconds)

> "We're going to build the same small feature several times, starting badly *on purpose*, and an objective scorecard will tell us how good our tests really are each time. For the first two levels Claude is set to be literal and not to ask questions. That's deliberate. Watch what it decides for us. After that we take control: we make the decisions, we compute the expected answers, and the tooling won't let anyone, Claude included, edit tests while we're making them pass. Roles: [assign]. The keyboard rotates every level."

### Coaching by Level

| Level | Watch for | Ask |
|---|---|---|
| 0 | Satisfaction with the plot | "What did the score say? Which decisions did Claude make for us?" |
| 1 | Missing the moment red should have happened | "Scribe, did any test fail before code existed? Where did 0.4472 come from?" |
| 2 | One person deciding everything; Claude steering the answers | "Do we all agree on what the error bar *means*? What does the plot reader assume?" |
| 3 | Claude writing several tests; numbers from Claude; impatience | "Sceptic, did *you* compute that value? Navigator, is this one behaviour?" |
| 4 | Arbitrary Monte Carlo tolerances | "What's the binomial σ for your N? Is your bound 3σ?" |

### Managing the Group

- **The hook block in green** ("tests are frozen") often sparks the best discussion of the session. Let it run for a minute.
- **The TDD sceptic** ("this is slow, I'd just write it"): agree it's slower for this tiny function, and point at the Level 0 scorecard. The discipline is insurance; the scorecard is the premium being priced.
- **2 people:** you are Coach + Navigator + phase-runner; the partner is Driver + Sceptic (computes oracles).
- **5 people:** at Level 3, two people independently hand-compute each expected value, and the cycle proceeds only if they agree. This models independent verification and keeps everyone busy.
- **Quiet member:** owns the gate terminal (`./tdd` transitions). Every cycle runs through them.

### Time Checkpoints

| T (since Go) | Expected | If behind |
|---|---|---|
| 5 min | Level 0 scored | Don't polish; score and move on |
| 11 min | Level 1 scored | Same |
| 21 min | `SPEC.md` done; client spec read | Cap the interview at 8 minutes |
| 36 min | ≥ 5 cycles | Fine to stop at 5 good cycles |
| 44 min | Level 4 attempted | Even one property test plus a re-score shows the jump |

### If Things Break

| Problem | Action |
|---|---|
| `./tdd green` refuses | Read the reason aloud. It's usually "tests not committed" or "failing for the wrong reason". That *is* the lesson. |
| Hook not blocking test edits | Check `/hooks`; call the facilitator. As a backstop, `./tdd` transitions still detect it. |
| Score is slow | Statistical tests may be too big; reduce N (and recompute the bound!) |

---

## 11. Show-and-Tell Prompts

- "Show your ladder: mutants killed at Levels 0, 1, 3 and 4."
- "Which client decision did nobody anticipate?"
- "The moment the hook stopped Claude editing a test: what did you decide?"
- "One TDD habit you'll actually use next week."

---

## 12. Build Notes

1. Write the correct reference implementation and the full client acceptance suite (~12 tests) from `CLIENT_SPEC.md`.
2. Write the 16 mutants. Verify that each fails at least one acceptance test and that each is killable by a reasonable Rung-5 suite.
3. Write your own Rung-4 and Rung-5 suites to confirm the targets (≥ 9/16, ≥ 14/16) are achievable in the time.
4. Build `./tdd`:
   - phase state and transition checks (git diff, pytest JUnit XML parsed with the standard library for failure types);
   - TTY requirement on transitions;
   - `score`: temp-dir runs, swapping `binning.py` for each mutant and for the reference.
5. Create the `level1-start` tag (stub + empty tests).
6. **Calibrate:**
   - Literal-persona Haiku at Levels 0–1 should score low. If it scores well, the persona isn't literal enough, or Haiku is better than expected (a good problem; tighten the scorecard).
   - Coach-persona Haiku must not hand out expected values.
   - Score runtime must stay under ~20 s.

---

## 13. Open Questions for Iteration

1. Is the literal persona at Levels 0–1 too contrived? The alternative is no persona instruction, with whatever Haiku does naturally. The scorecard will still likely show the gap, but less reliably.
2. Should the client spec be negotiable? For example, groups could argue S5 should be the midpoint, with the facilitator playing the client.
3. Swap the H(z) framing for a GW one (e.g. binned SNR versus frequency) for GW-heavy groups? The function is identical.
4. Should the scorecard ladder be shown room-wide (all groups' curves on one chart) at the show-and-tell?
