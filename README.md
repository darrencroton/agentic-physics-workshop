# Agentic AI for Physics Research: Workshop Exercises

Hands-on exercises for a workshop of about 70 minutes (a 15-minute lecture, then 45 minutes hands-on) that teaches physicists to work well with coding agents. Groups of two to five sit with a leader, drive [Claude Code](https://code.claude.com) on a modest model (Haiku or Sonnet), and climb through gated levels. The physics is the vehicle; the habit being drilled is the same every time: **understand, define the check, plan, small steps, evidence, review, recover.**

**This repository is public, so the answers are too.** Participants work in a small repo built from this one and never need to see it. If you run the workshop, point attendees at the built repo, not here.

## Who this is for

| You are | Start here |
|---|---|
| Organising the workshop (the facilitator) | [Run the workshop](#run-the-workshop) |
| Leading one group on the day | Your exercise's `LEADER-QUICKSTART.md` (one or two pages: set-up, the session, each level, when stuck), then its facilitator walkthrough for the detail, from "Group leaders: set up your laptop" onwards. The facilitator sends both with your copy of the repo, so you do not need this repository. |
| Adapting or writing an exercise | [Build and extend](#build-and-extend) |

## The exercises

| | Exercise | Core lesson | Model | Status | Guide |
|---|---|---|---|---|---|
| **B** | **Speed Run.** Make a correct but painfully slow galaxy pair counter fast, without ever getting a wrong answer. Every run is checked against hidden golden counts, and a wrong answer scores zero. | Measure first; a correctness gate is non-negotiable | Haiku | **Ready** (self-tested; live calibration pending) | [walkthrough](exercises/speed-run/FACILITATOR-WALKTHROUGH.md) |
| **D** | **The TDD Ladder.** Implement one small binning function several times, from "just build it" to tests you can trust. A scorecard runs the group's tests against deliberately broken copies and reports how many they catch. | You define "correct"; the agent cannot | Haiku | **Ready** (self-tested; live calibration pending) | [walkthrough](exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md) |
| **E** | **Explorer.** Have Claude build a browser tool that plots a real dataset (ATNF pulsars or CMS dimuons) in 2D or 3D. Plan it, build it in checked steps, test it and have it reviewed, committing as you go. | Plan, build, test, review: the workflow as a habit | Sonnet | **Ready** (self-tested; live calibration pending) | [walkthrough](exercises/explorer/FACILITATOR-WALKTHROUGH.md) |
| A | **Two Roads.** Two H₀ engines disagree on the same catalogue. Find out why, fix it properly, and leave code you would trust. | Evidence-driven debugging; agreement is not correctness | Haiku | Designed | [design](docs/01-two-roads.md) |
| C | **Fortran Archaeology.** Port legacy code and prove the port is equivalent. | Establish the oracle before you change anything | Sonnet | Designed | [design](docs/03-fortran-archaeology.md) |

Each exercise's **facilitator walkthrough** is its operating guide, for the facilitator and the group leaders: building and handing out the repo, setting up a leader's laptop, running the session, every level with its gate answers, troubleshooting and reset. It contains spoilers and is never copied into a participant repo. The [facilitator guide](docs/00-facilitator-guide.md) covers the whole session: the lecture, group roles, the leaders' briefing, the run-sheet and the trial. The pedagogical designs are in `docs/01`–`05`; once an exercise is built, its walkthrough supersedes its design.

## How a session works

- **Two windows.** Claude Code in a large window, driven by the group. A small **gate terminal** that only humans type in.
- **Gates.** Each level ends with a gate: a check that the work is done, then, at some gates, a question only someone who did the work can answer. `./gate unlock` runs the check, asks, decrypts the next level from the encrypted **vault** shipped with the repo, and ends with a short prompt for the group to talk over (nothing to type). Claude's shell has no terminal, so it cannot type there.
- **A teacher, not an oracle.** A short **persona** is injected into every prompt and tells Claude how to behave at that level: for example, literal at first, so the group sees what happens without discipline, then a coach that runs the group's experiments but does not hand over answers. Every persona also asks Claude to explain briefly what it is about to do and what each result means, so people who missed the introduction can keep up.
- **Guard rails.** A hook blocks Claude from the vault, the gate, package installs and the files a level has frozen. Every block carries a teaching message, and Claude is told to report a block rather than work round it; the block itself often starts the best discussion of the hour.
- **Hints, logs, a master key.** Three timed hints per level, and a fourth that gives the answer at levels with a graded question; every unlock and hint logged, and a Scribe's `LOG.md` for the show-and-tell; a facilitator passphrase to skip a stuck group or grant a **power-up** to a stronger model.

This is a learning scaffold, not an exam proctor. A group can cheat; they would be cheating themselves out of their hour of practice. The limits are written down in [`gatekit/README.md`](gatekit/README.md#11-honest-limits) and are worth saying aloud in the lecture.

## Run the workshop

You build one participant repo per exercise from this repository, rehearse it, and send each group leader a copy as a git bundle. Leaders and participants never need this repository.

1. **Plan.** Choose the exercises and the group leaders, and check everyone's Claude accounts: see [At a Glance](docs/00-facilitator-guide.md#1-at-a-glance), [Pre-Event Setup](docs/00-facilitator-guide.md#7-pre-event-setup) and [Open Decisions](docs/00-facilitator-guide.md#11-open-decisions-for-you) in the facilitator guide.
2. **Install the requirements** on your Mac: the Xcode Command Line Tools (`xcode-select --install`; they provide `git` and `clang`, which only the Speed Run needs), Python 3.11 or newer (for example `brew install python@3.13`), Claude Code **2.1.295 or newer** (`claude --version`), a Claude account that can run Claude Code on Haiku (and Sonnet, for Explorer), and a git identity (`git config --global user.name` and `user.email`).
3. **Clone this repository and create the master passphrase.** You type it to skip a stuck group or grant a power-up; it is kept outside every repo.

   ```zsh
   git clone <this repository> workshop && cd workshop
   mkdir -p ~/.config/workshop
   read -s "pass?Passphrase: " && print -r -- "$pass" > ~/.config/workshop/master-passphrase && unset pass   # not echoed; at least 8 characters
   chmod 600 ~/.config/workshop/master-passphrase
   ```

4. **Build, check and rehearse each exercise you will run:** `python3 tools/build.py <exercise>` (it reads the passphrase above and keeps `.venv`), then follow "Facilitator: build and rehearse" in its walkthrough. Play it through once yourself, on the exercise's model, before the day; [Building and Calibrating the Exercises](docs/00-facilitator-guide.md#6-building-and-calibrating-the-exercises) in the facilitator guide has the fuller calibration matrix.
5. **Give each leader their repo:** follow "Facilitator: give the repo to group leaders" in the walkthrough. Run `python3 tools/bundle.py <exercise>`: it checks the repo is freshly built or reset and writes `<exercise>.bundle` in the current folder. Send that, together with the walkthrough and the leader quickstart, and decide who types the master passphrase on the day. Leaders set up their own laptops with "Group leaders: set up your laptop". Groups bringing their own agent harness can do Explorer (they read `OTHER-AGENTS.md` in the repo); the other exercises need Claude Code.
6. **Brief the leaders, then run the day:** the facilitator guide has the leaders' briefing ([Pre-Event Setup](docs/00-facilitator-guide.md#7-pre-event-setup)), the [lecture](docs/00-facilitator-guide.md#3-the-pre-session-lecture-15-min) and the run-sheet and stuck protocol ([Running the Day](docs/00-facilitator-guide.md#8-running-the-day)).
7. **Afterwards:** each leader runs `./gate reset`, which saves the group's records to `.records/<date-time>/` and returns to level 0; they send you that folder ("What to record" in each walkthrough lists what is in it). For a trial run, [Trial With Your Research Group](docs/00-facilitator-guide.md#9-trial-with-your-research-group) says what to measure.

## Build and extend

```
gatekit/            shared toolkit: gate CLI, pack crypto, hooks, preflight, pty test helpers, README
exercises/<name>/   private source per exercise: levels, personas, hints, hidden assets, self-test, walkthrough
skills/             four take-home Claude Code skills (plan-code, style-code, test-code, review-code), shipped into the exercises that list them
tools/build.py      assembles dist/<name>/ from the three above
dist/<name>/        generated participant repo (gitignored here)
docs/               the pedagogical designs and the decision log
```

- The toolkit, its manifest schema, gate types and limits are documented in [`gatekit/README.md`](gatekit/README.md).
- An exercise is a directory under `exercises/` with a `manifest.json`, a plaintext `level0/`, one directory per later level (`BRIEF.md`, `persona.txt`, `hints.json`, `guard.json`, any new files, all encrypted at build time), a participant `workshop/AGENTS.workshop.md` (built into `AGENTS.md`, with a `CLAUDE.md` that imports it), an optional exercise tool and hidden assets, a self-test and a facilitator walkthrough. The TDD Ladder, the Speed Run and Explorer are the worked examples; `exercises/speed-run/PLAN.md` and `exercises/explorer/PLAN.md` show the design contracts they were built from.
- Everything the participant repo runs is standard-library Python, except the exercise code itself (numpy, scipy, matplotlib and pytest, and plotly and pytest-cov for Explorer, pinned in each exercise's `requirements.txt`). `tools/build.py` and `gatekit/` run on the system `python3` (3.9 or newer); the exercise code runs in the participant repo's `.venv` (Python 3.11 or newer).
- `BUILD-SPEC.md`, `CLAUDE.md` and `PROGRESS.md` are the engineering spec, instructions and hand-off notes used to build this repository with Claude Code. `docs/DECISIONS.md` records the verified facts about Claude Code hooks and permissions, every deviation from the designs, and the review findings.

### Self-tests

Run these once the exercise has been built and its `.venv` set up (step 4 of [Run the workshop](#run-the-workshop)). Each exercise self-test rebuilds its `dist/<name>` (keeping `.venv`), so do not run it on a repo a group is using.

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/speed-run/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/explorer/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

The first runs the toolkit's unit tests. The others verify each exercise's hidden assets and then play the whole exercise through a pseudo-terminal: every level, every gate refusal, the expected result bands, the master skip and the reset. They leave the repo clean at level 0.

## Licence

MIT. See `LICENSE`.
