# 024429.python.psposix.line1.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 024430.python.psposix.line2.comment Use of this source code is governed by a BSD-style license that can be
# 024431.python.psposix.line3.comment found in the LICENSE file.

"""Routines common to all posix systems."""

import enum
import glob
import os
import signal
import time

from ._common import MACOS
from ._common import TimeoutExpired
from ._common import memoize
from ._common import sdiskusage
from ._common import usage_percent

if MACOS:
    from . import _psutil_osx


__all__ = ['pid_exists', 'wait_pid', 'disk_usage', 'get_terminal_map']


def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    if pid == 0:
        # 024432.python.psposix.line29.comment According to "man 2 kill" PID 0 has a special meaning:
        # 024433.python.psposix.line30.comment it refers to <<every process in the process group of the
        # 024434.python.psposix.line31.comment calling process>> so we don't want to go any further.
        # 024435.python.psposix.line32.comment If we get here it means this UNIX platform *does* have
        # 024436.python.psposix.line33.comment a process with id 0.
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # 024437.python.psposix.line40.comment EPERM clearly means there's a process to deny access to
        return True
    # 024438.python.psposix.line42.comment According to "man 2 kill" possible error values are
    # 024439.python.psposix.line43.comment (EINVAL, EPERM, ESRCH)
    else:
        return True


Negsignal = enum.IntEnum(
    'Negsignal', {x.name: -x.value for x in signal.Signals}
)


def negsig_to_enum(num):
    """Convert a negative signal value to an enum."""
    try:
        return Negsignal(num)
    except ValueError:
        return num


def wait_pid(
    pid,
    timeout=None,
    proc_name=None,
    _waitpid=os.waitpid,
    _timer=getattr(time, 'monotonic', time.time),  # noqa: B008
    _min=min,
    _sleep=time.sleep,
    _pid_exists=pid_exists,
):
    """Wait for a process PID to terminate.

    If the process terminated normally by calling exit(3) or _exit(2),
    or by returning from main(), the return value is the positive integer
    passed to *exit().

    If it was terminated by a signal it returns the negated value of the
    signal which caused the termination (e.g. -SIGTERM).

    If PID is not a children of os.getpid() (current process) just
    wait until the process disappears and return None.

    If PID does not exist at all return None immediately.

    If *timeout* != None and process is still alive raise TimeoutExpired.
    timeout=0 is also possible (either return immediately or raise).
    """
    if pid <= 0:
        # 024441.python.psposix.line89.comment see "man waitpid"
        msg = "can't wait for PID 0"
        raise ValueError(msg)
    interval = 0.0001
    flags = 0
    if timeout is not None:
        flags |= os.WNOHANG
        stop_at = _timer() + timeout

    def sleep(interval):
        # 024442.python.psposix.line99.comment Sleep for some time and return a new increased interval.
        if timeout is not None:
            if _timer() >= stop_at:
                raise TimeoutExpired(timeout, pid=pid, name=proc_name)
        _sleep(interval)
        return _min(interval * 2, 0.04)

    # 024443.python.psposix.line106.comment See: https://linux.die.net/man/2/waitpid
    while True:
        try:
            retpid, status = os.waitpid(pid, flags)
        except InterruptedError:
            interval = sleep(interval)
        except ChildProcessError:
            # 024444.python.psposix.line113.comment This has two meanings:
            # 024445.python.psposix.line114.comment - PID is not a child of os.getpid() in which case
            # 024446.python.psposix.line115.comment we keep polling until it's gone
            # 024447.python.psposix.line116.comment - PID never existed in the first place
            # 024448.python.psposix.line117.comment In both cases we'll eventually return None as we
            # 024449.python.psposix.line118.comment can't determine its exit status code.
            while _pid_exists(pid):
                interval = sleep(interval)
            return None
        else:
            if retpid == 0:
                # 024450.python.psposix.line124.comment WNOHANG flag was used and PID is still running.
                interval = sleep(interval)
                continue

            if os.WIFEXITED(status):
                # 024451.python.psposix.line129.comment Process terminated normally by calling exit(3) or _exit(2),
                # 024452.python.psposix.line130.comment or by returning from main(). The return value is the
                # 024453.python.psposix.line131.comment positive integer passed to *exit().
                return os.WEXITSTATUS(status)
            elif os.WIFSIGNALED(status):
                # 024454.python.psposix.line134.comment Process exited due to a signal. Return the negative value
                # 024455.python.psposix.line135.comment of that signal.
                return negsig_to_enum(-os.WTERMSIG(status))
            # 024456.python.psposix.line137.comment elif os.WIFSTOPPED(status):
            # 024457.python.psposix.line138.comment # Process was stopped via SIGSTOP or is being traced, and
            # 024458.python.psposix.line139.comment # waitpid() was called with WUNTRACED flag. PID is still
            # 024459.python.psposix.line140.comment # alive. From now on waitpid() will keep returning (0, 0)
            # 024460.python.psposix.line141.comment # until the process state doesn't change.
            # 024461.python.psposix.line142.comment # It may make sense to catch/enable this since stopped PIDs
            # 024462.python.psposix.line143.comment # ignore SIGTERM.
            # 024463.python.psposix.line144.comment interval = sleep(interval)
            # 024464.python.psposix.line145.comment continue
            # 024465.python.psposix.line146.comment elif os.WIFCONTINUED(status):
            # 024466.python.psposix.line147.comment # Process was resumed via SIGCONT and waitpid() was called
            # 024467.python.psposix.line148.comment # with WCONTINUED flag.
            # 024468.python.psposix.line149.comment interval = sleep(interval)
            # 024469.python.psposix.line150.comment continue
            else:
                # 024470.python.psposix.line152.comment Should never happen.
                msg = f"unknown process exit status {status!r}"
                raise ValueError(msg)


