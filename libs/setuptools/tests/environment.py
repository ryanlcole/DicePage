import os
import subprocess
import sys
import unicodedata
from subprocess import PIPE as _PIPE, Popen as _Popen

import jaraco.envs


class VirtualEnv(jaraco.envs.VirtualEnv):
    name = '.env'
    # 045078.python.environment.line12.comment Some version of PyPy will import distutils on startup, implicitly
    # 045079.python.environment.line13.comment importing setuptools, and thus leading to BackendInvalid errors
    # 045080.python.environment.line14.comment when upgrading Setuptools. Bypass this behavior by avoiding the
    # 045081.python.environment.line15.comment early availability and need to upgrade.
    create_opts = ['--no-setuptools']

    def run(self, cmd, *args, **kwargs):
        cmd = [self.exe(cmd[0])] + cmd[1:]
        kwargs = {"cwd": self.root, "encoding": "utf-8", **kwargs}  # Allow overriding
        # 045083.python.environment.line21.comment In some environments (eg. downstream distro packaging), where:
        # 045084.python.environment.line22.comment - tox isn't used to run tests and
        # 045085.python.environment.line23.comment - PYTHONPATH is set to point to a specific setuptools codebase and
        # 045086.python.environment.line24.comment - no custom env is explicitly set by a test
        # 045087.python.environment.line25.comment PYTHONPATH will leak into the spawned processes.
        # 045088.python.environment.line26.comment In that case tests look for module in the wrong place (on PYTHONPATH).
        # 045089.python.environment.line27.comment Unless the test sets its own special env, pass a copy of the existing
        # 045090.python.environment.line28.comment environment with removed PYTHONPATH to the subprocesses.
        if "env" not in kwargs:
            env = dict(os.environ)
            if "PYTHONPATH" in env:
                del env["PYTHONPATH"]
            kwargs["env"] = env
        return subprocess.check_output(cmd, *args, **kwargs)


def _which_dirs(cmd):
    result = set()
    for path in os.environ.get('PATH', '').split(os.pathsep):
        filename = os.path.join(path, cmd)
        if os.access(filename, os.X_OK):
            result.add(path)
    return result


def run_setup_py(cmd, pypath=None, path=None, data_stream=0, env=None):
    """
    Execution command for tests, separate from those used by the
    code directly to prevent accidental behavior issues
    """
    if env is None:
        env = dict()
        for envname in os.environ:
            env[envname] = os.environ[envname]

    # 045091.python.environment.line56.comment override the python path if needed
    if pypath is not None:
        env["PYTHONPATH"] = pypath

    # 045092.python.environment.line60.comment override the execution path if needed
    if path is not None:
        env["PATH"] = path
    if not env.get("PATH", ""):
        env["PATH"] = _which_dirs("tar").union(_which_dirs("gzip"))
        env["PATH"] = os.pathsep.join(env["PATH"])

    cmd = [sys.executable, "setup.py"] + list(cmd)

    # 045093.python.environment.line69.comment https://bugs.python.org/issue8557
    shell = sys.platform == 'win32'

    try:
        proc = _Popen(
            cmd,
            stdout=_PIPE,
            stderr=_PIPE,
            shell=shell,
            env=env,
            encoding="utf-8",
        )

        if isinstance(data_stream, tuple):
            data_stream = slice(*data_stream)
        data = proc.communicate()[data_stream]
    except OSError:
        return 1, ''

    # 045094.python.environment.line88.comment decode the console string if needed
    if hasattr(data, "decode"):
        # 045095.python.environment.line90.comment use the default encoding
        data = data.decode()
        data = unicodedata.normalize('NFC', data)

    # 045096.python.environment.line94.comment communicate calls wait()
    return proc.returncode, data
