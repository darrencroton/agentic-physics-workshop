"""Drive human-only commands through a pseudo-terminal in self-tests."""

import os
import select
import subprocess
import time


class PtyTimeout(Exception):
    """Raised when an expected prompt does not appear in time."""


class PtySession:
    """Run a command with a pty and answer prompts as they appear."""

    def __init__(self, argv, cwd=None, env=None, timeout=60.0):
        env = dict(os.environ if env is None else env)
        for key in [k for k in env if k.startswith("CLAUDE")]:
            del env[key]
        self.master, slave = os.openpty()
        self.proc = subprocess.Popen(
            argv, cwd=cwd, env=env, stdin=slave, stdout=slave, stderr=slave,
            close_fds=True, start_new_session=True)
        os.close(slave)
        self.timeout = timeout
        self.transcript = ""
        self._buffer = ""

    def _read_some(self, wait):
        ready, _, _ = select.select([self.master], [], [], wait)
        if not ready:
            return False
        try:
            chunk = os.read(self.master, 4096)
        except OSError:
            return False
        if not chunk:
            return False
        text = chunk.decode("utf-8", "replace")
        self._buffer += text
        self.transcript += text
        return True

    def expect(self, needle, timeout=None):
        """Wait until `needle` appears in unread output; return text up to it."""
        deadline = time.time() + (timeout or self.timeout)
        while True:
            index = self._buffer.find(needle)
            if index >= 0:
                seen = self._buffer[:index + len(needle)]
                self._buffer = self._buffer[index + len(needle):]
                return seen
            remaining = deadline - time.time()
            if remaining <= 0:
                raise PtyTimeout("waited for %r; got:\n%s"
                                 % (needle, self.transcript[-2000:]))
            if not self._read_some(min(remaining, 0.25)):
                if self.proc.poll() is not None and not self._read_some(0.1):
                    raise PtyTimeout("process exited before %r; got:\n%s"
                                     % (needle, self.transcript[-2000:]))

    def send(self, line):
        """Type a line (with newline)."""
        os.write(self.master, (line + "\n").encode("utf-8"))

    def answer(self, needle, line, timeout=None):
        """expect() then send()."""
        self.expect(needle, timeout)
        self.send(line)

    def wait(self, timeout=None):
        """Drain output until the process exits; return its exit code."""
        deadline = time.time() + (timeout or self.timeout)
        while self.proc.poll() is None:
            if time.time() > deadline:
                self.proc.kill()
                raise PtyTimeout("process did not exit:\n%s"
                                 % self.transcript[-2000:])
            self._read_some(0.1)
        while self._read_some(0.05):
            pass
        os.close(self.master)
        return self.proc.returncode


def run_pty(argv, answers=(), cwd=None, env=None, timeout=60.0):
    """Run argv under a pty, answering (prompt, reply) pairs in order."""
    session = PtySession(argv, cwd=cwd, env=env, timeout=timeout)
    for needle, reply in answers:
        session.answer(needle, reply)
    code = session.wait()
    return code, session.transcript
