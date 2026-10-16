# gatekit

## 1. What it is

gatekit is a stdlib-only toolkit that turns an exercise into a ladder of levels, each unlocked by a human at a terminal. A level's files sit in an encrypted pack until the group passes the level's check and answers its gate question(s); hooks keep Claude Code inside the current level's rules (the hooks are Claude Code only; on other agent harnesses the written rules in `AGENTS.md` are the fallback, by design). It is a learning scaffold, not an exam proctor (see "Honest limits").

`tools/build.py <exercise> --master-passphrase-file <path>` assembles `dist/<exercise>/` from `gatekit/` and `exercises/<exercise>/`. The output is wiped and recreated, then committed as "Workshop start" and tagged `start`.

```
dist/<exercise>/
  gate                     # launcher: python3, adds .gatekit/ to sys.path, calls gatekit.cli.main
  preflight                # machine readiness check; --setup builds .venv (rendered with __SETUP_PYTHON__)
  AGENTS.md                # participant rules (harness-neutral), from workshop/AGENTS.workshop.md
  CLAUDE.md                # rendered from gatekit/agents/CLAUDE.md: imports AGENTS.md, adds the Claude Code section
  OTHER-AGENTS.md          # only when the manifest sets "other_agents": true, from gatekit/agents/OTHER-AGENTS.md
  <level 0 files>          # copied from exercises/<name>/level0/
  <other workshop/ files>  # copied from exercises/<name>/workshop/ (launchers such as tdd, data, ...)
  .claude/
    settings.json          # model (rendered from models.default), deny rules, hook wiring
    hooks/                 # guard.py, model_lock.py, teacher_context.py, model_check.py
  .gatekit/                # frozen tool sources (never edited by hand)
    gatekit/               # this package
    manifest.json          # the manifest, with gate.verify written in by the build
    levels/0/              # level 0 private files (persona, hints, guard) used by gate reset
    <tool>/                # exercise tool package, plus _pepper.py when verified gates exist
    preflight_extra.py     # optional exercise-specific preflight checks
  .vault/                  # encrypted material, readable only through the gate
    level1.pack ...        # one pack per level 1..n
    master.check           # tiny pack that only the master slot opens; verifies the passphrase
    scoring.pack           # optional hidden assets (when exercises/<name>/hidden/ exists)
    keys.bin               # sealed per-level secrets for verified gates (soft barrier)
  .workshop/               # runtime state (gitignored in the participant repo)
    state.json             # progress, see section 7
    levels/N/              # unpacked per-level private files: persona.txt, hints.json, guard.json, BRIEF.md
```

`LOG.md` is created in the repo root the first time a hint, reflection or skip is logged.

### Instruction files

