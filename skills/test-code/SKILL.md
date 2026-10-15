---
name: test-code
description: Write tests that are evidence. Agree a test plan before writing tests, test behaviour through the public interface, and show that a test can fail. Use when asked for a test plan, tests, coverage, or the test-code skill.
---

# Test what must not break

Tests are the evidence that the code does what was agreed, and the alarm that rings when a later change breaks it. A test plan comes before the tests, so the human can see what will and will not be covered while it is cheap to change. A test that has never failed has not yet shown that it can.

## Steps

1. **Start from what the code must do.** Read the plan or acceptance criteria if there are any, the interface the code exposes, and the existing tests. Ask the human which behaviours matter most if that is not clear from the plan.
2. **Propose a test plan.** One line per test: its name, what it checks and the input it uses. Then say what the set covers and what the tests here cannot exercise (a page in a browser, special hardware, a remote service), because that still needs a human or another environment. Write it where the project keeps such things if asked. Agree it before writing anything.
3. **Write the agreed tests**, and no more. Run them and show the command and its full output.
4. **See a test fail.** For a bug fix, write the test before the fix and show it failing. For new tests on working code, offer to prove one can fail: make one small deliberate break in the code, run the tests, show the failure, and undo that one edit by hand, never with a command that reverts the whole tree. A test that cannot fail is not a test.
5. **Report** what passed and what is not covered, and offer to commit the tests together with the code they test.

## Writing a good test

- One behaviour per test, named for it: `test_missing_file_gives_error_and_exit_1`, not `test_main`.
- Test through the public interface (the command line, the function the user calls), not private helpers.
- Small inputs with expected values a person can check by hand or from a trusted source. Say where each expected number comes from.
- Floats are compared with a tolerance you can justify (`pytest.approx`, `numpy.testing.assert_allclose`), never with `==`. Random inputs use a fixed seed.
- Cover the edges the plan decided: empty input, missing values, zero, a malformed file. At least one test checks a failure path: the right error, the right exit code, no traceback.
- Each test stands alone: its own inputs (a temporary directory, a tiny made-up file), no dependence on order, no shared mutable state.
- Fewer good tests beat many weak ones.

## Rules

- Never change a test, an expected value or a tolerance to make a failing test pass. Say which is wrong, the code or the test, and why, and stop.
- Never skip a test or mark it expected-to-fail without saying why in the test.
- Never claim tests pass without showing the run. "All green" with no output is not evidence.
- Tests the plan did not agree are proposed, not written.
- Coverage shows what no test runs. It does not show that the tests check anything. Use it to find gaps, not as a score.
