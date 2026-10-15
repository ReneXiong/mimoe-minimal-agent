"""A persistent Bash subprocess. Working directory is NOT a security sandbox."""

import os
from pathlib import Path
import re
import selectors
import shlex
import signal
import subprocess
import time
import uuid


class ShellError(Exception):
    pass


class Bash:
    def __init__(self, workspace, timeout=30, output_limit=16000):
        self.workspace = Path(workspace).resolve(strict=True)
        self.timeout = timeout
        self.output_limit = output_limit
        # Do not pass inference credentials or the parent's other secrets to tools.
        env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TMPDIR")
               if key in os.environ}
        self.process = subprocess.Popen(
            ["/bin/bash", "--noprofile", "--norc"], cwd=self.workspace,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, start_new_session=True,
        )

    def run(self, command):
        if self.process.poll() is not None:
            raise ShellError("The shell exited. Start a new agent session.")
        marker = "MIMOE_" + uuid.uuid4().hex
        # eval runs in this shell, so cd, variables and functions survive calls.
        script = f"eval {shlex.quote(command)}\nprintf '\\n{marker}:%s\\n' \"$?\"\n"
        try:
            self.process.stdin.write(script.encode())
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self.close()
            raise ShellError("The shell is no longer available.") from exc
        pattern = re.compile(rb"\n" + marker.encode() + rb":([0-9]+)\n")
        output = b""
        deadline = time.monotonic() + self.timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    self.close()
                    raise ShellError("Command timed out; shell process group terminated.")
                chunk = os.read(self.process.stdout.fileno(), 4096)
                if not chunk:
                    self.close()
                    raise ShellError("The shell exited before reporting command status.")
                output += chunk
                match = pattern.search(output)
                if (match.start() if match else len(output)) > self.output_limit:
                    self.close()
                    raise ShellError("Command exceeded output limit; shell process group terminated.")
                if match:
                    text = output[:match.start()].decode(errors="replace").rstrip()
                    return f"{text}\n[exit code {int(match[1])}]".lstrip("\n")

    def close(self):
        if getattr(self, "closed", False):
            return
        self.closed = True
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
