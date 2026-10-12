# Agentic AI for Physics Research: Workshop Exercises

Hands-on exercises for a one-hour workshop that teaches physicists to work well with coding agents. Groups of two to five sit with a leader, drive [Claude Code](https://code.claude.com) on a deliberately modest model, and climb through gated levels. The physics is the vehicle; the habit being drilled is the same every time: **understand, define the check, plan, small steps, evidence, review, recover.**

**This repository is public, so the answers are too.** Participants work in a small repo built from this one and never need to see it. If you run the workshop, point attendees at the built repo, not here.

## Who this is for

| You are | Start here |
|---|---|
| Organising the workshop for a group or department | [Quick start](#quick-start), then the walkthrough of the exercise you chose |
| Leading one group on the day | [Lead a group](#lead-a-group) |
| Adapting or writing an exercise | [Build and extend](#build-and-extend) |

## The exercises

| | Exercise | Core lesson | Model | Status | Facilitator walkthrough |
|---|---|---|---|---|---|
| **B** | **Speed Run.** A correct but painfully slow pair counter for galaxy clustering. Make it fast without ever getting a wrong answer: measure first, survive the memory wall, change the algorithm, then race. Every run is checked against golden counts you cannot see; a wrong answer scores zero, and "correct" is a decision the group must declare. | Measure first; a correctness gate is non-negotiable | Haiku | **Ready** (self-tested; live calibration pending) | [`exercises/speed-run/FACILITATOR-WALKTHROUGH.md`](exercises/speed-run/FACILITATOR-WALKTHROUGH.md) |
| **D** | **The TDD Ladder.** Implement one small binning function several times, from "just build it" to tests you can trust. At every step an objective scorecard runs the group's tests against deliberately broken copies of the function and reports how many they catch. | You define "correct"; the agent cannot | Haiku | **Ready** (self-tested; live calibration pending) | [`exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md`](exercises/tdd-ladder/FACILITATOR-WALKTHROUGH.md) |
| A | **Two Roads.** Two H₀ engines disagree on the same catalogue. Find out why, fix it properly, and leave code you would trust. | Evidence-driven debugging; agreement is not correctness | Haiku | Designed | `docs/01-two-roads.md` |
| C | **Fortran Archaeology.** Port legacy code and prove the port is equivalent. | Establish the oracle before you change anything | Sonnet | Designed | `docs/03-fortran-archaeology.md` |

Each exercise's **facilitator walkthrough** is the authoritative guide to that exercise: its commands, levels, gate answers, what to watch for, the fallbacks, and how to reset and distribute it. It contains spoilers and is never copied into a participant repo. The pedagogical designs live in `docs/01`–`04`, and `docs/00-facilitator-guide.md` has the 15-minute lecture, group roles, the run-sheet and calibration advice for the whole session.

## Quick start

Requirements: macOS with the Xcode Command Line Tools (`xcode-select --install`; they provide `git` and `clang`), Python 3.11 or newer (for example `brew install python@3.13`), Claude Code **2.1.295 or newer** (`claude --version`), and a Claude account that can run Claude Code on Haiku.

```zsh
git clone <this repository> workshop && cd workshop

# A facilitator passphrase, kept outside every repo (not echoed; at least 8 characters)
mkdir -p ~/.config/workshop
read -s "pass?Passphrase: " && print -r -- "$pass" > ~/.config/workshop/master-passphrase && unset pass
chmod 600 ~/.config/workshop/master-passphrase

# Build one participant repo and set up its Python environment (replace <name> with speed-run or tdd-ladder)
python3 tools/build.py <name> --master-passphrase-file ~/.config/workshop/master-passphrase
cd dist/<name>
./preflight --setup      # creates .venv and installs the exercise's pinned packages (network, once)
./preflight              # must end with "Preflight passed"
claude                   # accept the workspace trust dialog once; type /hooks and check four events are listed; /exit
```

The build uses `/opt/homebrew/bin/python3.13` for the participant environment. If your Python 3.11+ lives elsewhere, add `--setup-python /path/to/python3`. The build tool itself runs on the system `python3` (3.9).

Then open the exercise's walkthrough and play it through once yourself, on Haiku, before the day.

## How a session works

- **Two windows.** Claude Code in a large window, driven by the group. A small **gate terminal** that only humans type in.
- **Gates.** Each level ends with a gate: a check that the work is done, plus a question the humans must answer to show they understood it. `./gate unlock` runs the check, asks, and decrypts the next level from the encrypted **vault** shipped with the repo. Claude's shell has no terminal, so it cannot type there.
- **A teacher, not an oracle.** A short **persona** is injected into every prompt and tells Claude how to behave at that level: literal at first, so the group sees what happens without discipline, then a coach that runs the group's experiments but does not hand over answers. Every persona also asks Claude to explain, briefly, what it is about to do and what each result means, so that people who missed the introduction can keep up.
- **Guard rails.** A hook blocks Claude from the vault, the gate, package installs and the files a level has frozen. Every block carries a teaching message, and the block itself often starts the best discussion of the hour.
- **Hints, logs, a master key.** Three timed hint tiers per level; every unlock, hint and reflection logged for the show-and-tell; a facilitator passphrase to skip a stuck group or grant a **power-up** to a stronger model.

This is a learning scaffold, not an exam proctor. A group can cheat; they would be cheating themselves out of their hour of practice. The limits are written down in [`gatekit/README.md`](gatekit/README.md#11-honest-limits) and are worth saying aloud in the lecture.

## Lead a group

Open two Terminal windows in the participant repo. In the first, `claude`; in the second (a fresh window, not one opened from inside Claude Code), the gate commands. The session starts in plan mode: `Shift+Tab` leaves it once the group has agreed a plan. `/model` to anything but Haiku is refused until the facilitator grants a power-up. Confirm the model with `/status` (Haiku may misname itself when asked), and during setup check that `/model` to Sonnet is refused by the hook. The level brief is the participant repo's `README.md` at level 0 and `BRIEF.md` afterwards.

The gate commands are the same in every exercise:

| Command | What it does |
|---|---|
| `./gate status` | Level, persona, minutes on level, hints used |
| `./gate brief` | Print the current brief |
| `./gate hint` | Next hint tier (tiers unlock at 0, 5 and 10 minutes on the level) |
| `./gate unlock` | Run the check, ask the gate question, open the next level, log a reflection |
| `./gate skip --master` | Facilitator skip, with the passphrase and a logged reason |
| `./gate allow-model sonnet` | Facilitator power-up to a stronger model |

Each exercise adds its own tool (`./tdd` for the TDD Ladder, `./race` for the Speed Run) whose human-only commands are listed in the exercise's walkthrough and in the participant `README.md`. The commands that change progress refuse to run from Claude's shell and say why. Read refusals aloud: they are the lesson, not a bug.

**Give the repo to group leaders** as a bundle of the built repo, never this repository:

```zsh
cd dist/<name>
git bundle create ~/Desktop/<name>.bundle --all
# leader: git clone <name>.bundle <name> && cd <name> && ./preflight --setup && ./preflight
```

**Reset between runs:** `./gate reset`, then `git reset --hard start && git clean -fdx -e .venv -e .workshop` (keeps `.venv`; `-x` also removes ignored build products such as old result plots and compiled `.so` files). The walkthroughs have the exercise-specific details.

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
- Everything the participant repo runs is standard-library Python, except the exercise code itself.
- `BUILD-SPEC.md`, `CLAUDE.md` and `PROGRESS.md` are the engineering spec, instructions and hand-off notes used to build this repository with Claude Code. `docs/DECISIONS.md` records the verified facts about Claude Code hooks and permissions, every deviation from the designs, and the review findings.

### Self-tests

Run after the quick start. Each exercise self-test rebuilds its `dist/<name>` (keeping `.venv`), so do not run it on a repo a group is using.

```zsh
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'; cd ..
python3 exercises/tdd-ladder/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
python3 exercises/speed-run/selftest/run.py --master-passphrase-file ~/.config/workshop/master-passphrase
```

The first runs the toolkit's unit tests. The others verify each exercise's hidden assets and then play the whole exercise through a pseudo-terminal: every level, every gate refusal, the expected result bands, the master skip and the reset. They leave the repo clean at level 0.

## Licence

MIT. See `LICENSE`.
