# Exercise B — Speed Run: an Optimisation Race With a Correctness Gate

| | |
|---|---|
| **One-liner** | A correct but painfully slow pair counter for the two-point correlation function. Make it as fast as you can, without ever getting a wrong answer. |
| **Core lesson** | Measure before you optimise; a correctness gate is non-negotiable; *"correct"* is a scientific decision you must declare up front. |
| **Model** | Haiku throughout (keeps the race about direction, not model strength) |
| **Duration** | 45 min (four gated levels + open race) |
| **Group size** | 2–5 |
| **Languages** | Python (numpy, scipy); optional C via Apple `clang` |
| **Prep effort** | Low to moderate: reference code, a mock catalogue, golden counts, a benchmark harness |

---

## 1. The Story

> Your group measures galaxy clustering with the Landy–Szalay estimator. The pair counter at its heart was written years ago as a clear, obviously correct pure-Python double loop. It's fine for 2,000 galaxies. The new mock catalogue has **200,000**.
>
> Make it fast. Every submission is checked against **golden pair counts**, and a fast wrong answer scores zero.

---

## 2. Learning Objectives

1. **Measure first:** scaling exponents, profiles and memory estimates *before* changing code.
2. Make the **correctness check a hard gate** that every optimisation must pass.
3. Recognise that *"correct"* for floating-point code needs a **declared criterion** (exact versus toleranced), decided before seeing results.
4. Climb the optimisation ladder deliberately: interpreter → vectorisation → algorithm → compiled code → parallelism.
5. Distrust claimed speed-ups; insist on the **benchmark output**.
6. Commit every verified gain, so you can always fall back.

---

## 3. Repo Design

```
speed-run/
├── README.md                  # Level 0 brief + race rules
├── CLAUDE.md                  # teacher instructions
├── LOG.md
├── Makefile                   # make bench N=… | make xi | make check
├── gate                       # gate kit CLI
├── race                       # race submit (TTY, humans only) → prints score for the board
├── paircount/
│   ├── reference.py           # count_pairs(pos, edges) → int64 counts. Pure Python. Never edit.
│   └── fast.py                # count_pairs(pos, edges) — starts as a copy of reference; the race entry
├── xi/
│   └── landy_szalay.py        # uses fast.count_pairs for DD, DR, RR; prints ξ(r)
├── data/
│   ├── mock_2k.npy, mock_20k.npy, mock_200k.npy     # clustered mock in a 100 Mpc/h box
│   └── randoms_*.npy
├── bench/
│   └── harness.py             # timing (median of 3), peak RSS, correctness vs golden
├── .workshop/ …  .vault/ …  .claude/ …
```

### The Correctness Contract (Stated in the README)

- `count_pairs` counts unique pairs (i < j) with separation r in bins **[edgeₖ, edgeₖ₊₁)**.
- r is computed as `sqrt(dx*dx + dy*dy + dz*dz)` in float64. Non-periodic box. 20 log-spaced bins from 0.5 to 20 Mpc/h.
- The **golden counts** for each catalogue are stored as SHA-256 hashes (exact division) and as arrays (toleranced division).

### Two Divisions on the Leaderboard

| Division | Acceptance criterion |
|---|---|
| **Exact** | Counts identical to golden, bin by bin |
| **Toleranced** | Every bin within a declared relative tolerance ≤ 10⁻⁶. The tolerance and a one-paragraph *physical* justification must be written in `race.toml` and `LOG.md` **before** the first submission in this division. |

**Why two divisions:**

- The catalogue contains around 200 **planted "edge-straddler" pairs** whose separations sit within a few ulps of a bin edge.
- Mathematically equivalent reformulations classify some of them differently:
  - comparing r² with squared edges;
  - a library's ≤ versus < convention;
  - a different summation order;
  - fused multiply-add in compiled code.
- None of this matters scientifically. Out of ~10¹⁰ pairs, 200 is nothing. But it breaks bit-exactness.
- The group must *decide*, explicitly, what correctness means.

---

## 4. Levels

| Level | Title | Min | Gate: machine | Gate: human |
|---|---|---|---|---|
| 0 | Baseline and scaling | 6 | Bench log at ≥ 3 values of N | Scaling exponent; predicted runtime at N = 200k |
| 1 | Profile | 5 | Profile output saved | Count of a hot call at N = 1000 |
| 2 | Vectorise (and survive memory) | 10 | Exact or toleranced counts at N = 20k in < 30 s, peak RSS < 1.5 GB | Memory of the naive N×N approach at N = 200k |
| 3 | Change the algorithm | 12 | Correct counts at N = 200k in < 60 s | Measured scaling exponent of the new method |
| 4 | Open race | 12+ | `./race submit`: score on the board | (free text) What was your biggest wrong turn? |

