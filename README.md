# Agentic AI for Physics Research: Workshop Exercises

Hands-on exercises for a workshop of about 70 minutes (a 15-minute lecture, then 45 minutes hands-on) that teaches physicists to work well with coding agents. Groups of two to five sit with a leader, drive [Claude Code](https://code.claude.com) on a deliberately modest model, and climb through gated levels. The physics is the vehicle; the habit being drilled is the same every time: **understand, define the check, plan, small steps, evidence, review, recover.**

**This repository is public, so the answers are too.** Participants work in a small repo built from this one and never need to see it. If you run the workshop, point attendees at the built repo, not here.

## Who this is for

| You are | Start here |
|---|---|
| Organising the workshop (the facilitator) | [Run the workshop](#run-the-workshop) |
| Leading one group on the day | The walkthrough for your exercise, from section 3 ("Group leaders: set up your laptop"). The facilitator sends it to you with your copy of the repo; you do not need this repository. |
| Adapting or writing an exercise | [Build and extend](#build-and-extend) |

## The exercises

| | Exercise | Core lesson | Model | Status | Facilitator walkthrough |
|---|---|---|---|---|---|
| **B** | **Speed Run.** A correct but painfully slow pair counter for galaxy clustering. Make it fast without ever getting a wrong answer: measure first, survive the memory wall, change the algorithm, then race. Every run is checked against golden counts you cannot see; a wrong answer scores zero, and "correct" is a decision the group must declare. | Measure first; a correctness gate is non-negotiable | Haiku | **Ready** (self-tested; live calibration pending) | [`exercises/speed-run/FACILITATOR-WALKTHROUGH.md`](exercises/speed-run/FACILITATOR-WALKTHROUGH.md) |
| **D** | **The TDD Ladder.** Implement one small binning function several times, from "just build it" to tests you can trust. At every step an objective scorecard runs the group's tests against deliberately broken copies of the function and reports how many they catch. | You define "correct"; the agent cannot | Haiku | **Ready** (self-tested; live calibration pending) | [`exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md`](exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md) |
| A | **Two Roads.** Two H₀ engines disagree on the same catalogue. Find out why, fix it properly, and leave code you would trust. | Evidence-driven debugging; agreement is not correctness | Haiku | Designed | `docs/01-two-roads.md` |
| C | **Fortran Archaeology.** Port legacy code and prove the port is equivalent. | Establish the oracle before you change anything | Sonnet | Designed | `docs/03-fortran-archaeology.md` |

Each exercise's **facilitator walkthrough** is the operating guide to that exercise, for the facilitator and the group leaders: building and distributing it, setting up a leader's laptop, running the session, every level with its gate answers, what to do when something goes wrong, and how to reset. It contains spoilers and is never copied into a participant repo. `docs/00-facilitator-guide.md` covers the whole session: the lecture, group roles, the leaders' briefing, the run-sheet and the trial. The pedagogical designs live in `docs/01`–`04`; where an exercise has been built, its walkthrough supersedes the design.

## How a session works

- **Two windows.** Claude Code in a large window, driven by the group. A small **gate terminal** that only humans type in.
- **Gates.** Each level ends with a gate: a check that the work is done, plus a question the humans must answer to show they understood it. `./gate unlock` runs the check, asks, and decrypts the next level from the encrypted **vault** shipped with the repo. Claude's shell has no terminal, so it cannot type there.
- **A teacher, not an oracle.** A short **persona** is injected into every prompt and tells Claude how to behave at that level: literal at first, so the group sees what happens without discipline, then a coach that runs the group's experiments but does not hand over answers. Every persona also asks Claude to explain, briefly, what it is about to do and what each result means, so that people who missed the introduction can keep up.
- **Guard rails.** A hook blocks Claude from the vault, the gate, package installs and the files a level has frozen. Every block carries a teaching message, and the block itself often starts the best discussion of the hour.
- **Hints, logs, a master key.** Three timed hint tiers per level; every unlock, hint and reflection logged for the show-and-tell; a facilitator passphrase to skip a stuck group or grant a **power-up** to a stronger model.

This is a learning scaffold, not an exam proctor. A group can cheat; they would be cheating themselves out of their hour of practice. The limits are written down in [`gatekit/README.md`](gatekit/README.md#11-honest-limits) and are worth saying aloud in the lecture.

## Run the workshop

You build one participant repo per exercise from this repository, rehearse it, and send each group leader a copy as a git bundle. Leaders and participants never need this repository.

1. **Plan.** Choose the exercises and the group leaders, and check everyone's Claude accounts: `docs/00-facilitator-guide.md` sections 1, 7 and 11.
2. **Install the requirements** on your Mac: the Xcode Command Line Tools (`xcode-select --install`; they provide `git` and `clang`), Python 3.11 or newer (for example `brew install python@3.13`), Claude Code **2.1.295 or newer** (`claude --version`), a Claude account that can run Claude Code on Haiku, and a git identity (`git config --global user.name` and `user.email`).
3. **Clone this repository and create the master passphrase.** You type it to skip a stuck group or grant a power-up; it is kept outside every repo.

   ```zsh
   git clone <this repository> workshop && cd workshop
   mkdir -p ~/.config/workshop
   read -s "pass?Passphrase: " && print -r -- "$pass" > ~/.config/workshop/master-passphrase && unset pass   # not echoed; at least 8 characters
   chmod 600 ~/.config/workshop/master-passphrase
   ```

4. **Build, check and rehearse each exercise you will run:** section 1 of its walkthrough. Play it through once yourself, on Haiku, before the day; `docs/00` section 6 has the fuller calibration matrix.
5. **Give each leader their repo:** section 2 of the walkthrough. You send a bundle made from a freshly built or reset repo, together with the walkthrough, and decide who types the master passphrase on the day. Leaders set up their own laptops with section 3.
6. **Brief the leaders, then run the day:** `docs/00-facilitator-guide.md` has the leaders' briefing (section 7), the lecture (section 3) and the run-sheet and stuck protocol (section 8).
7. **Afterwards:** each walkthrough says what to copy out for the record and how to reset between runs. For a trial run, `docs/00` section 9 says what to measure.

## Build and extend

```
gatekit/            shared toolkit: gate CLI, pack crypto, hooks, preflight, pty test helpers, README
exercises/<name>/   private source per exercise: levels, personas, hints, hidden assets, self-test, walkthrough
tools/build.py      assembles dist/<name>/ from the two above
dist/<name>/        generated participant repo (gitignored here)
docs/               the pedagogical designs and the decision log
```

- The toolkit, its manifest schema, gate types and limits are documented in [`gatekit/README.md`](gatekit/README.md).
- An exercise is a directory under `exercises/` with a `manifest.json`, a plaintext `level0/`, one directory per later level (`BRIEF.md`, `persona.txt`, `hints.json`, `guard.json`, any new files, all encrypted at build time), a participant `CLAUDE.md`, an optional exercise tool and hidden assets, a self-test and a facilitator walkthrough. The TDD Ladder and the Speed Run are the worked examples; `exercises/speed-run/PLAN.md` shows the design contract the Speed Run was built from.
- Everything the participant repo runs is standard-library Python, except the exercise code itself. `tools/build.py` and `gatekit/` run on the system `python3` (3.9 or newer); the exercise code runs in the participant repo's `.venv` (Python 3.11 or newer).
- `BUILD-SPEC.md`, `CLAUDE.md` and `PROGRESS.md` are the engineering spec, instructions and hand-off notes used to build this repository with Claude Code. `docs/DECISIONS.md` records the verified facts about Claude Code hooks and permissions, every deviation from the designs, and the review findings.

### Self-tests

Run once the exercise has been built and its `.venv` set up (step 4 of [Run the workshop](#run-the-workshop)). Each exercise self-test rebuilds its `dist/<name>` (keeping `.venv`), so do not run it on a repo a group is using.

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/speed-run/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

The first runs the toolkit's unit tests. The others verify each exercise's hidden assets and then play the whole exercise through a pseudo-terminal: every level, every gate refusal, the expected result bands, the master skip and the reset. They leave the repo clean at level 0.

## Licence

MIT. See `LICENSE`.
