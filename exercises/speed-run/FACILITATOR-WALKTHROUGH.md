# Facilitator Walkthrough: Speed Run

Private. Contains gate answers and spoilers. Never copy into `dist/`.

Every timing and size below comes from the build PLAN and was **measured on an M1 Max (Python 3.13, numpy 2.3, Apple clang 21); calibrate on your laptop** before you quote a number to a group. The shape of the results (exponent 2, memory wall at 20k, a few counts moving at the bin edges) will hold on any Apple-silicon laptop; the seconds will not.

## 1. Build and set up (once per machine)

```zsh
cd <this repository>
python3 tools/build.py speed-run --master-passphrase-file ~/.config/workshop/master-passphrase --keep-venv
cd dist/speed-run
./preflight --setup      # only if .venv is missing; creates .venv and installs the pins (numpy, scipy)
./preflight              # must end with "Preflight passed"; also confirms clang is present for the optional C route
claude                   # accept the workspace trust dialog once, then the checks below, then /exit
```

Checks inside that first `claude` session (about a minute):

1. `/hooks`: all four events must be listed (SessionStart, UserPromptSubmit, PreToolUse, PreModelSwitch). If the list is empty, the trust dialog was not accepted: exit and re-open `claude`.
2. `/status`: the model line must say Haiku.
3. `/model` and pick Sonnet (or Default): it must be refused with "Today's exercise uses haiku. Ask a facilitator for a power-up." Picking Haiku again is allowed.

Then a 30-second smoke test in a normal terminal: `make bench N=500 IMPL=reference` should print the counts check, the time and a "recorded as ... (level 0)" line; then `./gate reset`, so the group's log and board start empty. `./race submit` re-times the calibration on every submission (about 20 s wall), so do your own rehearsal submit before the day if you want to know the wall time, then `./gate reset`, so the group's log and board start empty.

`--keep-venv` preserves an existing `dist/speed-run/.venv` across rebuilds. Everything else in `dist/speed-run` is regenerated, including the git history, so rebuild only between runs. The master passphrase never goes into a repo.

## 2. Two windows

| Window | Command | Who types |
|---|---|---|
| Claude (large) | `cd dist/speed-run && claude` | the Driver |
| Gate (small) | `cd dist/speed-run` in a fresh Terminal window (not one opened from Claude Code), then `./gate …`, `./race submit` | the humans |

Optional third: Activity Monitor, sorted by memory, so the group watches Python's memory climb at Level 1.

The session starts in plan mode on Haiku; `Shift+Tab` leaves it. Trust `/status`, not what Claude says about its own model (see the TDD walkthrough, "Which model is it, really?").

Useful at any time in the gate terminal: `./gate status`, `./gate brief`, `./race status`, `./race log`, `./race board`, `./gate hint` (tiers unlock at 0, 5 and 10 minutes on the level).

## 3. Level by level (45 minutes: 1 start, 7, 10, 14, 11, 2 spare)

Checkpoints from Go: Level 0 done by about 8 min, Level 1 by about 18, Level 2 by about 32, first Level 3 submission by about 40.

### Level 0: Measure before you touch anything (7 min, coach)

1. Driver asks Claude for `make bench N=500 IMPL=reference`, then 1000, then 2000, then `make profile`, then `make fit`. A group that types `make bench N=1000` without `IMPL=reference` runs the default `IMPL=fast`; those runs do not count towards the gate, which asks for reference records.
2. Expected (M1 Max): about 0.22 s at N = 2000, exponent about 2.0 (`make fit` prints it), predicted time at 200,000 about 37 minutes; the briefs say "about an hour". Profile: `math.sqrt` called 499,500 times at N = 1000.
3. Gate terminal: `./gate unlock`. Answer **499500** (N(N-1)/2). Reflection: the predicted minutes at 200,000 and how it was reached (the fit, or (200000/2000)² × t(2000)).

Observe: does Haiku offer to optimise before measuring? How many of the group can say why the exponent is 2?

Try deliberately:

- Ask Claude to "vectorise fast.py now". The guard refuses: "Level 0 is measurement only." Read it aloud.
- Ask Claude to run the reference at N = 200000. The harness refuses above N = 4000 and quotes the extrapolated time. That is the baseline made visible.