- `exercises/<name>/workshop/AGENTS.workshop.md` is required. The build writes it to `AGENTS.md`, the canonical, harness-neutral rules (standing rules, levels, the "Never" list). The build fails if it is missing.
- `CLAUDE.md` is rendered from the shared template `gatekit/agents/CLAUDE.md`: a first line `@AGENTS.md` (Claude Code's documented import, so the rules load once) and a short Claude Code section. `__MODEL_NAME__` is replaced by the manifest's `models.default`, capitalised (`Sonnet`, `Haiku`). Claude Code reads `AGENTS.md` only when there is no `CLAUDE.md`, which is why this file exists.
- `gatekit/agents/OTHER-AGENTS.md` is the single page for participants on another agent harness. The build copies it to the repo root only when the manifest sets `"other_agents": true`.
- The templates live in `gatekit/agents/`, not `gatekit/templates/`, because the build copies everything in `templates/` unconditionally.

## 2. The `gate` commands

All commands run as `./gate <command>`. A TTY means both stdin and stdout are terminals; otherwise the command prints "This command is for humans, in the gate terminal." and exits 3. Other errors exit 1, usage errors exit 2, Ctrl-C exits 130.

| Command | TTY required | Behaviour |
|---|---|---|
| `status` | No | Prints title, level and title (marks "complete"), persona, minutes on level against `target_minutes`, hints used of total, failed gate attempts, allowed models, then any `status_lines` from the exercise tool. |
| `brief` | No | Prints `.workshop/levels/N/BRIEF.md`; at level 0 with no such file, prints `README.md`. |
| `check` | No | Runs the level's check and prints `PASS: <reason>` or `FAIL: <reason>`; exit 0 or 1. Never prints the expected answer. |
| `unlock` | Yes | Runs the check (failure is logged as a failed attempt and stops). Asks each gate question, unlocks the next level by installing its pack, runs `post_unlock`, then prints the `pre_reflection_note`, then (if there are reflections) a "Quick reflection (saved to LOG.md, any answer is fine):" header and the reflection question(s), appending the answers to `LOG.md`. On the last level it sets `complete` instead of unpacking. A wrong answer prints "Not quite. Discuss and try again." and logs the failure (timestamp and kind only, never the answer). |
| `hint` | Yes | Shows the first unused tier in `hints.json`, provided `unlock_after_minutes` has passed on this level; otherwise says when it unlocks. Records the tier in `hints_used` and appends the text shown to `LOG.md`. A tier may carry `"text_from": "tool.name"`, naming a `hints` function that returns the text to show (for example an answer tailored to the group's data); an exception or an empty return falls back silently to the tier's static `text`, which is still required. |
| `skip --master` | Yes | Prompts for the master passphrase without echo, checks it against `.vault/master.check`, asks for a reason, records a skip, and unlocks the next level using the master slot (or marks the last level complete). Logs to `LOG.md`. A wrong passphrase is logged as a failed attempt of kind `master`. Without `--master` it errors. |
| `allow-model <name>` | Yes, plus master passphrase | Verifies the master passphrase, lower-cases the name, appends it to `allowed_models` and logs the power-up. |
| `reset` | Yes | Asks for confirmation (skipped with `--yes`), deletes the files later levels unlocked into the working tree (each level's `BRIEF.md` and its `files` targets), deletes `.workshop/`, copies `.gatekit/levels/0` to `.workshop/levels/0`, writes a fresh state and calls the tool's `on_reset(root)`. It does not otherwise touch the working tree; the message suggests `git reset --hard start`. |

`gate help`, `-h` and `--help` print usage.

## 3. Manifest schema

The manifest lives at `exercises/<name>/manifest.json` and is copied to `.gatekit/manifest.json`. `manifest.py` requires `exercise`, `title` and a non-empty `levels` list whose ids run 0..n in order; personas must be `literal`, `coach` or `collaborator`; gate types must be one of the four below; each question needs `id` and `prompt`; every question prompt and reflection must end (after trailing spaces) with `?`, `:` or `)`, and not `.)`, because the cursor sits straight after it; `contains` is valid only on `keyword` questions and each term must keep a letter or digit. Keys marked "build" are written or read by `tools/build.py`. JSON has no comments, so the annotations below are illustrative only.

```jsonc
{
  "exercise": "tdd-ladder",              // must match state.json; a mismatch tells you to reset
  "title": "The TDD Ladder",
  "tool": "tddtool",                     // optional: package under .gatekit/ (conditions, validators, hooks into status etc.)
  "other_agents": false,                 // optional boolean, default false: ship OTHER-AGENTS.md (build); other types are rejected
  "human_only": {"tdd": ["red", "green", "refactor", "done", "abort", "score", "new-attempt"]},  // optional and illustrative here: launcher -> subcommands only humans may run (see section 8); each exercise declares its own; absent means this tdd list
  "models": {
    "default": "haiku",                  // rendered into .claude/settings.json "model" (build)
    "allowed": ["haiku"]                 // initial state.allowed_models
  },
  "levels": [
    {
      "id": 0,                           // must equal the list index
      "title": "Just build it",
      "persona": "literal",              // literal | coach | collaborator (default coach)
      "target_minutes": 5,               // shown by status
      "files": {                         // pack path -> repo path, copied on unlock
        "BRIEF.md": "BRIEF.md",
        "CLIENT_SPEC.md": "CLIENT_SPEC.md"
      },
      "gate": {                          // the gate that leaves this level
        "type": "crypto",                // verified | crypto | crypto-reflection | none
        "condition": "tdd.score_recorded_at_level",   // verified: "tool.name" in tool.conditions
        "check": "checks/level0.py",     // crypto: script run from the repo root
        "python": "venv",                // crypto: "python3" (default), "venv" (.venv/bin/python) or a path
        "timeout": 600,                  // crypto: seconds (default 600)
        "verify": "<hex>",               // written by the build: SHA-256("verify" || T)
        "pass_message": "check passed",  // optional
        "fail_message": "the check ran but its output is not yet correct",   // optional
        "questions": [
          {
            "id": "h0",
            "prompt": "What is H0 to 1 d.p.?",
            "kind": "numeric",           // keyword | choice | numeric | numeric-log | free
            "decimals": 1,               // numeric (default 2), numeric-log (default 1)
            "lo": 69.9, "hi": 70.1,      // numeric / numeric-log accepted range (inclusive grid)
            "accept": ["a", "b"],        // keyword / choice: accepted synonyms or letters
            "contains": ["psi"],         // keyword (optional): any answer containing a term
            "validator": "tdd.equals_last_acceptance_count",  // verified: default "gate.answer"
            "wrong_hint": "Printed after a wrong answer.",    // optional
            "text_from": "tool.name"     // optional: "tool.name" in tool.questions
          }
        ],
        "reflection": "What surprised you?",           // one logged question, or
        "reflections": ["Q1?", "Q2?"],                 // several (takes precedence)
        "pre_reflection_note": "Printed before the reflection questions.",
        "post_unlock": "tdd.after_unlock"              // "tool.name" in tool.post_unlock
      }
    }
  ]
}
```

`human_only` maps an exercise launcher name (the executable at the repo root, such as `race`) to the subcommands Claude must never run. Names and subcommands must match `[A-Za-z0-9][A-Za-z0-9_-]*`. The guard builds its Bash patterns from it and the build renders the `settings.json` deny rules from it (section 8). When the field is absent the hard-coded TDD Ladder list applies (`tdd red|green|refactor|done|abort|score|new-attempt`); `{}` means no human-only exercise commands. Every launcher named in `human_only` is also frozen against edits and added to the build's executable launchers, alongside the hard-coded `gate`, `preflight`, `tdd` and `race`. The `gate` list is always hard-coded. A malformed field makes the build fail and the guard deny every Bash call.

`other_agents` is an optional boolean (default false). When true the build copies `gatekit/agents/OTHER-AGENTS.md` into the participant repo; set it only for an exercise that works without the Claude Code hooks (today, Explorer). `manifest.py` rejects any other type.

`skills` is an optional list of skill names; the build copies `skills/<name>/` from the builder repository into the participant repo's `.claude/skills/<name>/` for each one, and fails on a name with no `SKILL.md`. An exercise whose lesson depends on Claude getting no process advice (the TDD Ladder's literal levels) should leave it out.

`wrong_hint` is printed as `Hint: <text>` after "Not quite. Discuss and try again." when the gate rejects an answer. A `verified` gate prints the hint of the question that failed; a `crypto` gate cannot tell which question failed, so it prints the hint of every question asked. `text_from` names a `questions` function that returns `{"prompt": ..., "wrong_hint": ...}` to replace the static fields (for example to tailor the question to the group's own data). Either key may be omitted, and an exception or a bad return falls back silently to the static text, so the static `prompt` is still required. Both must be strings; `text_from` must be `tool.name`.

A level with no `gate` is treated as `{"type": "none"}`. For `verified` gates the only built-in validator is `gate.answer`, which checks the answer locally against the question's `accept`/range (`answers.matches`); anything else must be `tool.<name>`. `crypto` and `crypto-reflection` gates ignore `condition` and `validator`.

### Per-level directories and answers

Each level `N >= 1` has a private source directory `exercises/<name>/levels/N/`. The build requires `persona.txt` and `guard.json` in it, tars the whole directory deterministically and encrypts it as `.vault/levelN.pack`. Level 0 is not packed: `levels/0/` is copied to `.gatekit/levels/0/` and placed in `.workshop/levels/0/` by `gate reset`.

On unlock the pack is extracted to a temporary directory and then:

- every top-level file is copied into `.workshop/levels/N/`, so `persona.txt`, `hints.json` and `guard.json` stay private there (hints and guards are read from this directory);
- `BRIEF.md` is copied to the repo root even when the manifest omits it, and each entry in the level's `files` is copied from its pack path to its repo path (missing pack files abort the unlock).

Pack member paths are checked and any that escape the destination are refused.

`exercises/<name>/answers.json` supplies the token for each crypto gate, keyed by the level that holds the gate (not the level it unlocks):

```json
{"0": {"token": "<hex sha256 of canonical check output>"}}
```

The build needs an entry for every `crypto` and `crypto-reflection` gate, and fails otherwise. A crypto gate on the last level opens no pack, but its token still sets the `verify` value that lets `gate check` and `gate unlock` pass there. Because no pack checks the answer, such a gate may carry only `free` questions; the build refuses a graded one.

## 4. Gate types

T is the SHA-256 digest of the check script's canonical stdout. `verify = SHA-256("verify" || T)` is stored in the manifest, so `gate check` can print PASS or FAIL without holding any answer. The pack that a gate unlocks gets one slot per accepted secret plus a master slot.

| Type | Key material for the next level's pack | Notes |
|---|---|---|
| `crypto` | One slot per accepted answer, secret `T || 0x00 || canon(A)`. With several questions the canonical answers are joined with `\|` and the slots cover every combination of accepted forms (`free` questions contribute nothing). At unlock the typed answer yields one or more candidate forms (section 6) and every combination of them is tried as a secret. Plus the master slot. | The check must exit 0 and print output whose hash gives the `verify` value. Questions are graded by whether the pack opens. |
| `crypto-reflection` | As `crypto`: secret derived from T and the (usually empty) canonical answer. | Unlock behaves as `crypto`. Use `free` questions and a `reflection` so answers are logged, not graded. |
| `verified` | A per-level random 32-byte secret (hex from `secrets.token_hex(32)`) generated at build time, stored in `.vault/keys.bin` and released by the exercise tool's `level_secret(root, level)` after its `condition` and `validator`s pass. Plus the master slot. | Needed for group-specific outcomes (for example a score the group just recorded). |
| `none` | Empty secret `b""` plus the master slot. | Unlock needs no check or answer; `run_check` reports "No check at this level." |

Every pack has a master slot (secret: the stripped passphrase bytes). `.vault/master.check` is a pack of the single word `master` openable only by that slot, which is how `skip --master` and `allow-model` verify the passphrase.

`keys.bin` and the optional scoring pack secret (`scoring`) are sealed with a key from `SHA-256(exercise || 0 || pepper || 0)`, where the pepper is a random value written to `.gatekit/<tool>/_pepper.py` at build time. The key is therefore recoverable by anyone who can read the tool source.

Limits, stated plainly:

- `verified` gates are a soft barrier. They are obfuscation: the secrets are in `keys.bin`, sealed with a key derived from a pepper in the tool source. The guard, deny rules and persona stop Claude from reading them; a human with shell access can.
- `crypto` gates are only as strong as the answer space. A small multiple-choice space (or a narrow numeric grid) is guessable offline by trying every slot secret against the pack. A typed answer on a numeric gate can now carry up to 6 numbers, so each attempt at the prompt is up to 6 guesses (a wrong answer with 6 numbers costs about 6 x slots x 23 ms of PBKDF2 to refuse); the choice and keyword kinds still make one guess per attempt.
- The packs are pedagogical-grade encryption; see section 5.

## 5. Pack format and crypto

Implemented in `crypto.py` and `packs.py` with the standard library only. This is pedagogical-grade encryption, not for real secrets.

- **Payload:** a deterministic `tar.gz`: entries sorted, regular files only, mtime 0, uid/gid 0, empty user and group names, mode 0o755 if executable else 0o644, gzip mtime 0. Identical input gives identical bytes.
- **Content key:** K, 32 random bytes; nonce, 16 random bytes.
- **Encryption:** keystream `SHAKE-256(K || nonce)` of the payload length, XORed with the plaintext.
- **MAC:** `HMAC-SHA256(SHA-256("mac" || K), header || nonce || ciphertext)`, where `header` is the compact, key-sorted JSON of the header without its `mac` field. Checked in constant time after a slot opens; tampering raises "pack failed authentication".
- **Key slots** (one per secret, LUKS-style): `d = PBKDF2-HMAC-SHA256(secret, salt, 100000 iterations, dklen=64)`; `wrapped = K XOR d[:32]`; `tag = HMAC-SHA256(d[32:], K)`. Opening tries each supplied secret against each slot and accepts the slot whose tag verifies.
- **File:** one line of JSON header (`version`, `exercise`, `level`, `nonce`, `slots[{salt, wrapped, tag}]`, `mac`, all binary values base64), a newline, then the base64 ciphertext. `master.check` uses level -1 and `scoring.pack` level -2.
- **`seal_json` / `unseal_json`:** nonce, 32-byte MAC and ciphertext concatenated, same keystream and MAC under a raw key (used for `keys.bin`).

## 6. Answer canonicalisation

`answers.py` turns what a human types into canonical strings, and enumerates every accepted canonical form so the build can create one slot each. `answers.candidates(question, text)` returns the list of canonical forms to try for a typed answer: one per number for the numeric kinds, one form for `keyword` and `choice`, and none for `free`. An answer is accepted if any candidate is an accepted form (`answers.matches`); a `crypto` gate tries every combination of the questions' candidates as slot secrets.

| Kind | Canonical form | Accepted forms enumerated |
|---|---|---|
| `keyword` | Greek letters and subscript digits mapped to Latin names (α to alpha, Ω to omega, ₀ to 0, and so on), NFKC, case-fold, then everything except letters and digits removed. "Omega_m" and "ωM" both become `omegam`. With an optional `contains` list, if the canonical form of any term (checked in list order) is a substring of the canonical answer, the answer canonicalises to that term: with `"contains": ["psi", "meson"]`, "The J/ψ(1S) meson" becomes `psi`. `accept` entries get the same treatment, so typed input and `accept` are always canonicalised identically. A term must keep at least one letter or digit, and `contains` is valid only on `keyword` questions. | Canonical form of each string in `accept` (canonicalised with the same `contains` rule), plus the canonical form of each `contains` term. |
| `choice` | A single-letter token at the start of the text, else the only stand-alone single-letter token, lower-cased ("i" is never an option): "B)", "c - I think the second" and "I think c" give `b`, `c` and `c`. Otherwise (none, or several different ones) it is a format error ("answer with one letter, e.g. a"). | Canonical form of each string in `accept`. |
| `numeric` | One candidate per number in the text, using the last 6 numbers found (results usually come last), de-duplicated, order kept. Each number is parsed as a float after removing commas and converting `×10^` or `x10^` to `e` and a Unicode minus to `-`; `%` straight after a number (optional space) divides by 100, and a `k`, `K` or `M` suffix (optional space, not followed by a letter) multiplies by 1e3 or 1e6 ("500k", "0.5M"; "500 kB" and "5 kpc" are not multipliers). Other units and suffixes are ignored ("70.1 km/s/Mpc"). Each number is rounded to `decimals` (default 2) and formatted fixed-point; negative zero becomes `0`. | Every value on the grid from `lo` to `hi` in steps of 10^-decimals, formatted the same way. The grid runs from `lo` rounded to `decimals` to `hi` rounded to `decimals`, so a `lo` that is not on the grid still enumerates its own rounded form and the top form. More than 100,000 grid points is an error. |
| `numeric-log` | As `numeric`, but log10 of each number (non-positive numbers are skipped), rounded to `decimals` (default 1). | Every log-grid value from log10(`lo`) to log10(`hi`), both rounded to `decimals`. A 4-decimal grid over a narrow range is a handful of slots (Speed Run pairs: six, accepting about 499,402 to 500,092). |
| `free` | None; the answer is logged, not graded. | None. |

An answer with no number for a numeric question ("answer with a number, e.g. 0.0093 or 1.2e-3"), or with no single option letter for a choice question, is a format error: it is logged as a `crypto-format` failed attempt and no unlock is tried. A failed unlock is logged as before, whatever the number of candidates. `answers.matches` does the local check (no crypto) used by the built-in `gate.answer` validator, and `answers.numbers(text)` gives the last 6 numbers for exercise validators.

## 7. State file

`.workshop/state.json` is not in git, so a fresh clone (for example from a bundle) has none. Any `gate` command, and `./preflight`, then creates the level-0 state as `gate reset` would and says so.

The file is written only by `gate` and the exercise tool, atomically: a temporary file in `.workshop/` is written with sorted keys and indented, then renamed over the target. Loading (after that first creation) fails with a clear message if the file is corrupt, lacks `exercise`, `level`, `levels` or `allowed_models`, or has a non-integer `level`.

| Field | Meaning |
|---|---|
| `exercise` | Manifest exercise name (checked on every command). |
| `level` | Current level, an integer. |
| `persona` | Current persona; updated on unlock from the new level's manifest entry. |
| `allowed_models` | Initially `models.allowed`; `allow-model` appends. Read by `model_lock.py` and `model_check.py`. |
| `levels["N"].started` | ISO-8601 UTC time the level began (drives hint time locks and `status`). |
| `levels["N"].unlocked` | Time the level was left, or null. |
| `levels["N"].hints_used` | List of hint tier indices shown (`hint`). |
| `levels["N"].failed_attempts` | Count of failed checks and gate answers. |
| `attempts` | List of `{ts, level, kind}`; `kind` is `check`, `verified`, `crypto-format`, a gate type or `master`. Answers are never stored. |
| `skips` | List of `{ts, level, reason}` from `skip --master`. |
| `records` | Free dictionary for the exercise tool (for example scores). |
| `complete` | True once the last level is passed or skipped. |

`LOG.md` in the repo root is a separate human-readable log: hints used, reflections, skips, power-ups, level unlocks and completion.

## 8. Hooks

Wired in `.claude/settings.json`: `SessionStart` runs `model_check.py`, `UserPromptSubmit` runs `teacher_context.py`, `PreToolUse` (matcher `Read|Edit|Write|MultiEdit|NotebookEdit|Bash|Monitor|Grep|Glob`) runs `guard.py`; `Monitor` is checked as Bash, since a `Bash` matcher does not fire for it; `PreModelSwitch` (matcher `.*`) runs `model_lock.py`. They are exec-form commands (`python3` with `${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.py`) with a 10 second timeout; `guard.py` and `model_lock.py` set `onFailure: "block"` so a crash or timeout blocks. The settings file also sets `permissions.defaultMode` to `plan` and a deny list for the vault, state, tool and `.claude` paths, human-only `gate` subcommands, the exercise's human-only subcommands and package managers. The build renders the exercise part: the template holds one placeholder element, `"__HUMAN_ONLY_DENY__"`, which `tools/build.py` replaces with `Bash(./<launcher> <sub> *)` entries from the manifest's `human_only` (the tdd default when absent) and fails if the placeholder is left over or the result is not valid JSON. All hooks use only the standard library and run on Python 3.9+. They find the repo through `CLAUDE_PROJECT_DIR`, falling back to the current directory. The hook and settings schemas were verified against the docs (see `docs/DECISIONS.md`).

Deny output is `{"hookSpecificOutput": {"hookEventName": ..., "permissionDecision": "deny", "permissionDecisionReason": ...}}` on stdout with exit 0. Allowing is exit 0 with no output.

| Hook | Reads | Behaviour |
|---|---|---|
| `guard.py` (PreToolUse) | `tool_name`, `tool_input` (`file_path`, `notebook_path`, `path`, `pattern`, `command`), `cwd`; `.workshop/state.json` (level); the level's `guard.json`; `.tdd/phase` | Denies malformed input, a non-string tool name, a non-object `tool_input`, and missing state. For path tools: denies secret paths for every tool; for edit tools also denies paths outside the repo (except Claude Code's own plan-mode files under `~/.claude/plans` or `$CLAUDE_CONFIG_DIR/plans`), frozen files and the level's frozen globs, and anything not matching `editable`. For Bash: see below. Any unexpected exception also denies. |
| `model_lock.py` (PreModelSwitch) | `to_model` (or `requested_model`); `allowed_models` from state | Splits the target and each allowed entry on non-alphanumerics (case-insensitive) and allows an exact match, or a target that shares a model-family token (`haiku`, `sonnet`, `opus`, `fable`, `best`, `default`, `opusplan`) with an allowed entry and names no other family. Denies on malformed input, missing state, no target, or no match, with "Today's exercise uses <model>. Ask a facilitator for a power-up." |
| `teacher_context.py` (UserPromptSubmit) | state `level` and `persona`, manifest level title, `.workshop/levels/N/persona.txt`, the tool's `teacher_context_extra` | Prints `WORKSHOP LEVEL n - <title> - persona: <mode>` followed by the persona text. If the first line of `persona.txt` starts `persona:` it overrides the mode and is dropped. Prints a short warning, rather than failing, if gatekit, state or the manifest are missing or the tool errors. Plain stdout becomes context. |
| `model_check.py` (SessionStart) | `model` (optional) | When `model` is present, always prints `WORKSHOP: this session started on <model>; /status shows the current model.` into context (it reports the starting model only, and goes stale after a `/model` power-up), and also prints a warning if it matches no allowed model; prints a "run ./gate reset" notice if state is missing. Never blocks. Best effort, since Claude Code does not always send `model`. |

### guard.json

Per-level path rules, read from `.workshop/levels/N/guard.json`. Globs are `fnmatch` patterns where `**` also crosses `/`, and `dir/**` matches anything below `dir`. Paths are taken relative to the repo, resolved through symlinks.

```json
{
  "editable": ["src/**", "tests/**", "LOG.md"],
  "frozen": ["tests/acceptance/**"],
  "message": "Shown when an edit is refused.",
  "phases": {
    "none":     {"editable": ["LOG.md"], "frozen": [], "message": "..."},
    "red":      {"editable": ["tests/**"], "frozen": ["src/**"], "message": "..."},
    "green":    {"editable": ["src/**"], "frozen": ["tests/**"], "message": "..."},
    "refactor": {"editable": ["src/**"], "frozen": ["tests/**"], "message": "..."}
  }
}
```

The phase is read from `.tdd/phase` (`none`, `red`, `green` or `refactor`; anything else, or no file, means `none`). When `phases` is present, the entry for the current phase (falling back to `none`) overrides the top-level `editable`, `frozen` and `message`. An edit is allowed only if the path matches `editable` and no frozen pattern. With no `editable` list nothing is editable. A missing `guard.json` therefore leaves nothing editable.

Always blocked, whatever the level (`hooklib.py`):

- `SECRET_DIRS` (no read, list or write): `.vault`, `.workshop`, `.tdd`, `.claude`, `.gatekit`, `.tdd-tools`, `.git`.
- `FROZEN_FILES` (readable, never editable; the manifest's `human_only` launchers are added at run time): `gate`, `tdd`, `race`, `preflight`, `AGENTS.md`, `CLAUDE.md`, `OTHER-AGENTS.md`, `README.md`, `BRIEF.md`, `CLIENT_SPEC.md`, `Makefile`, `pytest.ini`, `requirements.txt`, `.gitignore`, plus the `data/` directory.

### Bash matching is best effort

`guard.py` reads the command's quotes, heredocs and redirects (`hooklib.parse_shell`), then applies regexes. It denies a command that:

- mentions a secret directory as a path component (for example `cat .vault/level1.pack`, `ls .workshop`);
- runs `gate unlock|hint|skip|reset|allow-model` or one of the manifest's `human_only` exercise commands (default `tdd red|green|refactor|done|abort|score|new-attempt`), including the indirect `<launcher> $VAR` form; the guard reads `.gatekit/manifest.json` on each Bash call and denies when it cannot be read or `human_only` is malformed;
- invokes a package manager (`pip`, `python -m pip`, `uv`, `brew`, `npm`, `conda`, `pipx`, `poetry`, `easy_install`), or pipes code into a bare `sh`, `bash`, `zsh` or `python` (`| sh`, `| bash -e`, `| python3 -`; `| python3 -m json.tool`, `| python3 -c ...` and `||` are fine; the pipe is looked for only outside quotes and heredocs);
- uses pty tricks (`pty`, `openpty`, `script `, `expect`, `unbuffer`, `socat`, `faketty`);
- redirects (`>`, `>>`, `>|`, `&>`, `N>`) to a secret path, a build-frozen file or directory, or a path matching the level's `frozen` globs (a relative target is resolved against the hook's `cwd` and against every literal `cd` or `pushd` directory earlier in the command, so `out/README.md` is fine but `cd tests && cat > test_x.py` is not; a computed `cd`, such as `cd "$X"`, `cd -` or a bare `pushd`, makes a relative target refuse with its own message; an absolute target is checked as written; only a target with a `..` component is also matched by name); `>!` counts as a redirect. Only a real shell redirect counts: a `>` inside quotes or a quoted heredoc body is text. Mentions of frozen paths elsewhere in the command are reads;
- runs `git clean` with `-x` or `-X`, which would delete `.workshop/`, `.tdd/` and `.venv/`;
- contains another write verb (`tee`, `sed -i` in any option position, `cp`, `mv`, `rm`, `touch`, `chmod`, `ln`, `patch`, mutating `git` subcommands, `python script.py`, `node script.js`, `perl`, `ruby`) or interpreter code with a file-writing API (Python `open(..., 'w')`, `write_text`, `shutil.`, `os.remove` and friends; Node `writeFileSync`, `writeSync`, `openSync` with a writable flag, `rmSync`, `mkdir` and friends; `awk` `print`/`printf` redirected with `>`, `>>` or `|`, even over several lines; a `>` inside parentheses, as in `print ($1 > 0)`, is a comparison), and also mentions a frozen file, a frozen directory or the base of a frozen glob. `python -c`, `node -e` and interpreter heredocs with no write API are reads.

How the command is read, before those tests:

- A `git commit -m "$(cat <<'EOF' ... EOF)"` message is dropped (a quoted delimiter makes the body literal). Any other command substitution in a commit message keeps the whole command under inspection.
- A heredoc with a quoted delimiter (`<<'X'`, `<<"X"`, `<<\X`) has a literal body. If a shell (`sh`, `bash`, `zsh`, `eval`, `source`, `.`) reads it, the body is checked as a command in its own right. If `python`, `node`, `perl`, `ruby` or any other command reads it (wrappers such as `env`, `timeout 30`, `nice` and `stdbuf` are skipped), it is interpreter code. Only `cat`, `tee` and `git` make it data (for example `cat > out/x.js <<'EOF'`): it is ignored for write and frozen-path checks, but still searched for secret names. Unquoted heredocs expand, so they stay in the full analysis.
- Inside quotes or a quoted heredoc, regex-only spellings (a group such as `(.*?)`, an escaped dot `\.`, or `.*`/`.+` followed by a word or regex character) are not treated as dot-globs reaching `.vault`. Neither is a `.*` inside a word before a slash (`s/=.*//`), but one directly after a slash (`./.*/x`, `explorer/.*/foo`) is; a bare quoted `'.*'` or `'.v*'` or `'.*/x'` still is, and secret names are matched everywhere.
- Unbalanced quotes, an unterminated heredoc, a substitution inside double quotes or a computed redirect target or a shell run with `-c` (`sh -c`, `bash -lc`, also via `env` or a path), whose quoted script is hidden from the parser, make the guard fall back to the whole-text rules, where any `>` counts as a write.
- Every Bash and path-tool refusal ends with a shared sentence telling Claude not to reword or retry it to slip past the guard, but to tell the group and use a make target or the tests.

It cannot catch: paths built at run time (variables, including a redirect to `$VAR`, string concatenation, `base64`/`eval` tricks); a script that was written earlier and then run; commands that reach a protected path through a glob or `cd` without naming it; a symlink created elsewhere; write verbs missing from the list; alternative interpreters and shell wrappers other than `sh -c`, `bash -c` and the like; or phase edits through tools the regex does not know. Reading frozen (non-secret) files through Bash is allowed. The Bash rules are a speed bump and a teaching message, not a security boundary.

## 9. Exercise tool interface

An exercise tool is a package (named by `manifest.tool`) shipped in `.gatekit/`. It is imported by `gate` and by `teacher_context.py`, and every member is optional.

| Member | Signature | Used for |
|---|---|---|
| `conditions` | `{name: fn(root, state, manifest) -> (ok, reason)}` | `gate.condition = "tool.name"` for `verified` gates; `check` and `unlock` print the reason. |
| `validators` | `{name: fn(root, state, question, answer) -> (ok, reason)}` | `question.validator = "tool.name"`. May compare the answer with local results. The built-in `gate.answer` checks `accept` or the numeric range. |
| `post_unlock` | `{name: fn(root, state, manifest, new_level) -> message}` | `gate.post_unlock`; runs after the new level is installed and may change `state`, which is then saved; a returned message is printed. |
| `questions` | `{name: fn(root, state, question) -> {"prompt": str, "wrong_hint": str}}` | `question.text_from = "tool.name"`; both keys optional, a non-empty string replaces the static field. Any exception falls back to the static text. |
| `hints` | `{name: fn(root, state, tier) -> str}` | `tier.text_from = "tool.name"` in `hints.json`; a non-empty string replaces the tier's `text`. Any exception falls back to the static text. |
| `level_secret` | `fn(root, level) -> bytes` | Returns the secret for the pack that level `level + 1` needs (unseals `keys.bin`). Called only for `verified` gates that are not on the last level. |
| `status_lines` | `fn(root, state) -> [str]` | Extra lines for `gate status`. |
| `teacher_context_extra` | `fn(root, state) -> str` | Text appended to the `UserPromptSubmit` context. |
| `on_reset` | `fn(root)` | Called at the end of `gate reset` (and at build time) to clear exercise state such as `.tdd/`. |

A dotted name with prefix `gate` refers to a built-in; any other prefix is resolved against the tool's table and fails with a clear error if the tool or the entry is missing.

## 10. Self-tests

Run from the toolkit directory with the standard library only. They work on Python 3.9 and 3.14.

```
cd gatekit && python3 -m unittest discover -s . -t . -p 'test_*.py'
```

| Module (in `tests/`) | Covers |
|---|---|
| `test_crypto_packs.py` | Keystream round-trip, slot wrap and unwrap, verify token, deterministic tar, pack round-trip with the master slot, tamper detection via the MAC, `seal_json`, unsafe member paths. |
| `test_answers_state.py` | Keyword synonyms, Greek and `contains`, manifest `contains` and prompt-ending rules, choice, numeric grid and units, numeric-log, free, crypto slot enumeration; state round-trip, level advance and corrupt state. |
| `test_build.py` | Builds the fixture exercise: layout and determinism, rendered `human_only` deny rules and the tdd fallback, wrong then right answer through the real `gate`, master skip and model power-up, and that `preflight` runs. |
| `test_hooks.py` | `guard.py` against synthetic hook JSON (vault read, `gate unlock`, package managers and pty, secret paths, frozen edits, normal work, malformed input, missing state, phase rules); `model_lock.py` allow, deny and power-up; `teacher_context.py` persona per level; `model_check.py` (model line and warning); manifest-driven `human_only` denials and the fail-closed bad-manifest case. |
| `test_tty_cli.py` | Human-only commands refuse without a TTY; `hint` and `reset` succeed through a pty; question `text_from` and `wrong_hint` (static, tool-supplied, failing tool); hint tier `text_from`. |

`tests/fakerepo.py` builds a throwaway repo and `tests/fixture_exercise/` is the small exercise the build tests use.

`gatekit/ptyhelper.py` drives human-only commands through a pseudo-terminal. `PtySession(argv, cwd, env, timeout)` starts the process on `os.openpty()`; `expect(text)` waits for output, `send(line)` types a line, `answer(text, line)` does both, and `wait()` drains output and returns the exit code. `run_pty(argv, answers=[(prompt, reply), ...])` runs a whole scripted session and returns `(exit_code, transcript)`. A timeout raises `PtyTimeout` with the recent transcript. It is a test helper, not used by the gate itself.

## 11. Honest limits

This is a learning scaffold, not an exam proctor (docs/00 §5.6). A group that wants to cheat can, and the lecture should say so openly.

### Hard to bypass

- Crypto gates (Speed Run Levels 0–2 and Explorer Level 1; the Explorer's other gates are reflections with no graded answer, so their slot needs the check token T alone): a slot opens only with the check token T plus the human answer. The answer is a soft secret: it sits in plaintext in the fourth hint tier under `.workshop/levels/N/` once a level is open (Level 0 from the start) and, for the Explorer, in the tool source (`.gatekit/exploretool/__init__.py`), protected only by the guard. The shipped manifest carries no `accept`, `lo` or `hi` for crypto questions (the build strips them), but the hint files and tool source do. It does carry any `contains` terms, because the runtime canonicalisation needs them, so those terms are readable, like the tool source.
- **Fixed success lines.** The Explorer's checks (`exploretool/gates.py`, `success_line`) and the Speed Run's Level 0–2 checks (`racetool/gates.py`, `success_line`) print the fixed line `{"level": N, "ok": true}` on a pass, and T is the SHA-256 of that line. The line is in the tool source under `.gatekit/`, so the crypto gate stops casual reading of the packs, not a determined agent that can read `.gatekit/`. Under Claude Code the guard hides `.gatekit/`; elsewhere only the written rules do. For Explorer the packs hold nothing secret (briefs, personas, hints and file templates; no hidden assets), so that is acceptable. The Speed Run's only remaining secret is the human answer (six values, 23 values, or four letters), which a determined group could guess offline against the pack, and one typed answer can carry up to six numbers, so six guesses per attempt; the Speed Run is Claude Code only.
- The TDD Ladder and the Speed Run race (Level 3) use verified gates, which are soft barriers (below).
- Writes outside the repo or to frozen files, and `..`, absolute, `~` and `/tmp/../` paths through Read and Edit.
- A wrong master passphrase leaks nothing (PBKDF2, 100k iterations).

### Soft

- The teacher persona and the `AGENTS.md` rules are instructions the agent is asked to follow. The hooks (guard, persona, model lock) run only in Claude Code; on other harnesses the written rules are the fallback, by design.
- Verified gates (all of tdd-ladder, and the Speed Run race at Level 3): the encrypted packs and the TTY requirement hold only because `AGENTS.md`, the persona and the guard tell Claude not to cheat, and because a group would have to ask it to. See the structural limit below.
- Path and command guards on Bash are regexes (section 8). They were tightened after the review but are still regex-based, so shell indirection always beats them.

### Bypassable by a determined human

- Launching with `claude --model opus`: a launch flag is not a mid-session switch, so `PreModelSwitch` never sees it, and `SessionStart` carries `model` only optionally, so `model_check.py` may not warn.
- Asking Claude to reverse-engineer a gate.
- Reading `keys.bin` and the pepper from the repo, or the vault with the master passphrase.
- Guessing a small crypto answer space offline.
- Editing `.workshop/state.json` or the hooks directly. Editing `state.json` can jump levels but yields no content.

Hooks may not run until the folder is trusted in the first interactive launch; the facilitator checklist covers accepting trust, and `preflight` cannot detect it.

### Adversarial review findings

An adversarial review attacked a fresh `dist/tdd-ladder` as a Claude session whose tool calls pass through `guard.py`.

**Structural limit (no cheap fix).** Claude may edit `tests/**` and may run `./tdd test`, pytest or `python3 tests/x.py`. Any Python file under `tests/` runs at import time with the repo's own permissions. It can read `.gatekit/tddtool/_pepper.py` and `.vault/keys.bin`, unseal every level secret and decrypt every pack (`CLIENT_SPEC.md`, the reference, the mutants). It can also call `os.openpty` to drive `./gate` and `./tdd` as if a human typed. So for verified gates neither the encrypted packs nor the TTY requirement is hard against a code-running Claude; both are soft barriers. The master passphrase is not needed to open tdd-ladder packs offline: `keys.bin` plus the pepper suffice. Crypto gates need T plus the answer, but T comes from a fixed success line in the tool source (see the bullet above) and the answer is guard-protected plaintext in the hint files and the Explorer's tool source, so they too hold only while the agent is kept out of `.gatekit/`.

**Second limit.** The vault and the pepper are committed to git, because they must travel with the clone. Git object readers (`git show`, `git cat-file`, `git archive`, `git log -p`, `git grep`) can therefore print them. The guard blocks the common spellings, but `$VAR`, `printf`, `base64 | sh`, `eval` or string concatenation in Python always beats a regex.

**Fixed after the review (closed by the guard, still regex-based):**

- Path checks are case-insensitive. APFS is case-insensitive, so `.VAULT/keys.bin` was readable and `.CLAUDE/hooks/guard.py` was writable.
- The secret-path regex matches after stripping quotes and backslashes, and inside `ref:path` forms.
- Git object readers are blocked: show, cat-file, archive, bundle, fast-export, grep, ls-tree, rev-list, format-patch, diff-tree, `log -p/--patch`, and `config core.hooksPath`.
- Human-only `gate` commands and the manifest's `human_only` commands (`tdd` by default) are matched after quote stripping and with variables.
- Package-manager variants are blocked: `-mpip`, ensurepip, uvx, `| sh`, `| python3`.
- Dot-glob and brace patterns that could expand to a dotdir are blocked; Grep `glob` and Glob dot-patterns are checked; Grep's regex `pattern` is tested only for secret names, so `def .*json` is fine.
- `gatekit/ptyhelper.py` is no longer shipped in `dist/`.
- `require_tty()` also refuses when the `CLAUDECODE` environment variable is present (Claude Code's Bash tool sets it), and the guard blocks `env -i`, `env -u` and `unset CLAUDECODE`.
- `model_lock` matches whole tokens and denies on non-object input.
- `__pycache__` is excluded from packs.
- Deny rules were added for `Read(./.git/**)` and `Edit(**/.claude/**)`.

**Not exploitable:** `..`, absolute, `~` and `/tmp/../` paths through Read and Edit; writes outside the repo or to frozen files; `cat -- .vault`, `ln -s .vault`, `cd .vault`, `script … ./gate`; a wrong master passphrase; git history beyond the start tree.

**Open (unverified against the Claude Code docs):**

- Whether permission deny-rule paths are case-sensitive.
- Whether Grep searches hidden directories, and whether Read-deny filtering applies to its results.
