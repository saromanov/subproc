import errno
import locale
import os
import signal
import shlex
import subprocess
import sys

from pexpect.popen_spawn import PopenSpawn

TIMEOUT = 30

class Command(object):
    def __init__(self, cmd, timeout=TIMEOUT):
        super(Command, self).__init__()
        self.cmd = cmd
        self.timeout = timeout
        self.subprocess = None
        self.blocking = None
        self.was_run = False
        self.__out = None
        self.__err = None

    def __repr__(self):
        return "<Command {!r}>".format(self.cmd)

    @property
    def _default_pexpect_kwargs(self):
        encoding = "utf-8"
        if sys.platform == "win32":
            default_encoding = locale.getdefaultlocale()[1]
            if default_encoding is not None:
                encoding = default_encoding
        return {"env": os.environ.copy(), "encoding": encoding, "timeout": self.timeout}

    @property
    def _uses_subprocess(self):
        return isinstance(self.subprocess, subprocess.Popen)

    @property
    def _uses_pexpect(self):
        return isinstance(self.subprocess, PopenSpawn)

    @property
    def std_out(self):
        return self.subprocess.stdout

    @property
    def ok(self):
        return self.return_code == 0

    @property
    def _pexpect_out(self):
        if self.subprocess.encoding:
            result = ""
        else:
            result = b""

        if self.subprocess.before:
            result += self.subprocess.before

        if self.subprocess.after:
            result += self.subprocess.after

        result += self.subprocess.read()
        return result

    @property
    def pid(self):
        if hasattr(self.subprocess, "proc"):
            return self.subprocess.proc.pid
        return self.subprocess.pid

    @property
    def return_code(self):
        if self._uses_pexpect:
            return self.subprocess.exitstatus
        return self.subprocess.returncode

    @property
    def std_in(self):
        return self.subprocess.stdin

    def run(self, block=True, binary=False, cwd=None, env=None, args=[]):
        self.blocking = block
        self.subprocess = subprocess.Popen(args)
        self.was_run = True

    def pipe(self, command, timeout=None, cwd=None):
        if not timeout:
            timeout = self.timeout

        if not self.was_run:
            self.run(block=False, cwd=cwd)

        data = self.out

        if timeout:
            c = Command(command, timeout)
        else:
            c = Command(command)

        c.run(block=False, cwd=cwd)
        if data:
            c.send(data)
            c.subprocess.sendeof()
        c.block()
        return c