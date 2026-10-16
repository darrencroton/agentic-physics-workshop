# Facilitator Walkthrough: The TDD Ladder

Private. Contains gate answers and spoilers. Never copy into `dist/`, and keep it away from participants.

This is the operating guide to the exercise. It has two readers:

- **The facilitator** (the organiser) builds the participant repo, rehearses it, sends it to the group leaders and holds the master passphrase. Read all of it.
- **Group leaders** set up their own laptop from the bundle the facilitator sends, and coach one group. Start at [section 3](#3-group-leaders-set-up-your-laptop); sections 1 and 2 are the facilitator's.

The lecture, roles by group size, the run-sheet and the trial are in `docs/00-facilitator-guide.md` in the builder repository.

## 1. Facilitator: build and rehearse

Once per machine, do steps 2 and 3 of "Run the workshop" in the repository [`README.md`](../../README.md#run-the-workshop): the requirements and the master passphrase. Then:

```zsh
cd <this repository>
python3 tools/build.py tdd-ladder --master-passphrase-file ~/.config/workshop/master-passphrase --keep-venv
cd dist/tdd-ladder
./preflight --setup      # only if .venv is missing; creates .venv and installs the pins (network, once)
./preflight              # must end with "Preflight passed"
```

Then do the Claude Code checks in section 3, step 4, play the whole exercise through once on Haiku using section 5, and reset (section 7).

- `--keep-venv` preserves an existing `dist/tdd-ladder/.venv` across rebuilds. Everything else in `dist/tdd-ladder` is regenerated, including the git history, so rebuild only between runs.
- The participant `.venv` is made with `/opt/homebrew/bin/python3.13` when that exists, otherwise `python3`. Pass `--setup-python /path/to/python3` to the build to bake in another Python 3.11+.
- The master passphrase stays in `~/.config/workshop/master-passphrase`, outside every repo. The build reads it; the repo stores only a check value. You type it at the prompt for `./gate skip --master` and `./gate allow-model`.

## 2. Facilitator: give the repo to group leaders

Each leader gets a copy of the built participant repo as a git bundle: one file that clones into a complete repo. Never send them, or point participants at, the builder repository; it holds the sources and the answers.

1. Start from a clean repo. A bundle carries everything in the repo, including rehearsal commits and the `attempt-*` branches that hold your rehearsal solutions, so rebuild (section 1) or reset (section 7, including the branch deletion) first.
2. Check it and make the bundle:

   ```zsh
   cd dist/tdd-ladder
   git status --short && git log --oneline && git branch   # expect no changes, one commit "Workshop start", only main
   git bundle create ~/Desktop/tdd-ladder.bundle --all      # under 100 KB
   ```

3. Send each leader the bundle and this walkthrough file. Ask them to work through section 3 before the leaders' briefing, so problems surface early. A private git remote works too: push `main` and the `start` tag, and send the clone URL instead.
4. Decide who types the master passphrase. Power-ups and skips ask for it in the group's own gate terminal; a leader's laptop never needs the passphrase file. By default you hold it and type it when a leader calls you over. If a leader will run a group without you in the room, such as a trial, tell them the passphrase. It opens every repo built from the same passphrase file, so if that matters, build their copy from a different passphrase file into another directory (`--out`).

## 3. Group leaders: set up your laptop

Do this a few days before the session, with a network connection. You need a Mac with:

- The Xcode Command Line Tools: `xcode-select --install` (they provide `git`).
- Python 3.11 or newer, for example `brew install python@3.13`.
- Claude Code 2.1.295 or newer (`claude --version`), signed in to a Claude account that can use Haiku, and Sonnet for power-ups.
- A git identity, because the exercise commits: `git config --global user.name "Your Name"` and `git config --global user.email you@example.org`.

Do not install anything else. If preflight asks for something, check with the facilitator first.

This exercise needs Claude Code: its lessons depend on Claude Code hooks (the personas, the model lock and the guard), so groups on another agent should do Explorer instead.

1. Clone the bundle the facilitator sent (adjust the path to wherever you saved it):

   ```zsh
   git clone ~/Downloads/tdd-ladder.bundle tdd-ladder && cd tdd-ladder
   ```

2. `./preflight --setup` creates `.venv` and installs the pinned numpy, matplotlib and pytest (a minute or so; the only step that needs the network apart from Claude Code). If it says your Python is too old, it prints the command to run with a newer one.
3. `./preflight` must end with "Preflight passed". The first run also sets the workshop up at level 0.
4. Run `claude` in the repo and accept the workspace trust dialog; the guard rails do not load until you do. Then, in Claude Code (about a minute):
   1. `/hooks`: four events must be listed (SessionStart, UserPromptSubmit, PreToolUse, PreModelSwitch). If the list is empty, the trust dialog was not accepted: `/exit` and run `claude` again.
   2. `/status`: the model line must say Haiku.
   3. `/model` and pick Sonnet (or Default): it must be refused with "Today's exercise uses haiku. Ask a facilitator for a power-up." Picking Haiku again is allowed and does nothing.
   4. `/exit`.
5. Rehearse: play Levels 0 and 1 yourself following section 5, then reset (section 7) so the group starts at level 0.

## 4. Running the session

### Two windows

| Window | Command | Who types |
|---|---|---|
| Claude (large) | `claude`, in the repo | the Driver |
| Gate (small) | a fresh Terminal window in the repo, then `./gate …` and `./tdd …` | the humans |

Open the gate terminal from Terminal itself, not from inside Claude Code: the gate refuses to run from Claude's shell and says so. If the room has a screen, put both windows on it; everyone needs to see the scorecard.

The session starts in plan mode on Haiku. `Shift+Tab` leaves plan mode once the group has agreed a plan. `/model` to anything but Haiku is refused until a power-up is granted. Choosing Haiku in `/model` is allowed, because Haiku is the allowed model; that is not a bypass.

**Which model is it, really?** Trust `/status` (or a status line), not what Claude says about itself. Haiku models sometimes misreport their own name, so "I'm Claude Sonnet" in answer to "what model are you?" is not evidence of an override. Claude Code applies the project's `model` setting at launch unless `--model`, `ANTHROPIC_MODEL` or an earlier `/model` overrides it; a launch-time `--model` or environment override is not blocked, and the start-up check only warns when Claude Code reports the model. If in doubt, quit and re-open with plain `claude`, then check `/status`. The participant `CLAUDE.md` tells Claude to say it cannot be sure and to point at `/status`.

### Opening (60 seconds, read aloud)

> "We're going to build the same small feature several times, starting badly *on purpose*, and an objective scorecard will tell us how good our tests really are each time. For the first two levels Claude is set to be literal and not to ask questions. That's deliberate: watch what it decides for us. After that we take control: we make the decisions, we compute the expected answers, and the tooling won't let anyone, Claude included, edit tests while we're making them pass. Roles: [assign]. The keyboard rotates at each gate."

You are the Coach: you ask questions and fix tooling, and you do not drive. Allocate the roles (described in the repo's `README.md`) by group size, as below. The Driver rotates at each gate through everyone except you, so every other member types; you drive only with two people or to fix a technical problem.

| Group size | Roles |
|---|---|
| 2 | You: Coach and Navigator. The other person: Driver, Sceptic and Scribe. |
| 3 | Driver (rotating), Sceptic. You: Coach, Navigator and Scribe. |
| 4 | Driver (rotating), Navigator, Sceptic. You: Coach and Scribe. |
| 5 | Driver (rotating), Navigator, Sceptic, Scribe. You: Coach. |

- **The hook block in GREEN** ("tests are frozen") often sparks the best discussion of the session. Let it run for a minute. Read every refusal aloud: it is the lesson, not a bug.
- **The TDD sceptic** ("this is slow, I'd just write it"): agree it is slower for this tiny function, and point at the Level 0 scorecard. The discipline is insurance; the scorecard prices it.
- **2 people:** you also run the `./tdd` phase commands; your partner, as Sceptic, computes the expected values.
- **5 people:** at Level 3, two people hand-compute each expected value independently, and the cycle goes on only if they agree.
- **A quiet member** can own the gate terminal: every `./tdd` transition runs through them.

### Time checkpoints

| From Go | Expected | If behind |
|---|---|---|
| 5 min | Level 0 scored | Don't polish; score and move on |
| 11 min | Level 1 scored | Same |
| 21 min | `SPEC.md` done; client spec read | Cap the interview at 8 minutes |
| 36 min | 5 or more cycles | Fine to stop at 5 good cycles |
| 44 min | Level 4 attempted | Even one property test plus a re-score shows the jump |

### Commands

Useful at any time in the gate terminal: `./gate status`, `./gate brief`, `./tdd status`, `./tdd ladder`, `./gate hint` (tiers unlock at 0, 5 and 10 minutes on the level). The repo's `README.md` lists the commands for Level 0 onwards; the Level 3 brief adds the cycle commands (`./tdd red`, `green`, `refactor`, `done`, `abort`).

Need the master passphrase, which the facilitator holds, so call them over: `./gate allow-model sonnet` (a power-up to Sonnet) and `./gate skip --master` (open the next level for a stuck group, with a reason). Both are logged.

## 5. Level by level

### Level 0: Just build it (5 min, persona literal)

1. Driver pastes the client's request from `README.md` into Claude exactly as written. Accept what it gives you. If it asks a question, answer "whatever you think best".
2. In Claude: `make plot`. Look at `results/hz_binned.png`; a copy is kept as `results/hz_binned_L0.png`.
3. Gate terminal: `./tdd score` (about 2 s). Then `./gate unlock`. The unlock saves the Level 0 work on branch `attempt-L1-<timestamp>` and restores the stub and an empty `tests/` automatically, and says so.

Observe: does Haiku ask any questions, or just decide? Does it write tests? Typical score with the sample naive code: acceptance 4/12, 1/16 killed, 2 false alarms. Anything in the band acceptance 4–9 and kills ≤ 6 is the expected experience.

Ask: "What did the score say? Which decisions did Claude make for us?"

Gate answer: the acceptance number printed by `./tdd score`. Reflection (logged, not graded): two silent decisions.

### Level 1: "Use TDD, please" (6 min, persona literal)

1. Nothing to run: the L0 unlock already started the attempt from the stub. (`./tdd new-attempt` is still there to restart the level; the gate then wants a fresh `./tdd score`.)
2. Driver: same request plus "Use test-driven development."
3. Watch for: tests and code in one turn; first `pytest` run all green; expected numbers from Claude's head. `.tdd/runs.jsonl` records every pytest run, so `./tdd status` after a score shows what happened.
4. `make plot` keeps `results/hz_binned_L1.png` next to the L0 plot, for comparison. `./tdd score`, then `./gate unlock`.

The unlock commits the Level 1 work as "Level 2 start", so the Level 2 refusal can quote an exact `git checkout <hash>` restore.

Ask: "Scribe, did any test fail before code existed? Where did that expected value come from?"

Gate: no graded question. Reflections: red seen (y/n); oracle source (a–d). Expected band: acceptance 6–10, kills ≤ 8.

### Level 2: Decide before you test (10 min, persona coach)

1. Driver uses the interview prompt from `BRIEF.md`. Claude should ask one question at a time and never suggest answers. Cap the interview at 8 minutes.
2. Claude writes `SPEC.md` with numbered decisions (`1.`, `2.`, … at least 6). No code, no tests: the guard allows only `SPEC.md` and `LOG.md`, and the gate checks that `src/` and `tests/` are byte-identical to when the level began.
3. `./gate unlock`. If `src/` or `tests/` changed, the refusal names the files and the `git checkout` or delete needed. The unlock writes `CLIENT_SPEC.md`, resets `src/hzbin/binning.py` and `tests/` to the stub (your work is on `attempt-L3-<timestamp>`), and only then asks the reflection "how many of the client's 10 decisions did your SPEC address?".

Observe: whether the group argues about what the error bar means and where the point sits (S4, S5). Most groups anticipate 5–8 of 10. Watch for one person deciding everything, and for Claude steering the answers.

Ask: "Do we all agree on what the error bar *means*? What does the plot reader assume?"

### Level 3: Red, green, refactor, for real (15 min, persona coach + phases)

Each cycle, in the gate terminal:

```zsh
./tdd red "single bin with equal sigma gives the arithmetic mean"   # opens the cycle; src/ frozen
# Claude writes ONE test; the Sceptic supplies the number; Claude commits: git add tests && git commit -m "..."
./tdd green        # refuses unless the test is committed and fails with AssertionError/NotImplementedError
# Claude writes the minimum code; commits
./tdd refactor     # optional
./tdd done         # closes the cycle; needs all green and a clean src/ and tests/
```

Things to try deliberately so the group sees the machinery:

- In GREEN, ask Claude to "fix the test". The guard denies with "Tests are frozen in GREEN…". Let the discussion run.
- Ask Claude to write a test that imports a name that does not exist. `./tdd green` refuses: "red for the wrong reason: ImportError".
- Have someone edit a test file by hand during GREEN. `./tdd refactor` or `./tdd done` refuses: "tests/ changed since GREEN began".

Suggested order of behaviours is in `BRIEF.md`. The gate needs 5 valid cycles with none left open (otherwise it says to run `./tdd done` or `./tdd abort`), then `./tdd score` with 0 false alarms and ≥ 9/16 killed. The sample Rung-4 suite scores 10/12 acceptance, 11/16 killed, survivors S2, S7, S9, S10.

Ask: "Sceptic, did *you* compute that value? Navigator, is this one behaviour?"

Gate answer: any spec ID listed under "surviving mutants violate" in the last score, or `none` if 16/16. Loose forms pass: "s4", "S4 and S5" (any one right id counts) and "none - we killed all 16" (the word none or nil, or just "no" or "0", with no S-prefixed id; it only passes at 16/16).

### Level 4: Think like a physicist (8 min, persona coach)

The brief has the property-test menu. Three property tests (uniform-σ limit, affine equivariance, seeded coverage) plus the validation tests usually take the suite to 14–16/16. The gate needs ≥ 14/16, 0 false alarms, suite under 10 s. Watch for arbitrary Monte Carlo tolerances.

Ask: "What's the binomial σ for your N? Is your bound 3σ?"

Gate answer: √(0.683 × 0.317 / 2500) ≈ 0.0093. Accepted: 0.0090 to 0.0096, and any number in the typed answer counts, so "0.93%" and "sqrt(0.683*0.317/2500) = 0.0093" both pass.

### Level 5: Stretch, test the tests (5 min, persona collaborator)

Claude (via a subagent) writes mutants of the group's own `binning.py`; the group runs its suite against each. The gate needs a `## Mutation report` section in `LOG.md`. Reflection: one test you'd delete.

## 6. When something goes wrong

| Symptom | Do |
|---|---|
| Group stuck | `./gate hint` (3 tiers; at Levels 0, 3 and 4 a fourth at 13 minutes gives the answer), then a question, then `./gate allow-model sonnet`, then `./gate skip --master` as the last resort. The last two need the master passphrase. All are logged in `LOG.md` and `.workshop/state.json`. |
| `./gate` or `./tdd` says it is "for humans, in the gate terminal" | It was run from Claude's shell, or from a window opened from Claude Code. Use a fresh Terminal window. |
| Hooks not firing (Claude edits tests in GREEN) | In Claude run `/hooks`; if empty, exit, re-open `claude` in the repo and accept trust. `./tdd` transitions still catch Bash edits via git diff. |
| `./tdd green` refuses | Read the reason aloud. It is usually "tests not committed" or "red for the wrong reason". That is the lesson. |
| `./tdd red` refuses because the suite is red or skipped | Claude cannot edit with no cycle open. The message gives the way out: restore the last good commit of `src tests` (or `git rm` the bad test file) in the gate terminal and commit. |
| A group forgot a step | Every gate refusal names the step: score missing, cycle open, SPEC.md missing or short, files changed. The Level 1 and Level 3 restarts are automatic at the unlock. |
| `./tdd score` slow or fails | It runs 18 pytest processes in parallel, normally 1–2 s. A group test that hangs is killed after 120 s. Large statistical tests are the usual cause: reduce N, and recompute the bound. |
| Someone launched `claude --model opus` | The SessionStart hook warns in Claude's context only when Claude Code reports the model. Ask the group to restart with plain `claude`, then check `/status`. |
| Claude names the wrong model when asked | Not an override. Check `/status`. See "Which model is it, really?" in section 4. |

## 7. Reset between runs

In the repo (`dist/tdd-ladder` for the facilitator, your clone for a leader):

```zsh
./gate reset                       # confirms, wipes .workshop/ and .tdd/, removes BRIEF.md and CLIENT_SPEC.md
git reset --hard start && git clean -fdx -e .venv -e .workshop   # restores the stub and empty tests; removes ignored results; keeps .venv
git branch | grep attempt- | xargs -n1 git branch -D   # optional: drop the attempt branches
```

The facilitator can instead rebuild (`tools/build.py … --keep-venv`), which also gives fresh packs and secrets; leaders then need a new bundle.

## 8. What to record

`.workshop/state.json` holds per-level start and unlock times, hints used, failed attempts, skips, model power-ups and every score. `./tdd ladder` prints the score curve for the show-and-tell. `LOG.md` has the reflections and the Scribe's notes. Copy both out before `./gate reset`, and leaders send their copies to the facilitator.

For the show-and-tell, ask each group:

- "Show your ladder: mutants killed at Levels 0, 1, 3 and 4."
- "Which client decision did nobody anticipate?"
- "The moment the hook stopped Claude editing a test: what did you decide?"
- "One TDD habit you'll actually use next week."