def disk_usage(path):
    """Return disk usage associated with path.
    Note: UNIX usually reserves 5% disk space which is not accessible
    by user. In this function "total" and "used" values reflect the
    total and used disk space whereas "free" and "percent" represent
    the "free" and "used percent" user disk space.
    """
    st = os.statvfs(path)
    # 024471.python.psposix.line165.comment Total space which is only available to root (unless changed
    # 024472.python.psposix.line166.comment at system level).
    total = st.f_blocks * st.f_frsize
    # 024473.python.psposix.line168.comment Remaining free space usable by root.
    avail_to_root = st.f_bfree * st.f_frsize
    # 024474.python.psposix.line170.comment Remaining free space usable by user.
    avail_to_user = st.f_bavail * st.f_frsize
    # 024475.python.psposix.line172.comment Total space being used in general.
    used = total - avail_to_root
    if MACOS:
        # 024476.python.psposix.line175.comment see: https://github.com/giampaolo/psutil/pull/2152
        used = _psutil_osx.disk_usage_used(path, used)
    # 024477.python.psposix.line177.comment Total space which is available to user (same as 'total' but
    # 024478.python.psposix.line178.comment for the user).
    total_user = used + avail_to_user
    # 024479.python.psposix.line180.comment User usage percent compared to the total amount of space
    # 024480.python.psposix.line181.comment the user can use. This number would be higher if compared
    # 024481.python.psposix.line182.comment to root's because the user has less space (usually -5%).
    usage_percent_user = usage_percent(used, total_user, round_=1)

    # 024482.python.psposix.line185.comment NB: the percentage is -5% than what shown by df due to
    # 024483.python.psposix.line186.comment reserved blocks that we are currently not considering:
    # 024484.python.psposix.line187.comment https://github.com/giampaolo/psutil/issues/829#issuecomment-223750462
    return sdiskusage(
        total=total, used=used, free=avail_to_user, percent=usage_percent_user
    )


@memoize
def get_terminal_map():
    """Get a map of device-id -> path as a dict.
    Used by Process.terminal().
    """
    ret = {}
    ls = glob.glob('/dev/tty*') + glob.glob('/dev/pts/*')
    for name in ls:
        assert name not in ret, name
        try:
            ret[os.stat(name).st_rdev] = name
        except FileNotFoundError:
            pass
    return ret