### Level 0 — Baseline and Scaling (6 min)

**Brief:** "Before optimising anything, find out how bad it is. Measure runtime at several N, fit the scaling, and predict the runtime at N = 200,000."

**What the group does:**

- Directs Claude to run `make bench` at N = 500, 1000, 2000 and fit log t against log N.
- The Navigator writes down the predicted time for N = 200k (expected: hours).

**Typical Haiku behaviour:** it may start optimising immediately ("I can vectorise this!"). The persona brief says Level 0 is measurement only, and `fast.py` edits are blocked until Level 1 unlocks.

**Gate:**

- *Machine:* a bench log exists, with ≥ 3 values of N produced by the harness.
- *Human:*
  - "Measured exponent α?" (accept 1.85–2.15).
  - "Predicted runtime at N = 200k, in hours?" (accept within a factor of 2 of the harness's own extrapolation).

**Teaching point:** know your target and your baseline. A 100× speed-up of something that takes 8 hours still takes 5 minutes.

### Level 1 — Profile (5 min)

**Brief:** "Where does the time go? Profile N = 1000 with `cProfile`. Don't guess."

**Gate:**

- *Machine:* the profile output file exists and corresponds to the reference implementation.
- *Human:* "How many times is `math.sqrt` called for N = 1000?" (answer: 499,500 = N(N−1)/2).

This forces someone to *read* the profile and connect it to the algorithm. The pair loop is the cost, so the cure is either to make the loop cheaper (vectorise) or to do fewer iterations (a better algorithm). Seeing the number makes the second option obvious.

**Teaching point:** profiles turn intuition into evidence. The profile also shows the shape of the problem: N²/2 evaluations, most of which are pairs far beyond the 20 Mpc/h maximum separation.

### Level 2 — Vectorise, and Survive the Memory Wall (10 min)

**Brief:** "Rewrite `fast.py` using NumPy. It must pass the correctness gate at N = 20,000 within 30 s and use under 1.5 GB of memory. **Estimate memory before you run anything at 20k.**"

**What typically happens:**

- Claude writes an N×N distance matrix. It works at 2k.
- At 20k, it needs 20,000² × 8 bytes ≈ 3.2 GB *per temporary array*, with several temporaries. The process swaps or is killed.
- **This is intended.** The lesson is to estimate memory before running.
- The fix is **chunking** (blocks of rows) or computing the upper triangle in tiles.

**The Sceptic's job:** before anything runs at 20k, ask Claude for the memory estimate and check the arithmetic.

**Gate:**

- *Machine:* counts at N = 20k pass (either division), runtime < 30 s, peak RSS < 1.5 GB (harness via `resource.getrusage`).
- *Human:* "Peak memory of the naive N×N float64 distance matrix at N = 200k, in GB?" (≈ 320; accept 100–1000).

**Teaching point:** vectorisation trades time for memory. Always estimate both.

### Level 3 — Change the Algorithm (12 min)

**Brief:** "N² is the enemy. The largest separation you need is 20 Mpc/h in a 100 Mpc/h box. Use that. Pass the gate at N = 200,000 in under 60 seconds."

**Expected approaches:**

- **Cell lists:** grid the box into cells of side ≥ r_max, and only compare neighbouring cells.
- **`scipy.spatial.cKDTree`** methods.
- Sorting along one axis with a sliding window.

**Planted trap:** the edge-straddler pairs. Typical routes into it:

- `cKDTree` pair-counting conventions (≤ versus <).
- Comparing r² against squared edges.
- `scipy.spatial.distance.cdist` or `np.linalg.norm`, which may round differently.

The first algorithmic attempt often fails the **Exact** division by a handful of counts in a few bins.

**What the group should do:**

- **Not** loosen the check silently.
- Investigate: how many pairs differ, in which bins, and why?
- Then choose, explicitly:
  - (a) match the reference semantics exactly (e.g. compute r the same way, apply the same half-open convention), or
  - (b) enter the Toleranced division with a written justification.

**Typical Haiku behaviour:** it may claim the counts "match within floating-point error" without showing a diff, or switch the check to `np.allclose`. The Sceptic must demand the per-bin difference table.

**Gate:**

- *Machine:* N = 200k passes in either division, in < 60 s.
- *Human:* "Measured scaling exponent of your new method between N = 50k and 200k?" (accept 0.9–1.5).

**Teaching point:** algorithmic change beats micro-optimisation by orders of magnitude, but every reformulation is a new opportunity to be subtly wrong. The gate is what lets you be bold.

### Level 4 — Open Race (Remaining Time)

**Brief:** "Anything goes within the rules: stdlib, numpy, scipy, C compiled with `clang` via `ctypes`, `multiprocessing`. No new packages. Submit with `./race submit` in the gate terminal; write your score on the board."

**Scoring:**

- `./race submit` runs the hidden benchmark (DD on the 200k mock, median of 3).
- It also runs a built-in calibration implementation on the *same machine*.
- **Score = t_calibration / t_yours**, which normalises across M1–M4 laptops.

**Second planted trap (C entries):**

- Apple `clang` may contract `dx*dx + dy*dy + dz*dz` into fused multiply-adds by default. That changes rounding, and some straddler pairs move bins.
- A C entry that "should" be exact fails the Exact division.
- The fix is to control floating-point contraction (`-ffp-contract=off`) or to move to the Toleranced division.
- **Verify the compiler's default behaviour during the build.** Tune the straddlers so this trap fires.

**Rules of the race:**

- Every submission must pass its division's gate. A failed submission scores zero and is logged.
- **Commit before every submission** (`./race submit` refuses on a dirty tree), so every score maps to a commit.

**Prize categories** (so mixed-experience groups have something to aim for):

- **Fastest Exact**
- **Fastest Toleranced**
- **Best speed-up per line changed** (`git diff --stat` against Level 3)
- **Best "caught it" story**

**The "Opus control" (facilitator):**

- Before the session, give the strongest available model the bare instruction "make `count_pairs` as fast as possible" with no gate, and record its score and whether it passes the Exact gate.
- Reveal this at the show-and-tell. Do the room's directed weak-model entries beat an undirected strong model? Either answer is a good discussion.

---

## 5. Teacher Instructions (Draft `CLAUDE.md`)

```markdown
# Workshop: Speed Run

You are assisting a group of physicists in an optimisation race. Speed only counts if the
correctness gate passes. The current level's rules are injected with each prompt.

## Always
- Report timings and correctness only from actual runs of bench/harness.py. Show the
  command and the output. Never estimate a speed-up you have not measured.
- Before running anything at large N, state the expected memory use and runtime, with
  the arithmetic.
- Never edit paircount/reference.py, bench/, data/ or the golden counts.
- Never change a correctness check, tolerance or comparison function. If the group wants a
  tolerance, they declare it in race.toml themselves.

## Coach mode (Levels 0–3)
- Do the measurement or experiment the group asks for. If asked to "just make it fast",
  ask what the profile says and what their target is.
- When counts differ from golden, produce a per-bin difference table and stop. Let the
  group decide what to do.

## Collaborator mode (Level 4)
- Propose and implement optimisations freely, but run the harness after every change and
  commit only verified improvements.

## Never
- Read .vault/ or golden arrays directly, run ./gate unlock or ./race submit, or
  install packages.
```

---

## 6. Answer Key (Facilitator Only)

### Expected Ladder

These are indicative figures; calibrate them on your hardware.

| Step | Typical approach | Order of speed-up vs pure Python at fixed N |
|---|---|---|
| Baseline | Double loop | 1× |
| Vectorised, chunked | NumPy blocks of ~2k rows | 10²× |
| Algorithmic | Cell list in NumPy, or `cKDTree` | 10³–10⁴× at N = 200k (vs extrapolated baseline) |
| Compiled | Cell list in C via `ctypes` | Further 3–10× |
| Parallel | `multiprocessing` over cells | Further ×(cores), minus overhead |

### Traps

| Trap | Where it bites | Recognising it | Resolution |
|---|---|---|---|
| Memory wall | Level 2, N×N at 20k | Swap, `MemoryError`, or the process is killed | Chunking; estimate first |
| Straddlers: r² comparison | Level 3+ | Exact gate fails by single counts in a few bins | Compute r as the reference does, or go Toleranced |
| Straddlers: library convention | Level 3, tree-based counting | Off-by-few counts at bin edges | Read the library's distance convention; convert ≤ to < correctly |
| Straddlers: FMA | Level 4, C | C entry fails Exact, Python version passes | `-ffp-contract=off`, or Toleranced |
| Self-pairs and double counting | Any | Counts off by ~N or ×2 | i < j only; check the smallest bin |

### Building the Straddlers

1. For each bin edge e, generate candidate separation vectors whose float64 r differs from e by −3 to +3 ulps.
2. Compute the bin under the reference semantics *and* under r²-versus-e² comparison (and FMA, using a small C helper).
3. Keep the candidates where the classifications disagree.
4. Embed around 200 such pairs at random positions and orientations within the mock, far from other structure.
5. Confirm the golden counts with the reference implementation at N = 2k and 20k. Compute the 200k golden counts with your own fast implementation that is verified bit-identical to the reference at 20k.

---

## 7. Group Leader Guide

### Before the Session

- Run `./preflight`, which confirms numpy, scipy and `clang` are available and that `make bench N=500` runs.
- Read the race rules in `README.md` so you can answer rule questions quickly.
- Arrange the windows: **Claude**, **Gate** (also used for `./race submit`), and optionally Activity Monitor for watching memory at Level 2.

### Opening (60 Seconds)

> "This is a race, but a wrong answer scores zero, and we must *declare* what correct means before we see results. Today's rhythm: measure, hypothesise, change one thing, run the check, commit. Claude is on a modest model. It won't know where the time goes unless we make it measure. Roles: [assign]. The keyboard rotates at each gate."

### Coaching by Level

| Level | Watch for | Ask |
|---|---|---|
| 0 | Optimising before measuring | "What's our predicted runtime at 200k? Is a 10× gain enough?" |
| 1 | Reading the profile superficially | "How many of those iterations are pairs we actually need?" |
| 2 | Running 20k without a memory estimate | "Sceptic, what's the memory estimate? Check the arithmetic." |
| 3 | `allclose` creeping into the check; "it's just floating-point error" | "Show me the per-bin differences. *Why* do they differ? Which division are we entering?" |
| 4 | Untested speed-ups; no commits | "Was that number from the harness? Is it committed?" |

### Managing the Group

- **Competitive energy is good**, but keep the Sceptic powerful. A team that submits fast wrong answers learns the wrong lesson.
- **2 people:** you are Coach + Navigator; the partner is Driver + Sceptic. Use the Scribe's `LOG.md` sparingly.
- **5 people:** at Level 4, split into two *idea pairs* who each propose an optimisation. The Navigator chooses which to try first. The Driver still types; there is one Claude session.
- **The HPC expert:** ask them to direct Claude without naming the technique ("ask it questions that lead it to cell lists"). Their expertise becomes the group's, not just theirs.
- **The quiet member:** make them the timekeeper at Level 4, owning `./race submit`. A visible, important role.

### Time Checkpoints

| T (since Go) | Expected | If behind |
|---|---|---|
| 11 min | Level 1 done | Take the Level 1 hint; don't skip the profile |
| 21 min | Level 2 done | If stuck on memory, take hint 2 (chunking) |
| 33 min | Level 3 done | Facilitator can skip to Level 4 with a provided Level 3 solution, so the group still races |
| 45+ min | Final submission | The Scribe records the best score, the division and the commit hash |

### If Things Break

| Problem | Action |
|---|---|
| Laptop freezes at Level 2 | Expected if no estimate was made. Kill the Python process in Activity Monitor; that *is* the lesson. Restart the Claude session if needed (`claude --continue`). |
| `./race submit` refuses | It needs a clean, committed tree and a filled-in `race.toml` |
| Different laptops give different speeds | The score is normalised; reassure the group |

---

## 8. Show-and-Tell Prompts

- "Which division did you enter, and how did you decide?"
- "What was your biggest wrong turn, and what evidence showed it?"
- "Reveal: the undirected strong model scored X and [passed / failed] the Exact gate."

---

## 9. Build Notes

1. Write the reference, the harness and the golden-count pipeline; verify the reference against an independent slow implementation at 2k.
2. Generate a **clustered** mock (e.g. a Neyman–Scott or Soneira–Peebles process) so ξ(r) is non-trivial and the result looks like science. Add the straddler pairs.
3. Write `race`: TTY check, clean-tree check, calibration run, timing, gate, score printout.
4. Provide a private Level 3 solution for facilitator skips.
5. **Calibrate:**
   - Haiku with a naive "make it fast" should hit the memory wall or the straddler trap.
   - Guided Haiku should reach Level 4 by about 33 minutes.
   - Check the FMA trap actually fires on the pinned `clang` version.

---

## 10. Open Questions for Iteration

1. Room-wide leaderboard (more energy) or within-group only (less pressure for novices)?
2. Allow `numba` if it's already installed on leader machines? It's a common real-world step, but a third-party dependency and a big shortcut.
3. Periodic boundary conditions as a "boss level" for groups who finish early?
4. Should the Toleranced division's justification be peer-reviewed by another group at the show-and-tell?
