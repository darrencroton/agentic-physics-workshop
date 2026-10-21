# TDD Ladder: group leader quickstart

Private: contains gate answers. Do not show it to your group.

## What this is

Your group builds one small function, `binned_weighted_mean`, several times, starting badly on purpose, while a scorecard shows how good their tests really are. The lesson: **the group defines "correct"; the agent cannot.** You are the Coach: ask questions, fix tooling, don't drive. Full detail is in `FACILITATOR-WALKTHROUGH.md` (section 3 for setup).

Before the day, on your laptop:

- [ ] Python 3.11+, git, a git identity, and Claude Code 2.1.295 or newer signed in.
- [ ] Cloned the bundle; `./preflight` (first run sets up `.venv`: needs the network, about a minute) ends with "Preflight passed". It also checks the skill and agent files.
- [ ] In `claude`, accept the trust dialog; `/hooks` lists four events, and `/model` to another model is refused.
- [ ] Played Levels 0 and 1, then `./gate reset`.

## On the day

**Opening (60 seconds).** "We'll build the same feature several times, starting badly on purpose, and a scorecard will show how good our tests are each time. First two levels Claude is literal: watch what it decides for us. After that we take control: we decide, we compute the expected answers, and the tooling won't let anyone, Claude included, edit tests while we make them pass."

**Roles.** 2 people: you are Coach and Navigator; the other is Driver, Sceptic and Scribe. 3: Driver (rotating) and Sceptic; you also Navigate and Scribe. 4: Driver, Navigator, Sceptic; you also Scribe. 5: Driver, Navigator, Sceptic, Scribe; you only coach. The Driver rotates at each gate.

**Two windows.** Agent window (large, Claude Code, Driver types, starts in plan mode: `Shift+Tab` to leave it). Gate terminal (a fresh Terminal window, not Claude's shell) for every `./gate` and `./tdd` command.

| From Go | Expected |
|---|---|
| 5 min | Level 0 scored |
| 11 min | Level 1 scored |
| 21 min | `SPEC.md` done, client spec read |
| 36 min | 5 or more cycles |
| 44 min | Level 4 attempted |

## Level by level

**0. Just build it (5 min).** Paste the request, accept anything, `make plot`, `./tdd score`, `./gate unlock`. Good looks like: a poor score, about 4/12 acceptance. Nudge: "Don't polish; which decisions did Claude make for us?" Gate answer: the acceptance count printed by `./tdd score`.

**1. "Use TDD, please" (6 min).** Same request plus "Use test-driven development." Good looks like: tests and code arriving together, all green, numbers from Claude's head. Nudge: "Did anything ever fail first? Where did that expected value come from?" No graded question.

**2. Decide before you test (10 min).** Claude interviews them and writes `SPEC.md` (six or more numbered decisions); no code. Good looks like: arguments about what the error bar means and where a bin's point sits. Nudge: "Do you all agree?" Cap the interview at 8 minutes. No graded question; they then read `CLIENT_SPEC.md` and adopt it.

**3. Red, green, refactor (15 min).** Each cycle: `./tdd red "<behaviour>"`, one test, Sceptic's hand-computed number, commit, `./tdd green`, minimum code, `./tdd done`. Five closed cycles, 0 false alarms, 9/16 mutants killed. Nudge: "Sceptic, did you compute that?" Let the "tests are frozen" refusal spark discussion. Gate answer: any spec ID under "surviving mutants violate" in the last score (such as S4), or `none` if 16/16.

**4. Think like a physicist (8 min).** Three property tests (uniform sigma, affine equivariance, seeded coverage) usually reach 14 to 16 of 16. Nudge: "What is the binomial sigma for your N?" Gate answer: about 0.0093 (square root of 0.683 x 0.317 / 2500); 0.0090 to 0.0096 passes, and "0.93%" works.

**5. Stretch: test the tests (5 min).** Claude writes about ten mutants of their own code; they run the suite on each and fill in `## Mutation report` in `LOG.md`. Nudge: "Show me the run." Closing talk prompt: which test would you delete?

After each gate a "talk it over" prompt appears with nothing to type: use it for 30 seconds of conversation.

## When stuck

- A command says it is for humans: use a fresh Terminal window, not Claude Code's shell.
- Hooks don't fire, or the agent edits what should be frozen: the trust dialog was missed (`/hooks` is empty). `/exit`, run `claude` again, accept trust.
- The agent names the wrong model: trust `/status`, not what it says. The session is locked to Haiku unless the facilitator grants a power-up.
- The agent is going in circles after two failed corrections: `/clear` and a better prompt that includes what you learned.
- A guard or gate refusal: read it aloud. It is usually the lesson and it names the fix.
- A stuck group: hints first (`./gate hint`), then call the facilitator, who holds the master passphrase for `./gate skip --master`.
- Hints: three tiers at 0, 5 and 10 minutes on the level; Levels 0, 3 and 4 add the answer at 13. A power-up (`./gate allow-model sonnet`) also needs the master passphrase.
- Group is tangled: `./tdd new-attempt` restarts the level from the stub (then score again).

## After

`./tdd ladder` prints the score curve for the show-and-tell. `./gate reset` saves the group's records (state, ladder, git log, `LOG.md`, `SPEC.md`) and the group's code as `work.bundle` (clone it with `git clone work.bundle`) to `.records/<date-time>/` and returns to level 0, also removing the `attempt-*` branches. `.records` is a hidden folder: `open .records` shows it in Finder, and reset prints its path. Send that folder to the facilitator.