### Level 1: Vectorise, and survive the memory wall (10 min, coach)

1. The unlock opens `fast.py`. Driver asks for a numpy version with the same arithmetic. The persona makes Claude state a memory estimate before a 20k run; the Sceptic checks it.
2. Gate: a `fast` run at N = 20000 made with the current `fast.py` must pass exact, run under 10 s, and peak under 1.5 GB. Answer **320** (200000² × 8 bytes = 320 GB; accepted 298 to 320, so GiB works).
3. Expected (M1 Max): a full N×N attempt at 20k needs 3.2 GB per temporary (10.2 GB peak when run unprotected, 9.4 s). Under the harness it is killed at the 2.5 GB cap and the record says so. A chunked version takes a few seconds. Chunks of 2000 rows measured 3.3 GB peak, which is too much for the 1.5 GB ceiling: a few hundred rows is the sweet spot. Let the group find this; it is the lesson.
4. The untouched pure-Python `fast.py` takes about 22 s at 20k on an M1 Max (110 ns × 2 × 10⁸ pairs), which is why the limit is 10 s: an unmodified entry cannot pass. A chunked numpy version takes about 3 s.

Try deliberately: tell the Driver to say "just run N=20000, no estimate". Claude's persona will still estimate. If someone runs it anyway, watch the harness kill it and print "killed: resident memory passed 2.5 GB; estimate before you run." Also: ask Claude to use `np.histogram` over all distances. It closes the last edge, so the pair planted exactly at r = 10 lands in the last bin and `exact` fails with a diff table.

Observe: the 20k estimate before the run. Is it in the log? Does the reflection quote the harness number?

### Level 2: Reduce the work, defend the answer (14 min, coach)

1. A cell list or `cKDTree` gets to 200k. Expected (M1 Max): numpy cell list about 4 s at 200k with r_max = 10 (77 s if it wrongly used 20). The 4 s is the hidden calibration counter as measured by the self-test; PLAN section 1's 11.5 s was the probe's simpler implementation. The limit is 60 s and 1.5 GB.
2. The likely first failure is a diff table: a handful of counts moving between adjacent bins. Causes, planted on purpose: comparing `s < e*e` instead of `sqrt(s) < e`; `cKDTree` using `<=`; `np.histogram`'s closed last edge. Fixes: copy the reference arithmetic exactly (exact division passes), or declare `toleranced`.
3. Gate: a `fast` run at 200k made with the current `fast.py` and `race.toml` must pass in the declared division, under 60 s, and 1.5 GB. Answer **(c)**: golden 100 allows 0.05 × 10 = 0.5, so a shift of 1 fails; golden 1,000,000 allows 0.05 × 1000 = 50, so a shift of 10 passes.
4. Judge the **justification**, not the number. The Poisson argument is the point. The build verified that each wrong-semantics variant passes at `sigma_fraction = 0.1`; do not tell groups that.

Try deliberately: ask Claude to "just use `np.allclose`". It cannot edit `bench/`. Ask it to put a sigma in `race.toml`: refused. Edit `fast.py` after a passing run, then `./gate unlock`: refused ("fast.py changed since that run"). That is the stale-evidence rule.

Observe: does anyone say "it is just floating point" before opening the diff table? Does the group write the division into `LOG.md` before the passing run?

### Level 3: Open race (11 min, collaborator)

1. Humans commit, then `./race submit` in the gate terminal. It runs the entry on a hidden 200k catalogue, then the calibration (a numpy cell list, re-timed every time). Score is calibration time divided by yours, so a numpy cell list scores about 1.0.
2. The C route (cell list in C, `-O2 -shared -ffp-contract=off`) is the expected winner: several times the calibration; calibrate on your laptop. A C entry built with default flags fails `exact` on the hidden catalogue, scores 0, and is on the board. That is the FMA trap, and a good story.
3. Gate: at least one submission that passed at this level. No question; reflection only: biggest wrong turn and the evidence.
4. `./race submit` re-times the calibration entry every time (about 20 s wall), so scores stay fair on a busy machine. A failed hidden submission shows only the failing-bin count and the largest absolute difference; the per-bin table is on `make check N=200000`.
5. Prizes: Fastest Exact, Fastest Toleranced, Best "caught it" story. Read `./race board`.

