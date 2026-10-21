# Facilitator Walkthrough: Explorer

Private. Contains gate answers and spoilers. Never copy into `dist/`, and keep it away from participants.

**Group leaders: [`LEADER-QUICKSTART.md`](LEADER-QUICKSTART.md) is the short version (one to two pages). This walkthrough is the full guide.**

This is the operating guide to the exercise. It has two readers:

- **The facilitator** (the organiser) builds the participant repo, rehearses it, sends it to the group leaders and holds the master passphrase. Read all of it.
- **Group leaders** set up their own laptop from the bundle the facilitator sends, and coach one group. Start at [section 3](#3-group-leaders-set-up-your-laptop); sections 1 and 2 are the facilitator's.

The lecture, roles by group size, the run-sheet and the trial are in `docs/00-facilitator-guide.md` in the builder repository. The design this exercise was built from is `docs/05-data-explorer.md`; where the two differ, this walkthrough and `docs/DECISIONS.md` win.

Every timing and size below was **measured on an M1 Max (Python 3.13.2, numpy 2.3.2, plotly 7.1.0); calibrate on your own laptop** before you quote a number to a group. Unlike the other exercises, the clock is not the main risk here: there are no planted bugs and no hidden assets, so what happens at each level depends on what Sonnet does on the day. The checks only prove that each step happened.

Explorer runs on **Sonnet**, not Haiku. The lesson is the workflow (plan, build in checked steps, test, review), not supervising a weak model, and building Python plus a JavaScript page in 18 minutes is a real risk on Haiku. The lecture's "weak model" slide does not apply to this group: tell them the agent is a normal, helpful collaborator today.

## 1. Facilitator: build and rehearse

Once per machine, do steps 2 and 3 of "Run the workshop" in the repository [`README.md`](../../README.md#run-the-workshop): the requirements and the master passphrase. Then:

```zsh
cd <this repository>
python3 tools/build.py explorer
cd dist/explorer
./preflight              # first run sets up .venv (needs the network, about a minute); must end with "Preflight passed"; also checks plotly and its bundled plotly.js
```

`./preflight` installs numpy 2.3.2, plotly 7.1.0, pytest 9.1.1 and pytest-cov 7.1.0. Nothing needs a compiler, so unlike the Speed Run there is no `clang` requirement.

Then do the Claude Code checks in section 3, step 3, play the whole exercise through once on Sonnet using section 5, and reset (section 7). Open `out/explorer.html` in a browser at least once in the rehearsal: the Level 1 question is meant to send the group there, and you want to have seen the page.

- The build reads the passphrase from `~/.config/workshop/master-passphrase` (`--master-passphrase-file` overrides it) and keeps an existing `dist/explorer/.venv` (`--fresh-venv` drops it). Everything else in `dist/explorer` is regenerated, including the git history, so rebuild only between runs.
- The participant `.venv` is made with `/opt/homebrew/bin/python3.13` when that exists, otherwise `python3`; the build machine used Python 3.13.2. Pass `--setup-python /path/to/python3` to the build to bake in another Python 3.11+.
- The master passphrase stays outside every repo; the repo stores only a check value. You type it at the prompt for `./gate skip --master`.
- `exercises/explorer/selftest/run.py` plays the whole exercise with a reference solution (138 checks, about a minute). It proves the gates, not the timing; the rehearsal is where you learn the timing.

### Optional: a calibration run

The self-test cannot say how long Sonnet takes to build the tool with a group directing it. If you have an hour, play it yourself with a stopwatch, following the playbook prompts in the briefs: plan mode, two build steps, commit each step. Write down the time at each unlock, and Level 1 above all: it is the long one (18 minutes) and the one most likely to run over. If Level 1 takes more than 20 minutes, tell leaders to give hint 3's advice at Level 0 early and to cut scope harder in the plan (the steps are already capped at two), and consider moving some of Level 0 into the README so that it fits 6 minutes. Record the result in `PROGRESS.md`.

## 2. Facilitator: give the repo to group leaders

Each leader gets a copy of the built participant repo as a git bundle: one file that clones into a complete repo. Never send them, or point participants at, the builder repository; it holds the sources and the answers.

1. Start from a freshly built or reset repo: a bundle carries everything in the repo.
2. From this repository's top folder, run `python3 tools/bundle.py explorer`. It checks that `dist/explorer` is clean, has one commit, only `main`, `start` at HEAD and level 0, then writes `explorer.bundle` in the current folder (use `--out PATH` to put it elsewhere) and verifies it.
3. Send each leader the bundle and this walkthrough file. Ask them to work through section 3 before the leaders' briefing, so problems surface early. A private git remote works too: push `main` and the `start` tag, and send the clone URL instead.
4. Decide who types the master passphrase. Skips ask for it in the group's own gate terminal; a leader's laptop never needs the passphrase file. By default you hold it and type it when a leader calls you over. If a leader will run a group without you in the room, such as a trial, tell them the passphrase. It opens every repo built from the same passphrase file, so if that matters, build their copy from a different passphrase file into another directory (`--out`).

## 3. Group leaders: set up your laptop

Do this a few days before the session, with a network connection. You need a Mac with:

- The Xcode Command Line Tools (`xcode-select --install`): they provide `git` and `make`. No compiler is used.
- Python 3.11 or newer, for example `brew install python@3.13`.
- Claude Code 2.1.295 or newer (`claude --version`), signed in to a Claude account that can use Sonnet. The session starts on Sonnet and stays on it.
- A git identity, because the exercise commits: `git config --global user.name "Your Name"` and `git config --global user.email you@example.org`.
- A web browser. The group looks at the page it builds.

Do not install anything else. If preflight asks for something, check with the facilitator first.

1. Clone the bundle the facilitator sent (run this in the folder where you saved it, or give its full path):

   ```zsh
   git clone explorer.bundle explorer && cd explorer
   ```

2. `./preflight` creates `.venv` and installs the pinned numpy, plotly, pytest and pytest-cov, then checks the machine. The first run needs the network and takes about a minute (the only step that needs the network apart from Claude Code). If it says your Python is too old, it prints the command to run with a newer one. It must end with "Preflight passed"; the first run also sets the workshop up at level 0.
3. Run `claude` in the repo and accept the workspace trust dialog; the guard rails do not load until you do. Preflight has already checked the skill and agent files. In Claude Code (about a minute):
   1. `/hooks`: four events must be listed (SessionStart, UserPromptSubmit, PreToolUse, PreModelSwitch). If the list is empty, the trust dialog was not accepted: `/exit` and run `claude` again.
   2. `/model` and pick another model: it must be refused. The session stays on Sonnet.
   3. `/exit`.
4. Rehearse: play Level 0 yourself following section 5, and reset (section 7) so the group's log starts empty. Level 0 needs nothing built, so it is a quick way to see the gate, the guard and the plan-mode start.

### Groups on other agents

Explorer can be done on another agent harness (Codex, Cursor, Copilot, Antigravity, OpenCode). The group reads `OTHER-AGENTS.md` in the repo, which covers the participant side. The rules are in `AGENTS.md`, which these harnesses read; `CLAUDE.md` imports it for Claude Code.

Without Claude Code the group loses:

- the guard and the other hooks: the rules are written in `AGENTS.md` instead and rest on trust, and the gates still check the work;
- the per-prompt persona, so the group asks the agent to run `./gate brief` at the start and after each unlock;
- the model lock, and the plan-mode start (they use the agent's own plan or ask mode);
- the forked review: they open a fresh session in the same folder instead.

The timings are calibrated on Claude Code with Sonnet only, and no other harness has been rehearsed yet. Cursor and Copilot may run the Claude Code hooks from `.claude/settings.json`; if every command is refused, `OTHER-AGENTS.md` says how to turn that off. Claude Code stays the recommended setup.

## 4. Running the session

### Two windows and a browser

| Window | Command | Who types |
|---|---|---|
| The agent (large) | `claude`, in the repo | the Driver |
| Gate (small) | a fresh Terminal window in the repo, then `./gate …`, `make open`, `make list`, `make test` | the humans |
| Browser | `make open` shows `out/explorer.html` | everyone looks |

Open the gate terminal from Terminal itself, not from inside Claude Code: the gate refuses to run from the agent's shell and says so. The agent cannot see the browser; that is the point of Level 1.

The session starts in plan mode on Sonnet. `Shift+Tab` (in Claude Code) leaves plan mode once the group has agreed a plan. `/model` to anything but Sonnet is refused.

**Which model is it, really?** Trust `/status`, not what the agent says about itself.

### Choosing the dataset

Before the session, choose the group's dataset: pulsars (`data/pulsars.csv`, for the astro and cosmology end of the room) or dimuons (`data/dimuons.csv`, for the particle end). At Level 0, before the plan is committed, run `./gate dataset pulsars` or `./gate dataset dimuons` in the gate terminal. It sets the `Dataset:` line of `PLAN.md` and leaves it uncommitted (the agent commits `PLAN.md`, which is what the gate wants). It refuses once the plan is committed. A reset puts the line back to pulsars.

That line is the only place the dataset is named. The Makefile reads it, so `make explore`, `make list` and the Level 1 and Level 3 checks all follow it, and the group never types a path. The value must be exactly one of the two relative paths: the Level 0 gate refuses anything else. Both datasets ship, but once `PLAN.md` is committed the group works only with its own: no gate and no brief points at the other one. A group's own CSV works with `make explore DATA=path/to/file.csv`. Dimuons has no missing values or text columns; the Level 2 brief suggests a test with a small made-up CSV for README rules a dataset never triggers.

### Opening (60 seconds, read aloud)

> "Today we build a real tool, a 3D explorer for our data, and we build it the way you'd want a careful student to: plan, build in two checked steps, test, review, and commit as we go. The agent is a normal, helpful collaborator today; the gates just make sure we do each step. The gate terminal is ours: the agent can't type there, and that's where we run the tests ourselves. Roles: [assign]. The keyboard rotates at each gate. All code goes through the agent; we read, look, decide. At the end, `PLAYBOOK.md` is yours to take home, and the four skills in `.claude/skills/` with it."

You are the Coach: you ask questions and fix tooling, and you do not drive. Allocate the roles (described in the repo's `README.md`) by group size, as below. The Driver rotates at each gate through everyone except you, so every other member types; you drive only with two people or to fix a technical problem.

| Group size | Roles |
|---|---|
| 2 | You: Coach and Navigator. The other person: Driver, Sceptic and Scribe. |
| 3 | Driver (rotating), Sceptic. You: Coach, Navigator and Scribe. |
| 4 | Driver (rotating), Navigator, Sceptic. You: Coach and Scribe. |
| 5 | Driver (rotating), Navigator, Browser Sceptic (looks at every result), Evidence Sceptic (wants every command and output). You: Coach and Scribe. |

- **The expert who wants to write it by hand:** "You'd be faster today. The point is the habit for when the code is ten times bigger. Can you get the agent to do it the way you would?"
- **Plotting rabbit holes** (styling, extra controls): the Navigator owns scope. "Is it in the plan?" Suggestions go in the log for later.
- **Correction spirals:** after two failed corrections, start a fresh session (`/clear` in Claude Code) with a better prompt.

### Time checkpoints

45 minutes: 8 for Level 0, 18 for Level 1, 8 each for Levels 2 and 3, and 3 spare. There is no stretch level.

| From Go | Expected | If behind |
|---|---|---|
| 8 min | `PLAN.md` committed, Level 0 unlocked | Keep the plan short; give hint 3's advice (acceptance criteria, then commit) |
| 26 min | Level 1 gate passed | Narrow to what `./gate check` names; skip styling |
| 34 min | Tests running | Five simple tests are enough |
| 42 min | Review triaged | Three findings is enough; fix one |

### Commands

The unlock screen is: `PASS:` line, any `Note:` lines (a relaxed check that did not hold, with a reason to do it next time), the graded question if any, a headed "Level N unlocked" block with new files and a `Next:` line, then "Talk it over" (nothing to type, nothing saved). Useful at any time: `./gate status` (level, time on level, hints, dataset, whether the page is built, commits since the last gate), `./gate brief`, `./gate check`, `./gate hint` (three tiers: at 0, 3 and 6 minutes on the 8-minute levels, and 0, 5 and 10 on Level 1, where a fourth at 13 minutes gives the answer for the group's dataset), and `make list`, `make explore`, `make open`, `make test`, `make coverage`. The repo's `README.md` lists every command.

Need the master passphrase, which the facilitator holds, so call them over: `./gate skip --master` (open the next level for a stuck group, with a reason) and `./gate install-solution --master` (install and commit the reference solution). Both are logged. There are no model power-ups: Sonnet is already the model.

## 5. Level by level

Every gate check prints one sentence on failure naming the first thing that is wrong and how to fix it, and the success line on a pass. Tell the Driver to run `./gate check` early and often and paste the sentence to the agent. Every gate also requires new commits since the previous unlock and a clean tree for the paths it checks, so every brief ends "commit, then unlock". Humans do not touch the code: The agent makes the commits when asked.

### Level 0: Plan (8 min, collaborator)

1. The group reads the README (short now; the fixed tool interface is in `INTERFACE.md`), then in plan mode gives the agent one prompt that combines the playbook's *Understand* and *Plan* prompts: summarise the data (including which columns have missing values and how many), then, using the plan-code skill, propose a plan. They argue with it, then have the agent save it as `PLAN.md` and commit it.
2. `make list` cannot work yet: the tool does not exist until Level 1, so it fails with "No module named explorer.__main__; 'explorer' is a package and cannot be directly executed". That is expected. The Level 0 prompt (which also names `INTERFACE.md`) asks the agent for the missing-value counts up front (hint 1 is the fallback if it doesn't say); the commands table says `make list` works once the tool has `--list`. (Pulsars: `P1` misses 1,524 values, `AGE`, `BSURF` and `EDOT` 1,605 each, and 74 pulsars have no distance, so their `XX`, `YY`, `ZZ` are blank. Dimuons has no missing values, but 60,000 rows to sample down.)
3. Gate (`crypto`, no graded question). The check requires `PLAN.md` to be complete: `Dataset:` exactly one of the two shipped paths; each section filled with something other than the template; and exactly two steps (top-level list items; sub-bullets do not count). A longer plan is refused: "PLAN.md lists 8 steps; merge them into two, each ending in something you can run and look at: the command line and data.json, then the page". Two steps keeps Level 1 to two stop-run-look-commit cycles; the README, the persona and the hint all suggest the same split (the command line, `--list` and `data.json`; then the page with the decisions and the initial view); the solo run's three-step plan split that way, with a small third step the cap now folds into the second. Steps written as `###` headings or an indented list count too; prose with no list is refused with "write the two steps as a numbered list". Also at least one commit since `start` and `PLAN.md` clean. Two checks only earn a `Note:` and the gate still passes: fewer than three acceptance criteria (the section must still be non-empty), and a blank or missing decision line (values at or below zero on a log axis; missing values in a selected column; the initial selection when the page opens; sampling above `--max-points`). The unlock screen then shows the talk prompt (nothing to type, nothing logged): "One thing in the agent's plan you changed, and why?" The fixed tool interface lives in `INTERFACE.md` (at the repo root in a leader's clone) (moved out of the README so the Level 0 brief is short); the Level 0 prompt tells the agent to read it, and it is frozen at every level.

Observe: which decisions did the agent make silently (dropping rows, clipping logs, which columns the page opens on)? Does the group notice, or accept the plan unread? Is the plan bigger than the job (class hierarchies, a config system, a build step for the JavaScript)?

Ask: "Which decisions did the agent make for us? Do we agree?" The Sceptic owns the acceptance criteria and the Navigator cuts the scope.

Try deliberately:

- Ask the agent to "just write the code". The guard refuses: "Level 0 is planning only: the agent may edit PLAN.md and LOG.md, and explorer/ opens at Level 1 and tests/ at Level 2." Read it aloud: the plan is where the decisions are cheap to change.
- Unlock with the template `PLAN.md` (still refused) or without committing (still refused): "no commit since start: ask the agent to commit PLAN.md (this level needs at least 1)". Change the `Dataset:` line to anything else and the gate says it must be exactly `data/pulsars.csv` or `data/dimuons.csv`.

### Level 1: Build the prototype (18 min, collaborator)

1. The unlock opens `explorer/` for editing (and freezes `tests/`). The group leaves plan mode and has the agent implement step 1 of the plan only, following the coding guidelines in the style-code skill, run it, show the command and output, and say what the group can run to check it; then runs that in the gate terminal (once the page exists, `make explore` then `make open`), has the agent commit, and goes to the next step. The plan has two steps, so this is two cycles; the two-commit minimum matches. The generated page embeds plotly.js (about 5 MB), so `out/explorer.html` is a few MB. `make explore` should take well under 5 s.
2. Gate (`crypto`, one graded question). The check runs the tool four times on the `PLAN.md` dataset: with the defaults; with `--max-points 500` (must write exactly 500 rows and still report the same `n_read`); with `--list` (must name every column of the column file); and on a file that does not exist (non-zero exit and no `Traceback`). It reads `data.json` as strict JSON with the structure in the README, and checks that `explorer.html` has plotly.js inline, no `<script src="http...">`, the five `<select>`s and four checkboxes with the right ids and an option for every numeric column, and the strings `scattergl` and `scatter3d` outside the plotly.js code. It also needs at least **2 commits** since the Level 0 unlock and `explorer/` and `PLAN.md` clean.
3. The question needs a human who has looked at the page, and `./gate unlock` asks only the one for the group's dataset (it reads the `Dataset:` line; if it cannot, it asks a neutral question and the leader gives the dataset's question aloud). A wrong answer prints "Not quite" and a dataset-specific hint, and the group runs `./gate unlock` again. **Pulsars:** plot `XX`, `YY`, `ZZ` and rotate it; the known pulsars crowd around one point. What is there? Answer **`sun`**. **Dimuons:** plot `M` against `pt1` with log axes; which particle makes the sharp band near 3.1 GeV? Answer **`jpsi`**. Matching ignores case, spaces and punctuation, and maps ψ to `psi`. Accepted for both datasets: any answer that contains `sun`, `solar`, `earth`, `meson`, `psi` or `charmonium` (so "It's the Sun", "Sun (solar system)", "Earth / the Sun", "the solar neighbourhood", "J/ψ", "the J/psi meson" and "charmonium" all pass), plus the exact answers `sol` and `us`. Wrong answers such as "galactic centre", "Sgr A*", "bulge", "black hole" and "Sagittarius" are still refused. Known consequence of the generous `contains` rule: "upsilon", "pion meson", a bare "meson", or "not the Sun" also pass.
4. The talk prompt (nothing to type): "What did you see in the browser that the check couldn't?" The brief also has the group play with the page for a minute (rotate, zoom, hover, switch columns, palettes and log axes) and agree one feature. The Scribe writes it in `LOG.md`; it is not built now. Typical ones are a slider, a trace-per-label, saved views and a second colour column; a group with time after Level 3 may build it (the Finished early section of the Level 3 brief offers it, or two others).

Observe:

- The agent tries to build everything in one go. The Driver stops it (`Esc` in Claude Code) and asks for one step.
- "This should work now" with no command and output run. The Sceptic asks for them.
- A plotly detail recalled wrongly (the hover template, the colour-bar title, the 3D trace). "Check the installed version's documentation" is worth a minute.
- `data.json` contains `NaN` and the check says: "data.json is not valid JSON (NaN is not JSON; write it with allow_nan=False)". That is two minutes of real debugging, on a mistake Python makes easy.
- Hover showing another row's values after sampling, or a colour bar with no unit. Only the humans looking at the browser catch these.
- Does anyone open the browser before the group's first commit? Does anyone commit?

Ask: "What did that step change? Show me in the browser. Is it committed?"

Try deliberately:

- Ask the agent to write tests now. The guard refuses ("tests/ is frozen until Level 2, so build first and test next").
- Have the agent write `NaN` into `data.json` and run `./gate check`: the sentence above. This is the bug that a human would not see and the check does.
- Commit once, then `./gate unlock`: "1 commit since the last gate; this level needs at least 2: ask the agent to commit each step that works (two commits or more)". Leave `explorer/` changes uncommitted: "explorer/ has uncommitted changes: ask the agent to commit, then unlock". (The commit count is checked first.)
- Answer the question with the wrong word (`moon`): refused with a hint for the dataset; the group can try again.

### Level 2: Test (8 min, collaborator)

1. The unlock opens `tests/`, `explorer/` and `TESTS.md` and freezes `PLAN.md`. The Scribe writes three things that must not break under "Our list" before anyone asks the agent anything (two minutes, no agent). Then one prompt asks the agent, using the test-code skill, for a plan of five to eight tests (one line each, the coverage, what it will not cover), written straight into `TESTS.md` under "The agent's plan", without writing any tests yet. The agent should not run unasked experiments (deliberate bugs, coverage write-ups, extra tests). The group compares the two lists and agrees what to write. Then the agent writes and runs the tests, commits, and the group runs `make test` and, if there's time, `make coverage` in the gate terminal.
2. Gate (`crypto`). `make test` finds at least five tests and all pass; at least one test module imports `explorer`; at least 1 commit since the Level 1 unlock; `explorer/`, `tests/` and `TESTS.md` clean. Notes only (the gate still passes): fewer than three items under "Our list", or "The agent's plan" missing or empty. Talk prompt: "What did the agent's test plan cover that your list didn't, or the reverse?"

Observe:

- The agent writes tests immediately unless held to the plan; the brief tells it to wait.
- The easy pure functions tested and the page left untested. Coverage shows it. The discussion to have: pytest can test the data preparation, `data.json` and the page's structure, but not what the page does in the browser, which needs a human.
- A failing test "fixed" by changing the test. The one thing never to accept: a failing test is a finding. Fix the code, or decide the test was wrong and say why.

Ask: "What won't these tests catch? Does that matter for us?"

Try deliberately:

- Unlock with an empty `TESTS.md`: the gate passes with `Note: TESTS.md has 0 items under "Our list"; next time write 3 things that must not break before asking: it shows what the agent's plan misses.` (the notes show on `./gate check` too). With four tests: "pytest collected 4 tests; this level needs at least 5, all passing: ask for the tests you agreed in TESTS.md". A failing test: "make test: 1 of 6 tests fail: fix the code, not the tests, then commit".
- *Does the alarm ring?* Ask the agent to break one behaviour on purpose (drop the unit from a title, write `NaN` into `data.json`), run the tests, see whether they fail, then revert. A test that never fails proves nothing. This is the hint 3 exercise and the best use of a spare minute.
- Ask the agent to weaken a test so that it passes. Watch whether the Sceptic notices.

### Level 3: Review (8 min, collaborator, last level)

1. The unlock opens `REVIEW.md` and freezes `PLAN.md` and `TESTS.md`. The group writes two things they think a reviewer will find (one minute), then asks the agent, in one prompt, to use the review-code skill to review the code since start against PLAN.md, rank the findings by severity and paste them into the table in `REVIEW.md`, most severe first, without fixing anything. The `review-code` skill (`.claude/skills/review-code/SKILL.md`) runs in a forked subagent (`context: fork`): a fresh context that has not seen the conversation. The shipped `reviewer` agent (`.claude/agents/reviewer.md`, on Sonnet, tools `Read`, `Grep`, `Glob`, `Bash`) is the fallback if the skill will not load. The persona has the agent ask the skill for three to five findings (the fork does not see the persona, so the number travels as the skill's arguments); the group compares them with their guesses and triages the top three to five themselves: **FIX**, **ACCEPT** (true, but not worth fixing in a prototype) or **REJECT** (wrong), with one line of reason; the rest can stay undecided. The agent fixes the top FIX item (more if there is time), with a test that fails before the fix, runs the tests and commits. The skill tells the reviewer to read the code, run the tool and the tests once each, and not to write scratch scripts or new tests.
2. Gate (`crypto`, the last level: it prints "Exercise complete"). The tests pass; the Level 1 run checks pass again on the `PLAN.md` dataset; at least 1 commit since the Level 2 unlock; `explorer/`, `tests/` and `REVIEW.md` clean. Notes only (the gate still passes): fewer than two guess bullets, or fewer than three table rows each with a decision in {FIX, ACCEPT, REJECT} and a non-empty reason (including no Findings section). Talk prompt: "What did the review find that the tests didn't?" The gate also prints the note that `PLAYBOOK.md` is theirs to take home, with the four skills in `.claude/skills/`.

Observe:

- What the reviewer finds in 20 minutes of agent-built code. Typically real issues: the planned log policy not implemented, hover misaligned after sampling, no error for a CSV with no numeric columns, duplicated loading code, a unit missing from a title. Also noise (style, speculative performance).
- Fixing every finding without discussion. Rejecting a finding with a good reason is as valuable as fixing one.
- A guess the reviewer also found, or missed: it calibrates how much to trust each.
- A fix that changes a test to pass.

Ask: "Is this worth fixing in a prototype? Why?"

Try deliberately:

- Unlock with an untriaged `REVIEW.md`: the gate passes with a note that fewer than three findings are triaged (and one about the guesses, if there are fewer than two). Triage everything as ACCEPT or REJECT with reasons: the gate passes, since no FIX is required (a clean review is a valid outcome); a cell such as "ACCEPT / REJECT" counts as undecided, so it earns the note.
- Groups with time left: the Level 3 brief's Finished early section offers, after the unlock, the Level 1 feature or two others, built the same way (one step, run it, look, commit): a day/night button that switches the page between light and dark colours, or mouse selection of points (box or lasso, in the 2D view) that shows how many were picked, with their labels if the dataset has them.

Honest limit: the check scripts print a fixed line, so each crypto gate's only secret is the human answer, and Level 1 accepts both datasets' answers, so a group could give the other dataset's answer. It is harmless here: the question exists to make a human look at the page, and the gates for Levels 0, 2 and 3 have no question at all. The checks are structural and cannot tell whether the page looks right. Two more limits worth knowing: the Level 1 question can be answered without the browser (the pulsar column file says where the Sun is, and a particle physicist knows the J/ψ), so it prompts a look rather than proving one; and a FIX in `REVIEW.md` is a label, not evidence that anything was fixed. Both are the leader's check: ask to see the page, and ask what changed. See `gatekit/README.md` section 11 in the builder repository.

## 6. When something goes wrong

| Symptom | Do |
|---|---|
| Group stuck | `./gate hint` (3 tiers; at Level 1 a fourth gives the answer), then a question. A stuck Level 1 is the likeliest. The last resort is `./gate skip --master` (needs the master passphrase), which opens the next level but installs no code. To let the group still test and review a real tool, run `./gate install-solution --master`: it installs and commits the reference solution. |
| Build too slow for the time | The same: `./gate skip --master`, then `./gate install-solution --master`. Say so to the group. |
| `./gate` says it is "for humans, in the gate terminal" | It was run from the agent's shell, or from a window opened from Claude Code. Use a fresh Terminal window. |
| `make list` fails at Level 0 ("'explorer' is a package and cannot be directly executed") | Expected: the tool does not exist until Level 1. Ask the agent for the missing counts instead. |
| `make open` does nothing | Open `out/explorer.html` from Finder, or `open out/explorer.html`. Check `out/` was written (`make explore` first). |
| Page blank in the browser, or a JavaScript error | plotly.js not embedded, or a script error: open the browser console (Safari: Develop, Show JavaScript Console) and paste the message to the agent. `./gate check` names the embedding case. |
| `data.json` check fails | Almost always `NaN` in a column of missing values. Paste the sentence to the agent: `allow_nan=False`, and write missing values as `null`. |
| The agent's Bash command is refused and the agent says it won't reword it | The guard reads quotes, heredocs and redirects, so reading `data/`, regexes, and the agent's usual heredoc commit message are allowed; it still refuses writes to frozen or secret paths, and a few odd spellings fall back to the strict rules. A command that both writes (`cp`, `mv`, `rm`, `tee`, `sed -i`, `python script.py`, a write call in `python -c`) and names `data/` is still refused, for example `cp data/pulsars.csv /tmp/x.csv`; a plain redirect such as `head -5 data/pulsars.csv > out/small.csv` is allowed. Every refusal tells the agent not to reword the command but to say so and use a `make` target or the tests. If the command really was harmless, note it for the facilitator and carry on another way. |
| `./gate unlock` says "no commit since start" or "N commits ... needs at least ..." | The agent has not committed. Ask it to commit, then `./gate status` shows commits since the last gate. |
| Hooks not loaded | `/hooks`; if empty, exit, re-open `claude` in the repo and accept trust. |
| A skill is not listed, or the agent says "unknown skill" | `/reload-skills`; if it is still missing, `/exit`, re-open `claude` in the repo and accept trust. For Level 3 the `reviewer` agent in `.claude/agents/` still works as a fallback, with the old prompt: "Use the reviewer agent to review the code since start against PLAN.md. Rank the findings by severity and paste them into the table in REVIEW.md, most severe first. Don't fix anything." |
| `reviewer` agent not found (only matters if the `review-code` skill is also unavailable) | `/agents`: it should be listed as a project agent. If not, the workspace trust dialog was not accepted: `/exit`, re-open `claude`, accept. If it is still missing, the group can ask the agent to review in a fresh subagent with the same prompt (the file is `.claude/agents/reviewer.md`). Record whether the guard fires on the subagent's own tool calls. |
| The agent names the wrong model | Not an override. Check `/status`. |
| Page opens very slowly | The dimuon file has 60,000 rows, sampled to 20,000 by default; `--max-points 5000` makes it quicker. |

## 7. Reset between runs

In the repo (`dist/explorer` for the facilitator, your clone for a leader), in the gate terminal:

```zsh
./gate reset
```

It asks first, then saves the group's records to `.records/<date-time>/` (git-ignored, kept by every reset, hidden from the agent), puts the repo back to `start`, removes untracked files such as `out/` (keeping `.venv`) and returns to level 0. The `Dataset:` line goes back to pulsars, so set it again with `./gate dataset dimuons` if needed. The facilitator can instead rebuild, which also gives fresh packs and secrets; leaders then need a new bundle.

## 8. What to record

`./gate reset` saves these to `.records/<date-time>/`, and the leader sends that folder to the facilitator:

- `state.json`: per-level times, hints, failed attempts and skips.
- `git-log.txt`: the commits are the group's path through the plan. `work.bundle` holds the group's code (clone it with `git clone work.bundle`).
- `LOG.md` (the Scribe's notes), `PLAN.md`, `TESTS.md` and `REVIEW.md`. The last two comparisons are the show-and-tell material. The talk prompts are not saved by the gate, so anything written there is the Scribe's own.

Collect the folder before the next group uses the laptop; it is never in a bundle. For the show-and-tell, ask each group: one decision the agent made that they hadn't (and whether they changed it); one thing the tests did not catch; one finding they rejected, and why; and the moment the browser showed something the check could not. Also ask what time Level 1 finished: it is the calibration number for the next run.
