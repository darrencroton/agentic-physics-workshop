# Speed Run: group leader quickstart

Private: it holds gate answers. Keep it away from participants.

## 1. What this is, and before the day

Your group makes a slow, correct pair counter fast on 200,000 galaxies, while a hidden check punishes any wrong answer. Four levels in about 45 minutes: measure, vectorise, reduce the work, race. You are the Coach: ask questions, fix tooling, don't drive (unless there are two of you).

Before the day (details in section 3 of `FACILITATOR-WALKTHROUGH.md`):

- [ ] Apple-silicon Mac with Xcode Command Line Tools (`git`, `clang`) and Python 3.11 or newer.
- [ ] Claude Code 2.1.295 or newer, signed in (Haiku, plus Sonnet for power-ups).
- [ ] A git identity (`git config --global user.name` and `user.email`).
- [ ] Cloned the bundle; `./preflight` (first run sets up `.venv`: needs the network, about a minute) ends with "Preflight passed". It also checks the skill and agent files.
- [ ] In `claude`, accept the trust dialog; `/hooks` lists four events, and `/model` to another model is refused.
- [ ] You have played Level 0 once, then `./gate reset`.

## 2. On the day

**Opening (60 seconds):** "This is a race, but a wrong answer scores zero, and we declare what correct means before we see results. The rhythm: measure, hypothesise, change one thing, run the check, commit. Claude is on a modest model and won't know where the time goes unless we make it measure. The keyboard rotates at each gate."

**Roles by group size** (the Driver rotates through everyone except you):

| Size | Roles |
|---|---|
| 2 | You: Coach and Navigator. Other: Driver, Sceptic, Scribe. |
| 3 | Driver, Sceptic. You: Coach, Navigator, Scribe. |
| 4 | Driver, Navigator, Sceptic. You: Coach, Scribe. |
| 5 | Driver, Navigator, Sceptic, Scribe. You: Coach. |

**Two windows:** a large Claude Code window (only the Driver types) and a separate gate terminal for `./gate` and `./race submit`. Open the gate terminal from Terminal itself, not from inside Claude Code. The session starts in plan mode: `Shift+Tab` leaves it.

**Checkpoints from Go:** 8 min Level 0 done; 18 min Level 1 done; 32 min Level 2 done; 40 min first Level 3 submission.

## 3. Level by level

Each gate ends with a "talk it over" prompt: nothing to type, so ask it aloud.

**Level 0, measure (7 min).** Goal: bench the reference at N = 500, 1000, 2000, then `make profile` and `make fit`. Good: exponent about 2, predicted time about 37 minutes at 200,000 on an M1 Max (laptops differ), and `math.sqrt` called 499,500 times at N = 1000. Nudge: "How many of those calls are pairs we actually need?" Gate answer: **499500** (N(N-1)/2; "500k" also passes). Talk: the predicted runtime and how they got it.

**Level 1, vectorise (10 min).** Goal: a numpy `fast.py`, with a memory estimate before any run at 20,000. Good: the 20k run is killed at 2.5 GB, then chunking in a few hundred rows passes in about 3 s. Nudge: "Sceptic, what's the estimate? Check the arithmetic." Gate answer: **320** (200,000² × 8 bytes = 320 GB; 298 to 320 accepted, so GiB works). Talk: estimate versus measured.

**Level 2, reduce the work (14 min).** Goal: a cell list or `cKDTree` at 200,000 in under 60 s and 1.5 GB, and a written decision on the division. Good: a diff table is read before anyone says "just floating point", and the division goes in `race.toml` and `LOG.md` before the passing run. Nudge: "Show me the per-bin differences. Why do they differ?" Judge the justification (the Poisson argument), not the number. Gate answer: **(c)** (golden 100 allows 0.5, so a shift of 1 fails; golden 1,000,000 allows 50, so a shift of 10 passes). Talk: division and evidence.

**Level 3, open race (11 min).** Goal: commit, then `./race submit`, repeatedly. Good: every submit has a commit and a `make bench` number behind it; a C cell list (`-O2 -shared -ffp-contract=off`) wins by several times. Nudge: "Was that number from the harness? Is it committed?" No graded question: one passed submission opens the gate. A C entry built with default flags fails `exact` on the hidden catalogue (fused multiply-adds) and scores 0: a good story. Give the quiet member `./race submit`. Talk: biggest wrong turn and the evidence.

## 4. When stuck

- A command says it is for humans: use a fresh Terminal window, not Claude Code's shell.
- Hooks don't fire, or the agent edits what should be frozen: the trust dialog was missed (`/hooks` is empty). `/exit`, run `claude` again, accept trust.
- The agent names the wrong model: trust `/status`, not what it says. The session is locked to Haiku unless the facilitator grants a power-up.
- The agent is going in circles after two failed corrections: `/clear` and a better prompt that includes what you learned.
- A guard or gate refusal: read it aloud. It is usually the lesson and it names the fix.
- A stuck group: hints first (`./gate hint`), then call the facilitator, who holds the master passphrase for `./gate skip --master` (plus `./race install-solution <level>`).
- Hints: tiers at 0, 5 and 10 minutes; Levels 0 to 2 give the gate answer at 13. A power-up (`./gate allow-model sonnet`) or a level's solution (Levels 1 to 3) needs the facilitator; after a solution, re-run `make bench`. `./gate skip --master` is the last resort.
- Gate says the run is stale: `paircount/` or `race.toml` changed, so re-run `make bench`.
- Laptop freezing at Level 1: close other apps and kill the Python process in Activity Monitor.

## 5. After

- `./gate reset` saves the group's records (state, bench log, board, `git-log.txt`, `LOG.md`, `race.toml`) and the group's code as `work.bundle` (clone it with `git clone work.bundle`) to `.records/<date-time>/` and returns to level 0. `.records` is a hidden folder: `open .records` shows it in Finder, and reset prints its path. Send that folder to the facilitator.
- For show-and-tell: which division and why, and the biggest wrong turn with the evidence that showed it.
