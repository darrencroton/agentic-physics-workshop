---
name: style-code
description: Coding guidelines for small scientific Python tools, covering structure, names, comments, errors and numbers. Use when asked to write or change code following the style-code skill, or run /style-code to audit changed files without editing them.
---

# Write code a colleague can read

Style exists so that someone else, or you in six months, can read the code, trust it and change it. The project's own conventions win: `CLAUDE.md`, a style guide, a formatter or linter configuration, and the surrounding code. Where the project has no convention, use these.

## Two ways to use it

- **While writing:** name the skill in the request ("following the style-code skill") and apply the guidelines as the code is written.
- **As an audit:** `/style-code [paths]` checks the named files, or the files changed since the last commit, and reports. It changes nothing.

## Guidelines

Structure

- Small functions that do one thing and are named for it. If the name needs an "and", split the function.
- Argument parsing and the top-level flow live in `main()`. The work lives in functions that take and return plain values, so they can be tested without the command line.
- No clever construct where a boring one reads better. Clarity beats brevity.
- No dead code, commented-out code or unused imports.

Names

- `snake_case` for functions, variables and files; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- A name carries its unit or convention when that matters: `distance_kpc`, `angle_deg`, `log_mass`.

Comments and docstrings

- A comment says what the code cannot: a unit, a sign convention, a sentinel value, why a surprising choice was made. It never restates the code.
- A docstring goes on any public function whose behaviour or failure modes are not obvious from its signature: what it takes, what it returns, what it raises.
- No TODO without saying what would resolve it.

Errors

- Validate at the boundary: files, command-line arguments, external data. Inside, trust your own values.
- An error message names the thing: the file, the column, the value. "Invalid input" is not a message.
- Never `except:` or `except Exception: pass`. Catch what you expect and let the rest fail loudly.
- A command-line tool exits non-zero with a one-line message, not a traceback.

Data and numbers

- Use `pathlib.Path` for paths.
- A missing value is explicit (`None` or `NaN`), never a magic number.
- Keep a quantity in one unit end to end. Convert once, at the edge, and say so in the name.

## Audit report

For each finding: `file:line`, the guideline, why it matters and a one-phrase fix. Skip anything with no effect on a reader. If a formatter or linter is configured, run it in its check-only mode (one that rewrites nothing) and cite its output rather than repeating it.
