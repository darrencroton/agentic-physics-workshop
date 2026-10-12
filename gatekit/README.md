# gatekit

## 1. What it is

gatekit is a stdlib-only toolkit that turns an exercise into a ladder of levels, each unlocked by a human at a terminal. A level's files sit in an encrypted pack until the group passes the level's check and answers its gate question(s); hooks keep Claude Code inside the current level's rules. It is a learning scaffold, not an exam proctor (see "Honest limits").

`tools/build.py <exercise> --master-passphrase-file <path>` assembles `dist/<exercise>/` from `gatekit/` and `exercises/<exercise>/`. The output is wiped and recreated, then committed as "Workshop start" and tagged `start`.

```
dist/<exercise>/
  gate                     # launcher: python3, adds .gatekit/ to sys.path, calls gatekit.cli.main
  preflight                # machine readiness check; --setup builds .venv (rendered with __SETUP_PYTHON__)
  CLAUDE.md                # participant rules, from workshop/CLAUDE.workshop.md
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

## 2. The `gate` commands

All commands run as `./gate <command>`. A TTY means both stdin and stdout are terminals; otherwise the command prints "This command is for humans, in the gate terminal." and exits 3. Other errors exit 1, usage errors exit 2, Ctrl-C exits 130.

| Command | TTY required | Behaviour |
|---|---|---|
| `status` | No | Prints title, level and title (marks "complete"), persona, minutes on level against `target_minutes`, hints used of total, failed gate attempts, allowed models, then any `status_lines` from the exercise tool. |
| `brief` | No | Prints `.workshop/levels/N/BRIEF.md`; at level 0 with no such file, prints `README.md`. |
| `check` | No | Runs the level's check and prints `PASS: <reason>` or `FAIL: <reason>`; exit 0 or 1. Never prints the expected answer. |
| `unlock` | Yes | Runs the check (failure is logged as a failed attempt and stops). Asks each gate question, unlocks the next level by installing its pack, runs `post_unlock`, then prints the `pre_reflection_note` and asks the reflection question(s), appending the answers to `LOG.md`. On the last level it sets `complete` instead of unpacking. A wrong answer prints "Not quite. Discuss and try again." and logs the failure (timestamp and kind only, never the answer). |
| `hint` | Yes | Shows the first unused tier in `hints.json`, provided `unlock_after_minutes` has passed on this level; otherwise says when it unlocks. Records the tier in `hints_used` and appends the text to `LOG.md`. |
| `skip --master` | Yes | Prompts for the master passphrase without echo, checks it against `.vault/master.check`, asks for a reason, records a skip, and unlocks the next level using the master slot (or marks the last level complete). Logs to `LOG.md`. A wrong passphrase is logged as a failed attempt of kind `master`. Without `--master` it errors. |
| `allow-model <name>` | Yes, plus master passphrase | Verifies the master passphrase, lower-cases the name, appends it to `allowed_models` and logs the power-up. |
| `reset` | Yes | Asks for confirmation (skipped with `--yes`), deletes `.workshop/`, copies `.gatekit/levels/0` to `.workshop/levels/0`, writes a fresh state and calls the tool's `on_reset(root)`. It does not touch the working tree; the message suggests `git reset --hard start`. |

`gate help`, `-h` and `--help` print usage.

## 3. Manifest schema

The manifest lives at `exercises/<name>/manifest.json` and is copied to `.gatekit/manifest.json`. `manifest.py` requires `exercise`, `title` and a non-empty `levels` list whose ids run 0..n in order; personas must be `literal`, `coach` or `collaborator`; gate types must be one of the four below; each question needs `id` and `prompt`. Keys marked "build" are written or read by `tools/build.py`. JSON has no comments, so the annotations below are illustrative only.

```jsonc
{
  "exercise": "tdd-ladder",              // must match state.json; a mismatch tells you to reset
  "title": "The TDD Ladder",
  "tool": "tddtool",                     // optional: package under .gatekit/ (conditions, validators, hooks into status etc.)
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
            "validator": "tdd.equals_last_acceptance_count"   // verified: default "gate.answer"
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

The build needs an entry for every `crypto` and `crypto-reflection` gate, and fails otherwise.

## 4. Gate types

T is the SHA-256 digest of the check script's canonical stdout. `verify = SHA-256("verify" || T)` is stored in the manifest, so `gate check` can print PASS or FAIL without holding any answer. The pack that a gate unlocks gets one slot per accepted secret plus a master slot.

| Type | Key material for the next level's pack | Notes |
|---|---|---|
| `crypto` | One slot per accepted answer, secret `T || 0x00 || canon(A)`. With several questions the canonical answers are joined with `\|` and the slots cover every combination of accepted forms (`free` questions contribute nothing). Plus the master slot. | The check must exit 0 and print output whose hash gives the `verify` value. Questions are graded by whether the pack opens. |
| `crypto-reflection` | As `crypto`: secret derived from T and the (usually empty) canonical answer. | Unlock behaves as `crypto`. Use `free` questions and a `reflection` so answers are logged, not graded. |
| `verified` | A per-level random 32-byte secret (hex from `secrets.token_hex(32)`) generated at build time, stored in `.vault/keys.bin` and released by the exercise tool's `level_secret(root, level)` after its `condition` and `validator`s pass. Plus the master slot. | Needed for group-specific outcomes (for example a score the group just recorded). |
| `none` | Empty secret `b""` plus the master slot. | Unlock needs no check or answer; `run_check` reports "No check at this level." |

Every pack has a master slot (secret: the stripped passphrase bytes). `.vault/master.check` is a pack of the single word `master` openable only by that slot, which is how `skip --master` and `allow-model` verify the passphrase.

`keys.bin` and the optional scoring pack secret (`scoring`) are sealed with a key from `SHA-256(exercise || 0 || pepper || 0)`, where the pepper is a random value written to `.gatekit/<tool>/_pepper.py` at build time. The key is therefore recoverable by anyone who can read the tool source.

Limits, stated plainly:

- `verified` gates are a soft barrier. They are obfuscation: the secrets are in `keys.bin`, sealed with a key derived from a pepper in the tool source. The guard, deny rules and persona stop Claude from reading them; a human with shell access can.
- `crypto` gates are only as strong as the answer space. A small multiple-choice space (or a narrow numeric grid) is guessable offline by trying every slot secret against the pack.
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

`answers.py` turns what a human types into a canonical string, and enumerates every accepted canonical form so the build can create one slot each.

| Kind | Canonical form | Accepted forms enumerated |
|---|---|---|
| `keyword` | Greek letters and subscript digits mapped to Latin names (α to alpha, Ω to omega, ₀ to 0, and so on), NFKC, case-fold, then everything except letters and digits removed. "Omega_m" and "ωM" both become `omegam`. | Canonical form of each string in `accept`. |
| `choice` | The single letter in the text, lower-cased ("B)" gives `b`). Zero or several letters is a format error ("answer with one letter, e.g. a"). | Canonical form of each string in `accept`. |
| `numeric` | First number in the text, parsed as a float after removing commas and converting `×10^` or `x10^` to `e` and a Unicode minus to `-`. Units and other suffixes are ignored ("70.1 km/s/Mpc"). Rounded to `decimals` (default 2) and formatted fixed-point; negative zero becomes `0`. | Every value on the grid from `lo` to `hi` in steps of 10^-decimals, formatted the same way. More than 100,000 grid points is an error. |
| `numeric-log` | As `numeric`, but log10 of the parsed value (which must be positive), rounded to `decimals` (default 1). | Every log-grid value from log10(`lo`) to log10(`hi`). |
| `free` | None; the answer is logged, not graded. | None. |

An answer that cannot be parsed ("answer with a number, e.g. 0.0093 or 1.2e-3") is a format error: it is logged as a `crypto-format` failed attempt and no unlock is tried. `answers.matches` does the local check (no crypto) used by the built-in `gate.answer` validator.

## 7. State file

`.workshop/state.json` is written only by `gate` and the exercise tool, atomically: a temporary file in `.workshop/` is written with sorted keys and indented, then renamed over the target. Loading fails with a clear message if the file is missing, corrupt, lacks `exercise`, `level`, `levels` or `allowed_models`, or has a non-integer `level`.

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

Wired in `.claude/settings.json`: `SessionStart` runs `model_check.py`, `UserPromptSubmit` runs `teacher_context.py`, `PreToolUse` (matcher `Read|Edit|Write|MultiEdit|NotebookEdit|Bash|Grep|Glob`) runs `guard.py`, `PreModelSwitch` (matcher `.*`) runs `model_lock.py`. They are exec-form commands (`python3` with `${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.py`) with a 10 second timeout; `guard.py` and `model_lock.py` set `onFailure: "block"` so a crash or timeout blocks. The settings file also sets `permissions.defaultMode` to `plan` and a deny list for the vault, state, tool and `.claude` paths, human-only `gate` and `tdd` subcommands and package managers. All hooks use only the standard library and run on Python 3.9+. They find the repo through `CLAUDE_PROJECT_DIR`, falling back to the current directory. The hook and settings schemas were verified against the docs (see `docs/DECISIONS.md`).

Deny output is `{"hookSpecificOutput": {"hookEventName": ..., "permissionDecision": "deny", "permissionDecisionReason": ...}}` on stdout with exit 0. Allowing is exit 0 with no output.

| Hook | Reads | Behaviour |
|---|---|---|
| `guard.py` (PreToolUse) | `tool_name`, `tool_input` (`file_path`, `notebook_path`, `path`, `pattern`, `command`); `.workshop/state.json` (level); the level's `guard.json`; `.tdd/phase` | Denies malformed input, a non-string tool name, a non-object `tool_input`, and missing state. For path tools: denies secret paths for every tool; for edit tools also denies paths outside the repo, frozen files and the level's frozen globs, and anything not matching `editable`. For Bash: see below. Any unexpected exception also denies. |
| `model_lock.py` (PreModelSwitch) | `to_model` (or `requested_model`); `allowed_models` from state | Allows if any allowed alias is a substring of the target (case-insensitive). Denies on malformed input, missing state, no target, or no match, with "Today's exercise uses <model>. Ask a facilitator for a power-up." |
| `teacher_context.py` (UserPromptSubmit) | state `level` and `persona`, manifest level title, `.workshop/levels/N/persona.txt`, the tool's `teacher_context_extra` | Prints `WORKSHOP LEVEL n - <title> - persona: <mode>` followed by the persona text. If the first line of `persona.txt` starts `persona:` it overrides the mode and is dropped. Prints a short warning, rather than failing, if gatekit, state or the manifest are missing or the tool errors. Plain stdout becomes context. |
| `model_check.py` (SessionStart) | `model` (optional) | Prints a warning into context if `model` is present and matches no allowed model; prints a "run ./gate reset" notice if state is missing. Never blocks. Best effort, since Claude Code does not always send `model`. |

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
- `FROZEN_FILES` (readable, never editable): `gate`, `tdd`, `preflight`, `CLAUDE.md`, `README.md`, `BRIEF.md`, `CLIENT_SPEC.md`, `Makefile`, `pytest.ini`, `requirements.txt`, `.gitignore`, plus the `data/` directory.

### Bash matching is best effort

`guard.py` applies regexes to the command text. It denies a command that:

- mentions a secret directory as a path component (for example `cat .vault/level1.pack`, `ls .workshop`);
- runs `gate unlock|hint|skip|reset|allow-model` or `tdd red|green|refactor|done|score|new-attempt`;
- invokes a package manager (`pip`, `python -m pip`, `uv`, `brew`, `npm`, `conda`, `pipx`, `poetry`, `easy_install`);
- uses pty tricks (`pty`, `openpty`, `script `, `expect`, `unbuffer`, `socat`, `faketty`);
- contains a write verb (redirection, `tee`, `sed -i`, `cp`, `mv`, `rm`, `touch`, `mkdir`, `chmod`, `ln`, `patch`, mutating `git` subcommands, or `python`, `perl`, `ruby`, `node`) and also mentions a frozen file, a frozen directory or the base of a frozen glob.

It cannot catch: paths built at run time (variables, string concatenation, `base64`/`eval` tricks); a script that was written earlier and then run; commands that reach a protected path through a glob or `cd` without naming it; a symlink created elsewhere; write verbs missing from the list; shell wrappers and alternative interpreters; or phase edits through tools the regex does not know. Reading frozen (non-secret) files through Bash is allowed. The Bash rules are a speed bump and a teaching message, not a security boundary.

## 9. Exercise tool interface

An exercise tool is a package (named by `manifest.tool`) shipped in `.gatekit/`. It is imported by `gate` and by `teacher_context.py`, and every member is optional.

| Member | Signature | Used for |
|---|---|---|
| `conditions` | `{name: fn(root, state, manifest) -> (ok, reason)}` | `gate.condition = "tool.name"` for `verified` gates; `check` and `unlock` print the reason. |
| `validators` | `{name: fn(root, state, question, answer) -> (ok, reason)}` | `question.validator = "tool.name"`. May compare the answer with local results. The built-in `gate.answer` checks `accept` or the numeric range. |
| `post_unlock` | `{name: fn(root, state, manifest, new_level) -> message}` | `gate.post_unlock`; runs after the new level is installed and may change `state`, which is then saved; a returned message is printed. |
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
| `test_answers_state.py` | Keyword synonyms and Greek, choice, numeric grid and units, numeric-log, free, crypto slot enumeration; state round-trip, level advance and corrupt state. |
| `test_build.py` | Builds the fixture exercise: layout and determinism, wrong then right answer through the real `gate`, master skip and model power-up, and that `preflight` runs. |
| `test_hooks.py` | `guard.py` against synthetic hook JSON (vault read, `gate unlock`, package managers and pty, secret paths, frozen edits, normal work, malformed input, missing state, phase rules); `model_lock.py` allow, deny and power-up; `teacher_context.py` persona per level; `model_check.py`. |
| `test_tty_cli.py` | Human-only commands refuse without a TTY; `hint` and `reset` succeed through a pty. |

`tests/fakerepo.py` builds a throwaway repo and `tests/fixture_exercise/` is the small exercise the build tests use.

`gatekit/ptyhelper.py` drives human-only commands through a pseudo-terminal. `PtySession(argv, cwd, env, timeout)` starts the process on `os.openpty()`; `expect(text)` waits for output, `send(line)` types a line, `answer(text, line)` does both, and `wait()` drains output and returns the exit code. `run_pty(argv, answers=[(prompt, reply), ...])` runs a whole scripted session and returns `(exit_code, transcript)`. A timeout raises `PtyTimeout` with the recent transcript. It is a test helper, not used by the gate itself.

## 11. Honest limits

This is a learning scaffold, not an exam proctor. A group that wants to cheat can, and the lecture should say so openly.

### Hard to bypass

- Encrypted packs: no later-level content is readable without the secret, which means T plus the correct answer (crypto), the level secret (verified) or the master passphrase.
- The TTY requirement: Claude cannot type into the gate terminal through its normal tools.

### Soft

- The teacher persona and `CLAUDE.md` rules are instructions Claude is asked to follow.
- Path guards on Bash are best-effort regexes (section 8), which is why the vault is encrypted rather than merely hidden.
- `verified` gates rely on obfuscation (section 4).

### Bypassable by a determined human

- Launching with `claude --model opus`: a launch flag is not a mid-session switch, so `PreModelSwitch` never sees it, and `SessionStart` carries `model` only optionally, so `model_check.py` may not warn.
- Asking Claude to reverse-engineer a gate.
- Reading the vault with the master passphrase, or reading `keys.bin` and the pepper from the tool source.
- Guessing a small crypto answer space offline.
- Editing `.workshop/state.json` or the hooks directly; they are protected from Claude, not from the person at the keyboard.

Further limits to be aware of:

- Claude could itself use a pty (`pty`, `script`, `expect`) to type into `./gate`, despite the guard regex and the `CLAUDE.md` rule against it. The regex only catches obvious spellings.
- Bash deny rules in `settings.json` and the guard regex are not a security boundary: indirection, wrappers and scripts can avoid them.
- Hooks may not run until the folder is trusted in the first interactive launch; the facilitator checklist covers accepting trust, and `preflight` cannot detect it.

### Adversarial review findings

(to be filled after the review)
