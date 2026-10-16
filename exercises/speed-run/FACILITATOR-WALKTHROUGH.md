# Facilitator Walkthrough: Speed Run

Private. Contains gate answers and spoilers. Never copy into `dist/`, and keep it away from participants.

This is the operating guide to the exercise. It has two readers:

- **The facilitator** (the organiser) builds the participant repo, rehearses it, sends it to the group leaders and holds the master passphrase. Read all of it.
- **Group leaders** set up their own laptop from the bundle the facilitator sends, and coach one group. Start at [section 3](#3-group-leaders-set-up-your-laptop); sections 1 and 2 are the facilitator's.

The lecture, roles by group size, the run-sheet and the trial are in `docs/00-facilitator-guide.md` in the builder repository.

Every timing and size below was **measured on an M1 Max (Python 3.13, numpy 2.3, Apple clang 21); calibrate on your own laptop** before you quote a number to a group. The shape of the results (exponent 2, memory wall at 20k, a few counts moving at the bin edges) holds on any Apple-silicon laptop; the seconds will not.

## 1. Facilitator: build and rehearse

Once per machine, do steps 2 and 3 of "Run the workshop" in the repository [`README.md`](../../README.md#run-the-workshop): the requirements and the master passphrase. Then:

```zsh
cd <this repository>
python3 tools/build.py speed-run --master-passphrase-file ~/.config/workshop/master-passphrase --keep-venv
cd dist/speed-run
./preflight --setup      # only if .venv is missing; creates .venv and installs the pins (network, once)
./preflight              # must end with "Preflight passed"; also compiles a tiny C library with clang
```

Then do the Claude Code checks in section 3, step 4, play the whole exercise through once on Haiku using section 5, and reset (section 7). Do at least one `./race submit` in the rehearsal: it re-times the calibration on every submission (about 20 s wall on an M1 Max), and you want to know that time on your machine.

- `--keep-venv` preserves an existing `dist/speed-run/.venv` across rebuilds. Everything else in `dist/speed-run` is regenerated, including the git history, so rebuild only between runs.
- The participant `.venv` is made with `/opt/homebrew/bin/python3.13` when that exists, otherwise `python3`. Pass `--setup-python /path/to/python3` to the build to bake in another Python 3.11+.
- The master passphrase stays in `~/.config/workshop/master-passphrase`, outside every repo. The build reads it; the repo stores only a check value. You type it at the prompt for `./gate skip --master`, `./gate allow-model` and `./race install-solution`.

### Optional: the Opus control

Before the session, find out what the strongest available model does undirected. Reveal it at the show-and-tell: do the room's directed Haiku entries beat an undirected strong model? Either answer is a good discussion.

1. Build a separate copy, so no group's repo is touched: `python3 tools/build.py speed-run --master-passphrase-file ~/.config/workshop/master-passphrase --out ~/opus-control`, then `cd ~/opus-control && ./preflight --setup && ./preflight`.
2. In a terminal, `./gate skip --master` three times to reach Level 3 (the earlier levels freeze `paircount/`), then `./gate allow-model opus`.
3. `claude`, `/model` to Opus, leave plan mode, and give the bare instruction "make `count_pairs` as fast as possible". Add nothing.
4. Commit, then `./race submit` in the terminal. Record the score and whether it passed exact.

## 2. Facilitator: give the repo to group leaders

Each leader gets a copy of the built participant repo as a git bundle: one file that clones into a complete repo. Never send them, or point participants at, the builder repository; it holds the sources and the answers.

1. Start from a clean repo. A bundle carries everything in the repo, including rehearsal commits and branches, so rebuild (section 1) or reset (section 7) first.
2. Check it and make the bundle:

   ```zsh
   cd dist/speed-run
   git status --short && git log --oneline && git branch   # expect no changes, one commit "Workshop start", only main
   git bundle create ~/Desktop/speed-run.bundle --all       # about 10 MB (the mock catalogues)
   ```

3. Send each leader the bundle and this walkthrough file. Ask them to work through section 3 before the leaders' briefing, so problems surface early. A private git remote works too: push `main` and the `start` tag, and send the clone URL instead.
4. Decide who types the master passphrase. Power-ups, skips and installed solutions ask for it in the group's own gate terminal; a leader's laptop never needs the passphrase file. By default you hold it and type it when a leader calls you over. If a leader will run a group without you in the room, such as a trial, tell them the passphrase. It opens every repo built from the same passphrase file, so if that matters, build their copy from a different passphrase file into another directory (`--out`).

## 3. Group leaders: set up your laptop

Do this a few days before the session, with a network connection. You need an Apple-silicon Mac with:

- The Xcode Command Line Tools: `xcode-select --install`. They provide `git` and `clang`; preflight fails without `clang`, which the race's C route needs.
- Python 3.11 or newer, for example `brew install python@3.13`.
- Claude Code 2.1.295 or newer (`claude --version`), signed in to a Claude account that can use Haiku, and Sonnet for power-ups.
- A git identity, because the exercise commits: `git config --global user.name "Your Name"` and `git config --global user.email you@example.org`.

Do not install anything else. If preflight asks for something, check with the facilitator first.

This exercise needs Claude Code: its lessons depend on Claude Code hooks (the personas, the model lock and the guard), so groups on another agent should do Explorer instead.

1. Clone the bundle the facilitator sent (adjust the path to wherever you saved it):

   ```zsh
   git clone ~/Downloads/speed-run.bundle speed-run && cd speed-run
   ```

2. `./preflight --setup` creates `.venv` and installs the pinned numpy, scipy, matplotlib and pytest (a minute or so; the only step that needs the network apart from Claude Code). If it says your Python is too old, it prints the command to run with a newer one.
3. `./preflight` must end with "Preflight passed". The first run also sets the workshop up at level 0.
4. Run `claude` in the repo and accept the workspace trust dialog; the guard rails do not load until you do. Then, in Claude Code (about a minute):
   1. `/hooks`: four events must be listed (SessionStart, UserPromptSubmit, PreToolUse, PreModelSwitch). If the list is empty, the trust dialog was not accepted: `/exit` and run `claude` again.
   2. `/status`: the model line must say Haiku.
   3. `/model` and pick Sonnet (or Default): it must be refused with "Today's exercise uses haiku. Ask a facilitator for a power-up." Picking Haiku again is allowed.
   4. `/exit`.
5. Rehearse: in a normal terminal, `make bench N=500 IMPL=reference` should print the counts check, the time and a "recorded as ... (level 0)" line. Then play Level 0 yourself following section 5, and reset (section 7) so the group's log and board start empty.

## 4. Running the session

### Two windows

| Window | Command | Who types |
|---|---|---|
| Claude (large) | `claude`, in the repo | the Driver |
| Gate (small) | a fresh Terminal window in the repo, then `./gate …`, `./race submit` | the humans |

Optional third: Activity Monitor, sorted by memory, so the group watches Python's memory climb at Level 1.

Open the gate terminal from Terminal itself, not from inside Claude Code: the gate refuses to run from Claude's shell and says so.

The session starts in plan mode on Haiku. `Shift+Tab` leaves plan mode once the group has agreed a plan. `/model` to anything but Haiku is refused until a power-up is granted. Choosing Haiku in `/model` is allowed, because Haiku is the allowed model; that is not a bypass.

**Which model is it, really?** Trust `/status` (or a status line), not what Claude says about itself. Haiku models sometimes misreport their own name, so "I'm Claude Sonnet" in answer to "what model are you?" is not evidence of an override. A launch-time `claude --model …` or `ANTHROPIC_MODEL` is not blocked, and the start-up check only warns when Claude Code reports the model. If in doubt, quit and re-open with plain `claude`, then check `/status`.

### Opening (60 seconds, read aloud)

> "This is a race, but a wrong answer scores zero, and we must *declare* what correct means before we see results. Today's rhythm: measure, hypothesise, change one thing, run the check, commit. Claude is on a modest model. It won't know where the time goes unless we make it measure. Roles: [assign]. The keyboard rotates at each gate."

The race rules are in the repo's `README.md`; read them so you can answer questions quickly. You are the Coach: you ask questions and fix tooling, and you do not drive. Allocate the roles (described in the repo's `README.md`) by group size, as below. The Driver rotates at each gate through everyone except you, so every other member types; you drive only with two people or to fix a technical problem.

| Group size | Roles |
|---|---|
| 2 | You: Coach and Navigator. The other person: Driver, Sceptic and Scribe. |
| 3 | Driver (rotating), Sceptic. You: Coach, Navigator and Scribe. |
| 4 | Driver (rotating), Navigator, Sceptic. You: Coach and Scribe. |
| 5 | Driver (rotating), Navigator, Sceptic, Scribe. You: Coach. |

- **Competitive energy is good**, but keep the Sceptic powerful. A team that submits fast wrong answers learns the wrong lesson. Read every refusal aloud: it is the lesson, not a bug.
- **5 people:** at Level 3, split into two idea pairs who each propose an optimisation. The Navigator chooses which to try first. The Driver still types; there is one Claude session.
- **The HPC expert:** ask them to direct Claude without naming the technique ("ask it questions that lead it to cell lists").
- **A quiet member** can own `./race submit` at Level 3: a visible, important role.

### Time checkpoints

45 minutes: 1 to start, then 7, 10, 14 and 11 for Levels 0 to 3, and 2 spare.

| From Go | Expected | If behind |
|---|---|---|
| 8 min | Level 0 done | Take the hint; don't skip the profile |
| 18 min | Level 1 done | If stuck on memory, take hint 2 (chunking) |
| 32 min | Level 2 done | The facilitator can install the Level 2 solution (section 6) so the group still races |
| 40 min | First Level 3 submission | The Scribe records the best score, the division and the commit hash |

### Commands

Useful at any time in the gate terminal: `./gate status`, `./gate brief`, `./race status`, `./race log`, `./race board`, `./gate hint` (tiers unlock at 0, 5 and 10 minutes on the level). The repo's `README.md` lists every command the group uses.

Need the master passphrase, which the facilitator holds, so call them over: `./gate allow-model sonnet` (a power-up to Sonnet), `./race install-solution <level>` (copies the reference solution for a level) and `./gate skip --master` (open the next level for a stuck group, with a reason). All are logged.

## 5. Level by level

### Level 0: Measure before you touch anything (7 min, coach)

1. Driver asks Claude for `make bench N=500 IMPL=reference`, then 1000, then 2000, then `make profile`, then `make fit`. A group that types `make bench N=1000` without `IMPL=reference` runs the default `IMPL=fast`; those runs do not count towards the gate, which asks for reference records.
2. Expected (M1 Max): about 0.22 s at N = 2000, exponent about 2.0 (`make fit` prints it), predicted time at 200,000 about 37 minutes; the briefs say "about an hour". Profile: `math.sqrt` called 499,500 times at N = 1000.
3. Gate terminal: `./gate unlock`. Answer **499500** (N(N-1)/2). Reflection: the predicted minutes at 200,000 and how it was reached (the fit, or (200000/2000)² × t(2000)).

Observe: does Haiku offer to optimise before measuring? How many of the group can say why the exponent is 2? Does anyone read the profile superficially?

Ask: "What's our predicted runtime at 200k? Is a 10× gain enough?" and "How many of those calls are pairs we actually need?"

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

Ask: "Sceptic, what's the memory estimate? Check the arithmetic."

### Level 2: Reduce the work, defend the answer (14 min, coach)

1. A cell list or `cKDTree` gets to 200k. Expected (M1 Max): numpy cell list about 4 s at 200k with r_max = 10 (77 s if it wrongly used 20). The 4 s is the hidden calibration counter as measured by the self-test; the build plan's 11.5 s was a simpler probe. The limit is 60 s and 1.5 GB.
2. The likely first failure is a diff table: a handful of counts moving between adjacent bins. Causes, planted on purpose: comparing `s < e*e` instead of `sqrt(s) < e`; `cKDTree` using `<=`; `np.histogram`'s closed last edge. Fixes: copy the reference arithmetic exactly (exact division passes), or declare `toleranced`.
3. Gate: a `fast` run at 200k made with the current `fast.py` and `race.toml` must pass in the declared division, under 60 s, and 1.5 GB. Answer **(c)**: golden 100 allows 0.05 × 10 = 0.5, so a shift of 1 fails; golden 1,000,000 allows 0.05 × 1000 = 50, so a shift of 10 passes.
4. Judge the **justification**, not the number. The Poisson argument is the point. The build verified that each wrong-semantics variant passes at `sigma_fraction = 0.1`; do not tell groups that.

Try deliberately: ask Claude to "just use `np.allclose`". It cannot edit `bench/`. Ask it to put a sigma in `race.toml`: refused. Edit `fast.py` after a passing run, then `./gate unlock`: refused ("fast.py changed since that run"). That is the stale-evidence rule.

Observe: does anyone say "it is just floating point" before opening the diff table? Does the group write the division into `LOG.md` before the passing run?

Ask: "Show me the per-bin differences. *Why* do they differ? Which division are we entering?"

### Level 3: Open race (11 min, collaborator)

1. Humans commit, then `./race submit` in the gate terminal. It runs the entry on a hidden 200k catalogue, then the calibration (a numpy cell list, re-timed every time). Score is calibration time divided by yours, so a numpy cell list scores about 1.0.
2. The C route (cell list in C, `-O2 -shared -ffp-contract=off`) is the expected winner: several times the calibration; calibrate on your laptop. A C entry built with default flags fails `exact` on the hidden catalogue, scores 0, and is on the board. That is the FMA trap, and a good story.
3. Gate: at least one submission that passed at this level. No question; reflection only: biggest wrong turn and the evidence.
4. `./race submit` re-times the calibration entry every time (about 20 s wall), so scores stay fair on a busy machine. A failed hidden submission shows only the failing-bin count and the largest absolute difference; the per-bin table is on `make check N=200000`.
5. Prizes: Fastest Exact, Fastest Toleranced, Best "caught it" story. Read `./race board`.

Observe: does anyone submit without a commit? Does anyone start two processes? Does a failing 0 get discussed or hidden?

Ask: "Was that number from the harness? Is it committed?"

Intel Macs: without FMA instructions (no `-mfma`), clang does not contract, so the FMA trap, the `l3_c_default` sample and the Level 3 hint do not fire. Apple silicon is assumed.

Honest limit: the Speed Run's crypto gates reduce to the human answer, because the check output is fixed. The answer spaces (one value at Level 0, 23 at Level 1, four letters at Level 2) are the only secret. The Level 3 claim that a hard-coded answer scores 0 is soft against code the harness runs, which can read `.gatekit/racetool/golden.json`. See `gatekit/README.md` section 11 in the builder repository.

## 6. When something goes wrong

| Symptom | Do |
|---|---|
| Group stuck | `./gate hint` (3 tiers, then the gate answer at 13 minutes), then a question, then `./gate allow-model sonnet`, then `./race install-solution <level>` (gate terminal; copies the reference solution for that level over `paircount/` and logs it). Re-run the bench for that level so the gate sees current evidence, then `./gate unlock` as normal. `./gate skip --master` is the last resort. The last three need the master passphrase. |
| `./gate` or `./race` says it is "for humans, in the gate terminal" | It was run from Claude's shell, or from a window opened from Claude Code. Use a fresh Terminal window. |
| Laptop freezing at Level 1 | Close other apps. Kill the Python process in Activity Monitor; the harness should do it at 2.5 GB. The harness polls every 0.1 s, so a very large single allocation can outrun it on a small-memory laptop. If that happens it is the lesson, but do not let it cost the group the hour. |
| Hooks not firing | `/hooks`; if empty, exit, re-open `claude` in the repo and accept trust. |
| Different speeds on different laptops | The score is normalised by the calibration run on the same machine. Say so. |
| `./race submit` refuses | Read the reason aloud. Usually uncommitted `paircount/` or `race.toml`, or an invalid `race.toml` (sigma above 0.2, justification under 80 characters). |
| Gate says the run is stale | `fast.py` or `race.toml` changed since the run. Re-run `make bench`. |
| Bench record "bad signature" | Someone edited `.workshop/race/bench.jsonl`. `./race log` flags it; those records are ignored. |
| Claude names the wrong model | Not an override. Check `/status`. See "Which model is it, really?" in section 4. |

## 7. Reset between runs

In the repo (`dist/speed-run` for the facilitator, your clone for a leader):

```zsh
./gate reset                       # confirms, wipes .workshop/ (including the bench log and submissions)
git reset --hard start && git clean -fdx -e .venv -e .workshop   # restores fast.py, race.toml and LOG.md; removes ignored .so files; keeps .venv
```

The facilitator can instead rebuild (`tools/build.py … --keep-venv`), which also gives fresh packs and secrets; leaders then need a new bundle.

## 8. What to record

- `.workshop/state.json`: per-level times, hints, failed attempts, skips, model power-ups, submissions.
- `.workshop/race/bench.jsonl` (`./race log`): every run, including the killed ones. These are the wrong turns.
- `./race board` for the final scores, and the divisions entered.
- `LOG.md`: the Scribe's notes and the reflections.

Copy all four out before `./gate reset`, and leaders send their copies to the facilitator. For the show-and-tell, ask each group: which division, and why; the biggest wrong turn and the evidence that showed it; and then reveal the Opus control.