Intel Macs: without FMA instructions (no `-mfma`), clang does not contract, so the FMA trap, the `l3_c_default` sample and the Level 3 hint do not fire. Apple silicon is assumed.

Honest limit: the Speed Run's crypto gates reduce to the human answer, because the check output is fixed. The answer spaces (one value at Level 0, 23 at Level 1, four letters at Level 2) are the only secret. The Level 3 claim that a hard-coded answer scores 0 is soft against code the harness runs, which can read `.gatekit/racetool/golden.json`. See `gatekit/README.md` section 11.

Observe: does anyone submit without a commit? Does anyone start two processes? Does a failing 0 get discussed or hidden?

## 4. The Opus control

Before the session, in a **copy** of the built repo (not the live one), give the strongest available model the bare instruction "make `count_pairs` as fast as possible" with no gate and no brief. Move the copy to Level 3 (`./gate skip --master` as needed), commit, run `./race submit` in a terminal, and record the score and whether it passed exact. Reveal it at the show-and-tell: do the room's directed Haiku entries beat an undirected strong model? Either answer is a good discussion.

## 5. When something goes wrong

| Symptom | Do |
|---|---|
| Group stuck | `./gate hint` (3 tiers), then a question, then `./gate allow-model sonnet`, then `./race install-solution <level>` (gate terminal, master passphrase; copies the reference solution for that level over `paircount/` and logs it). Re-run the bench for that level so the gate sees current evidence, then `./gate unlock` as normal. `./gate skip --master` is the last resort. |
| Laptop freezing at Level 1 | Close other apps. Kill the Python process in Activity Monitor; the harness should do it at 2.5 GB. The harness polls every 0.1 s, so a very large single allocation can outrun it on a small-memory laptop. If that happens it is the lesson, but do not let it cost the group the hour. |
| Hooks not firing | `/hooks`; if empty, exit, re-open `claude` in the repo and accept trust. |
| Different speeds on different laptops | The score is normalised by the calibration run on the same machine. Say so. |
| `./race submit` refuses | Read the reason aloud. Usually uncommitted `paircount/` or `race.toml`, or an invalid `race.toml` (sigma above 0.2, justification under 80 characters). |
| Gate says the run is stale | `fast.py` or `race.toml` changed since the run. Re-run `make bench`. |
| Bench record "bad signature" | Someone edited `.workshop/race/bench.jsonl`. `./race log` flags it; those records are ignored. |
| Claude names the wrong model | Not an override. Check `/status`. |

## 6. Reset between runs

```zsh
cd dist/speed-run
./gate reset                       # confirms, wipes .workshop/ (including the bench log and submissions)
git reset --hard start && git clean -fdx -e .venv -e .workshop   # restores fast.py, race.toml and LOG.md; removes ignored .so files; keeps .venv
```

A full rebuild (`tools/build.py … --keep-venv`) also works and gives fresh packs and secrets.

## 7. Giving the repo to group leaders

The participant repo is self-contained and must not include this file or `exercises/`.

```zsh
cd dist/speed-run
git bundle create ~/Desktop/speed-run.bundle --all
# leader: git clone speed-run.bundle speed-run && cd speed-run && ./preflight --setup && ./preflight
```

Leaders need Python 3.11+ (the harness reads `race.toml` with `tomllib`), numpy and scipy from the pins, git, Apple clang (Xcode command line tools) for the optional C route, and Claude Code 2.1.295 or later. Ask before installing anything on a leader's machine.

## 8. What to record

- `.workshop/state.json`: per-level times, hints, failed attempts, skips, model power-ups, submissions.
- `.workshop/race/bench.jsonl` (`./race log`): every run, including the killed ones. These are the wrong turns.
- `./race board` for the final scores, and the divisions entered.
- `LOG.md`: the Scribe's notes and the reflections.

Copy all four out before `./gate reset`. For the show-and-tell, ask each group: which division, why; the biggest wrong turn and the evidence that showed it; and then reveal the Opus control.
