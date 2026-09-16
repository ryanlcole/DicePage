# 023305.python.init.line1.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 023306.python.init.line2.comment Use of this source code is governed by a BSD-style license that can be
# 023307.python.init.line3.comment found in the LICENSE file.

"""psutil is a cross-platform library for retrieving information on
running processes and system utilization (CPU, memory, disks, network,
sensors) in Python. Supported platforms:

 - Linux
 - Windows
 - macOS
 - FreeBSD
 - OpenBSD
 - NetBSD
 - Sun Solaris
 - AIX

Supported Python versions are cPython 3.6+ and PyPy.
"""

import collections
import contextlib
import datetime
import functools
import os
import signal
import socket
import subprocess
import sys
import threading
import time

try:
    import pwd
except ImportError:
    pwd = None

from . import _common
from ._common import AIX
from ._common import BSD
from ._common import CONN_CLOSE
from ._common import CONN_CLOSE_WAIT
from ._common import CONN_CLOSING
from ._common import CONN_ESTABLISHED
from ._common import CONN_FIN_WAIT1
from ._common import CONN_FIN_WAIT2
from ._common import CONN_LAST_ACK
from ._common import CONN_LISTEN
from ._common import CONN_NONE
from ._common import CONN_SYN_RECV
from ._common import CONN_SYN_SENT
from ._common import CONN_TIME_WAIT
from ._common import FREEBSD
from ._common import LINUX
from ._common import MACOS
from ._common import NETBSD
from ._common import NIC_DUPLEX_FULL
from ._common import NIC_DUPLEX_HALF
from ._common import NIC_DUPLEX_UNKNOWN
from ._common import OPENBSD
from ._common import OSX  # deprecated alias
from ._common import POSIX
from ._common import POWER_TIME_UNKNOWN
from ._common import POWER_TIME_UNLIMITED
from ._common import STATUS_DEAD
from ._common import STATUS_DISK_SLEEP
from ._common import STATUS_IDLE
from ._common import STATUS_LOCKED
from ._common import STATUS_PARKED
from ._common import STATUS_RUNNING
from ._common import STATUS_SLEEPING
from ._common import STATUS_STOPPED
from ._common import STATUS_TRACING_STOP
from ._common import STATUS_WAITING
from ._common import STATUS_WAKING
from ._common import STATUS_ZOMBIE
from ._common import SUNOS
from ._common import WINDOWS
from ._common import AccessDenied
from ._common import Error
from ._common import NoSuchProcess
from ._common import TimeoutExpired
from ._common import ZombieProcess
from ._common import debug
from ._common import memoize_when_activated
from ._common import wrap_numbers as _wrap_numbers

if LINUX:
    # 023309.python.init.line89.comment This is public API and it will be retrieved from _pslinux.py
    # 023310.python.init.line90.comment via sys.modules.
    PROCFS_PATH = "/proc"

    from . import _pslinux as _psplatform
    from ._pslinux import IOPRIO_CLASS_BE  # noqa: F401
    from ._pslinux import IOPRIO_CLASS_IDLE  # noqa: F401
    from ._pslinux import IOPRIO_CLASS_NONE  # noqa: F401
    from ._pslinux import IOPRIO_CLASS_RT  # noqa: F401

elif WINDOWS:
    from . import _pswindows as _psplatform
    from ._psutil_windows import ABOVE_NORMAL_PRIORITY_CLASS  # noqa: F401
    from ._psutil_windows import BELOW_NORMAL_PRIORITY_CLASS  # noqa: F401
    from ._psutil_windows import HIGH_PRIORITY_CLASS  # noqa: F401
    from ._psutil_windows import IDLE_PRIORITY_CLASS  # noqa: F401
    from ._psutil_windows import NORMAL_PRIORITY_CLASS  # noqa: F401
    from ._psutil_windows import REALTIME_PRIORITY_CLASS  # noqa: F401
    from ._pswindows import CONN_DELETE_TCB  # noqa: F401
    from ._pswindows import IOPRIO_HIGH  # noqa: F401
    from ._pswindows import IOPRIO_LOW  # noqa: F401
    from ._pswindows import IOPRIO_NORMAL  # noqa: F401
    from ._pswindows import IOPRIO_VERYLOW  # noqa: F401

elif MACOS:
    from . import _psosx as _psplatform

elif BSD:
    from . import _psbsd as _psplatform

elif SUNOS:
    from . import _pssunos as _psplatform
    from ._pssunos import CONN_BOUND  # noqa: F401
    from ._pssunos import CONN_IDLE  # noqa: F401

    # 023328.python.init.line124.comment This is public writable API which is read from _pslinux.py and
    # 023329.python.init.line125.comment _pssunos.py via sys.modules.
    PROCFS_PATH = "/proc"

elif AIX:
    from . import _psaix as _psplatform

    # 023330.python.init.line131.comment This is public API and it will be retrieved from _pslinux.py
    # 023331.python.init.line132.comment via sys.modules.
    PROCFS_PATH = "/proc"

else:  # pragma: no cover
    msg = f"platform {sys.platform} is not supported"
    raise NotImplementedError(msg)


# 023333.python.init.line140.comment fmt: off
__all__ = [
    # 023334.python.init.line142.comment exceptions
    "Error", "NoSuchProcess", "ZombieProcess", "AccessDenied",
    "TimeoutExpired",

    # 023335.python.init.line146.comment constants
    "version_info", "__version__",

    "STATUS_RUNNING", "STATUS_IDLE", "STATUS_SLEEPING", "STATUS_DISK_SLEEP",
    "STATUS_STOPPED", "STATUS_TRACING_STOP", "STATUS_ZOMBIE", "STATUS_DEAD",
    "STATUS_WAKING", "STATUS_LOCKED", "STATUS_WAITING", "STATUS_LOCKED",
    "STATUS_PARKED",

    "CONN_ESTABLISHED", "CONN_SYN_SENT", "CONN_SYN_RECV", "CONN_FIN_WAIT1",
    "CONN_FIN_WAIT2", "CONN_TIME_WAIT", "CONN_CLOSE", "CONN_CLOSE_WAIT",
    "CONN_LAST_ACK", "CONN_LISTEN", "CONN_CLOSING", "CONN_NONE",
    # 023336.python.init.line157.comment "CONN_IDLE", "CONN_BOUND",

    "AF_LINK",

    "NIC_DUPLEX_FULL", "NIC_DUPLEX_HALF", "NIC_DUPLEX_UNKNOWN",

    "POWER_TIME_UNKNOWN", "POWER_TIME_UNLIMITED",

    "BSD", "FREEBSD", "LINUX", "NETBSD", "OPENBSD", "MACOS", "OSX", "POSIX",
    "SUNOS", "WINDOWS", "AIX",

    # 023337.python.init.line168.comment "RLIM_INFINITY", "RLIMIT_AS", "RLIMIT_CORE", "RLIMIT_CPU", "RLIMIT_DATA",
    # 023338.python.init.line169.comment "RLIMIT_FSIZE", "RLIMIT_LOCKS", "RLIMIT_MEMLOCK", "RLIMIT_NOFILE",
    # 023339.python.init.line170.comment "RLIMIT_NPROC", "RLIMIT_RSS", "RLIMIT_STACK", "RLIMIT_MSGQUEUE",
    # 023340.python.init.line171.comment "RLIMIT_NICE", "RLIMIT_RTPRIO", "RLIMIT_RTTIME", "RLIMIT_SIGPENDING",

    # 023341.python.init.line173.comment classes
    "Process", "Popen",

    # 023342.python.init.line176.comment functions
    "pid_exists", "pids", "process_iter", "wait_procs",             # proc
    "virtual_memory", "swap_memory",                                # memory
    "cpu_times", "cpu_percent", "cpu_times_percent", "cpu_count",   # cpu
    "cpu_stats",  # "cpu_freq", "getloadavg"
    "net_io_counters", "net_connections", "net_if_addrs",           # network
    "net_if_stats",
    "disk_io_counters", "disk_partitions", "disk_usage",            # disk
    # 023349.python.init.line184.comment "sensors_temperatures", "sensors_battery", "sensors_fans"     # sensors
    "users", "boot_time",                                           # others
]
# 023351.python.init.line187.comment fmt: on


__all__.extend(_psplatform.__extra__all__)

# 023352.python.init.line192.comment Linux, FreeBSD
if hasattr(_psplatform.Process, "rlimit"):
    # 023353.python.init.line194.comment Populate global namespace with RLIM* constants.
    from . import _psutil_posix

    _globals = globals()
    _name = None
    for _name in dir(_psutil_posix):
        if _name.startswith('RLIM') and _name.isupper():
            _globals[_name] = getattr(_psutil_posix, _name)
            __all__.append(_name)
    del _globals, _name

AF_LINK = _psplatform.AF_LINK

__author__ = "Giampaolo Rodola'"
__version__ = "7.1.0"
version_info = tuple(int(num) for num in __version__.split('.'))

_timer = getattr(time, 'monotonic', time.time)
_TOTAL_PHYMEM = None
_LOWEST_PID = None
_SENTINEL = object()

# 023354.python.init.line216.comment Sanity check in case the user messed up with psutil installation
# 023355.python.init.line217.comment or did something weird with sys.path. In this case we might end
# 023356.python.init.line218.comment up importing a python module using a C extension module which
# 023357.python.init.line219.comment was compiled for a different version of psutil.
# 023358.python.init.line220.comment We want to prevent that by failing sooner rather than later.
# 023359.python.init.line221.comment See: https://github.com/giampaolo/psutil/issues/564
if int(__version__.replace('.', '')) != getattr(
    _psplatform.cext, 'version', None
):
    msg = f"version conflict: {_psplatform.cext.__file__!r} C extension "
    msg += "module was built for another version of psutil"
    if hasattr(_psplatform.cext, 'version'):
        v = ".".join(list(str(_psplatform.cext.version)))
        msg += f" ({v} instead of {__version__})"
    else:
        msg += f" (different than {__version__})"
    what = getattr(
        _psplatform.cext,
        "__file__",
        "the existing psutil install directory",
    )
    msg += f"; you may try to 'pip uninstall psutil', manually remove {what}"
    msg += " or clean the virtual env somehow, then reinstall"
    raise ImportError(msg)


# 023360.python.init.line242.comment =====================================================================
# 023361.python.init.line243.comment --- Utils
# 023362.python.init.line244.comment =====================================================================


if hasattr(_psplatform, 'ppid_map'):
    # 023363.python.init.line248.comment Faster version (Windows and Linux).
    _ppid_map = _psplatform.ppid_map
else:  # pragma: no cover

    def _ppid_map():
        """Return a {pid: ppid, ...} dict for all running processes in
        one shot. Used to speed up Process.children().
        """
        ret = {}
        for pid in pids():
            try:
                ret[pid] = _psplatform.Process(pid).ppid()
            except (NoSuchProcess, ZombieProcess):
                pass
        return ret


def _pprint_secs(secs):
    """Format seconds in a human readable form."""
    now = time.time()
    secs_ago = int(now - secs)
    fmt = "%H:%M:%S" if secs_ago < 60 * 60 * 24 else "%Y-%m-%d %H:%M:%S"
    return datetime.datetime.fromtimestamp(secs).strftime(fmt)


def _check_conn_kind(kind):
    """Check net_connections()'s `kind` parameter."""
    kinds = tuple(_common.conn_tmap)
    if kind not in kinds:
        msg = f"invalid kind argument {kind!r}; valid ones are: {kinds}"
        raise ValueError(msg)


# 023365.python.init.line281.comment =====================================================================
# 023366.python.init.line282.comment --- Process class
# 023367.python.init.line283.comment =====================================================================


class Process:
    """Represents an OS process with the given PID.
    If PID is omitted current process PID (os.getpid()) is used.
    Raise NoSuchProcess if PID does not exist.

    Note that most of the methods of this class do not make sure that
    the PID of the process being queried has been reused. That means
    that you may end up retrieving information for another process.

    The only exceptions for which process identity is pre-emptively
    checked and guaranteed are:

     - parent()
     - children()
     - nice() (set)
     - ionice() (set)
     - rlimit() (set)
     - cpu_affinity (set)
     - suspend()
     - resume()
     - send_signal()
     - terminate()
     - kill()

    To prevent this problem for all other methods you can use
    is_running() before querying the process.
    """

    def __init__(self, pid=None):
        self._init(pid)

    def _init(self, pid, _ignore_nsp=False):
        if pid is None:
            pid = os.getpid()
        else:
            if pid < 0:
                msg = f"pid must be a positive integer (got {pid})"
                raise ValueError(msg)
            try:
                _psplatform.cext.check_pid_range(pid)
            except OverflowError as err:
                msg = "process PID out of range"
                raise NoSuchProcess(pid, msg=msg) from err

        self._pid = pid
        self._name = None
        self._exe = None
        self._create_time = None
        self._gone = False
        self._pid_reused = False
        self._hash = None
        self._lock = threading.RLock()
        # 023368.python.init.line338.comment used for caching on Windows only (on POSIX ppid may change)
        self._ppid = None
        # 023369.python.init.line340.comment platform-specific modules define an _psplatform.Process
        # 023370.python.init.line341.comment implementation class
        self._proc = _psplatform.Process(pid)
        self._last_sys_cpu_times = None
        self._last_proc_cpu_times = None
        self._exitcode = _SENTINEL
        self._ident = (self.pid, None)
        try:
            self._ident = self._get_ident()
        except AccessDenied:
            # 023371.python.init.line350.comment This should happen on Windows only, since we use the fast
            # 023372.python.init.line351.comment create time method. AFAIK, on all other platforms we are
            # 023373.python.init.line352.comment able to get create time for all PIDs.
            pass
        except ZombieProcess:
            # 023374.python.init.line355.comment Zombies can still be queried by this class (although
            # 023375.python.init.line356.comment not always) and pids() return them so just go on.
            pass
        except NoSuchProcess:
            if not _ignore_nsp:
                msg = "process PID not found"
                raise NoSuchProcess(pid, msg=msg) from None
            self._gone = True

    def _get_ident(self):
        """Return a (pid, uid) tuple which is supposed to identify a
        Process instance univocally over time. The PID alone is not
        enough, as it can be assigned to a new process after this one
        terminates, so we add process creation time to the mix. We need
        this in order to prevent killing the wrong process later on.
        This is also known as PID reuse or PID recycling problem.

        The reliability of this strategy mostly depends on
        create_time() precision, which is 0.01 secs on Linux. The
        assumption is that, after a process terminates, the kernel
        won't reuse the same PID after such a short period of time
        (0.01 secs). Technically this is inherently racy, but
        practically it should be good enough.

        NOTE: unreliable on FreeBSD and OpenBSD as ctime is subject to
        system clock updates.
        """

        if WINDOWS:
            # 023376.python.init.line384.comment Use create_time() fast method in order to speedup
            # 023377.python.init.line385.comment `process_iter()`. This means we'll get AccessDenied for
            # 023378.python.init.line386.comment most ADMIN processes, but that's fine since it means
            # 023379.python.init.line387.comment we'll also get AccessDenied on kill().
            # 023380.python.init.line388.comment https://github.com/giampaolo/psutil/issues/2366#issuecomment-2381646555
            self._create_time = self._proc.create_time(fast_only=True)
            return (self.pid, self._create_time)
        elif LINUX or NETBSD or OSX:
            # 023381.python.init.line392.comment Use 'monotonic' process starttime since boot to form unique
            # 023382.python.init.line393.comment process identity, since it is stable over changes to system
            # 023383.python.init.line394.comment time.
            return (self.pid, self._proc.create_time(monotonic=True))
        else:
            return (self.pid, self.create_time())

    def __str__(self):
        info = collections.OrderedDict()
        info["pid"] = self.pid
        if self._name:
            info['name'] = self._name
        with self.oneshot():
            if self._pid_reused:
                info["status"] = "terminated + PID reused"
            else:
                try:
                    info["name"] = self.name()
                    info["status"] = self.status()
                except ZombieProcess:
                    info["status"] = "zombie"
                except NoSuchProcess:
                    info["status"] = "terminated"
                except AccessDenied:
                    pass

            if self._exitcode not in {_SENTINEL, None}:
                info["exitcode"] = self._exitcode
            if self._create_time is not None:
                info['started'] = _pprint_secs(self._create_time)

            return "{}.{}({})".format(
                self.__class__.__module__,
                self.__class__.__name__,
                ", ".join([f"{k}={v!r}" for k, v in info.items()]),
            )

    __repr__ = __str__

    def __eq__(self, other):
        # 023384.python.init.line432.comment Test for equality with another Process object based
        # 023385.python.init.line433.comment on PID and creation time.
        if not isinstance(other, Process):
            return NotImplemented
        if OPENBSD or NETBSD or SUNOS:  # pragma: no cover
            # 023387.python.init.line437.comment Zombie processes on Open/NetBSD/illumos/Solaris have a
            # 023388.python.init.line438.comment creation time of 0.0.  This covers the case when a process
            # 023389.python.init.line439.comment started normally (so it has a ctime), then it turned into a
            # 023390.python.init.line440.comment zombie. It's important to do this because is_running()
            # 023391.python.init.line441.comment depends on __eq__.
            pid1, ident1 = self._ident
            pid2, ident2 = other._ident
            if pid1 == pid2:
                if ident1 and not ident2:
                    try:
                        return self.status() == STATUS_ZOMBIE
                    except Error:
                        pass
        return self._ident == other._ident

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self._ident)
        return self._hash

    def _raise_if_pid_reused(self):
        """Raises NoSuchProcess in case process PID has been reused."""
        if self._pid_reused or (not self.is_running() and self._pid_reused):
            # 023392.python.init.line463.comment We may directly raise NSP in here already if PID is just
            # 023393.python.init.line464.comment not running, but I prefer NSP to be raised naturally by
            # 023394.python.init.line465.comment the actual Process API call. This way unit tests will tell
            # 023395.python.init.line466.comment us if the API is broken (aka don't raise NSP when it
            # 023396.python.init.line467.comment should). We also remain consistent with all other "get"
            # 023397.python.init.line468.comment APIs which don't use _raise_if_pid_reused().
            msg = "process no longer exists and its PID has been reused"
            raise NoSuchProcess(self.pid, self._name, msg=msg)

    @property
    def pid(self):
        """The process PID."""
        return self._pid

    # 023398.python.init.line477.comment --- utility methods

    @contextlib.contextmanager
    def oneshot(self):
        """Utility context manager which considerably speeds up the
        retrieval of multiple process information at the same time.

        Internally different process info (e.g. name, ppid, uids,
        gids, ...) may be fetched by using the same routine, but
        only one information is returned and the others are discarded.
        When using this context manager the internal routine is
        executed once (in the example below on name()) and the
        other info are cached.

        The cache is cleared when exiting the context manager block.
        The advice is to use this every time you retrieve more than
        one information about the process. If you're lucky, you'll
        get a hell of a speedup.

        >>> import psutil
        >>> p = psutil.Process()
        >>> with p.oneshot():
        ...     p.name()  # collect multiple info
        ...     p.cpu_times()  # return cached value
        ...     p.cpu_percent()  # return cached value
        ...     p.create_time()  # return cached value
        ...
        >>>
        """
        with self._lock:
            if hasattr(self, "_cache"):
                # 023399.python.init.line508.comment NOOP: this covers the use case where the user enters the
                # 023400.python.init.line509.comment context twice:
                # 023401.python.init.line510.comment
                # 023402.python.init.line511.comment >>> with p.oneshot():
                # 023403.python.init.line512.comment ...    with p.oneshot():
                # 023404.python.init.line513.comment ...
                # 023405.python.init.line514.comment
                # 023406.python.init.line515.comment Also, since as_dict() internally uses oneshot()
                # 023407.python.init.line516.comment I expect that the code below will be a pretty common
                # 023408.python.init.line517.comment "mistake" that the user will make, so let's guard
                # 023409.python.init.line518.comment against that:
                # 023410.python.init.line519.comment
                # 023411.python.init.line520.comment >>> with p.oneshot():
                # 023412.python.init.line521.comment ...    p.as_dict()
                # 023413.python.init.line522.comment ...
                yield
            else:
                try:
                    # 023414.python.init.line526.comment cached in case cpu_percent() is used
                    self.cpu_times.cache_activate(self)
                    # 023415.python.init.line528.comment cached in case memory_percent() is used
                    self.memory_info.cache_activate(self)
                    # 023416.python.init.line530.comment cached in case parent() is used
                    self.ppid.cache_activate(self)
                    # 023417.python.init.line532.comment cached in case username() is used
                    if POSIX:
                        self.uids.cache_activate(self)
                    # 023418.python.init.line535.comment specific implementation cache
                    self._proc.oneshot_enter()
                    yield
                finally:
                    self.cpu_times.cache_deactivate(self)
                    self.memory_info.cache_deactivate(self)
                    self.ppid.cache_deactivate(self)
                    if POSIX:
                        self.uids.cache_deactivate(self)
                    self._proc.oneshot_exit()

    def as_dict(self, attrs=None, ad_value=None):
        """Utility method returning process information as a
        hashable dictionary.
        If *attrs* is specified it must be a list of strings
        reflecting available Process class' attribute names
        (e.g. ['cpu_times', 'name']) else all public (read
        only) attributes are assumed.
        *ad_value* is the value which gets assigned in case
        AccessDenied or ZombieProcess exception is raised when
        retrieving that particular process information.
        """
        valid_names = _as_dict_attrnames
        if attrs is not None:
            if not isinstance(attrs, (list, tuple, set, frozenset)):
                msg = f"invalid attrs type {type(attrs)}"
                raise TypeError(msg)
            attrs = set(attrs)
            invalid_names = attrs - valid_names
            if invalid_names:
                msg = "invalid attr name{} {}".format(
                    "s" if len(invalid_names) > 1 else "",
                    ", ".join(map(repr, invalid_names)),
                )
                raise ValueError(msg)

        retdict = {}
        ls = attrs or valid_names
        with self.oneshot():
            for name in ls:
                try:
                    if name == 'pid':
                        ret = self.pid
                    else:
                        meth = getattr(self, name)
                        ret = meth()
                except (AccessDenied, ZombieProcess):
                    ret = ad_value
                except NotImplementedError:
                    # 023419.python.init.line584.comment in case of not implemented functionality (may happen
                    # 023420.python.init.line585.comment on old or exotic systems) we want to crash only if
                    # 023421.python.init.line586.comment the user explicitly asked for that particular attr
                    if attrs:
                        raise
                    continue
                retdict[name] = ret
        return retdict

    def parent(self):
        """Return the parent process as a Process object pre-emptively
        checking whether PID has been reused.
        If no parent is known return None.
        """
        lowest_pid = _LOWEST_PID if _LOWEST_PID is not None else pids()[0]
        if self.pid == lowest_pid:
            return None
        ppid = self.ppid()
        if ppid is not None:
            # 023422.python.init.line603.comment Get a fresh (non-cached) ctime in case the system clock
            # 023423.python.init.line604.comment was updated. TODO: use a monotonic ctime on platforms
            # 023424.python.init.line605.comment where it's supported.
            proc_ctime = Process(self.pid).create_time()
            try:
                parent = Process(ppid)
                if parent.create_time() <= proc_ctime:
                    return parent
                # 023425.python.init.line611.comment ...else ppid has been reused by another process
            except NoSuchProcess:
                pass

    def parents(self):
        """Return the parents of this process as a list of Process
        instances. If no parents are known return an empty list.
        """
        parents = []
        proc = self.parent()
        while proc is not None:
            parents.append(proc)
            proc = proc.parent()
        return parents

    def is_running(self):
        """Return whether this process is running.

        It also checks if PID has been reused by another process, in
        which case it will remove the process from `process_iter()`
        internal cache and return False.
        """
        if self._gone or self._pid_reused:
            return False
        try:
            # 023426.python.init.line636.comment Checking if PID is alive is not enough as the PID might
            # 023427.python.init.line637.comment have been reused by another process. Process identity /
            # 023428.python.init.line638.comment uniqueness over time is guaranteed by (PID + creation
            # 023429.python.init.line639.comment time) and that is verified in __eq__.
            self._pid_reused = self != Process(self.pid)
            if self._pid_reused:
                _pids_reused.add(self.pid)
                raise NoSuchProcess(self.pid)
            return True
        except ZombieProcess:
            # 023430.python.init.line646.comment We should never get here as it's already handled in
            # 023431.python.init.line647.comment Process.__init__; here just for extra safety.
            return True
        except NoSuchProcess:
            self._gone = True
            return False

    # 023432.python.init.line653.comment --- actual API

    @memoize_when_activated
    def ppid(self):
        """The process parent PID.
        On Windows the return value is cached after first call.
        """
        # 023433.python.init.line660.comment On POSIX we don't want to cache the ppid as it may unexpectedly
        # 023434.python.init.line661.comment change to 1 (init) in case this process turns into a zombie:
        # 023435.python.init.line662.comment https://github.com/giampaolo/psutil/issues/321
        # 023436.python.init.line663.comment http://stackoverflow.com/questions/356722/

        # 023437.python.init.line665.comment XXX should we check creation time here rather than in
        # 023438.python.init.line666.comment Process.parent()?
        self._raise_if_pid_reused()
        if POSIX:
            return self._proc.ppid()
        else:  # pragma: no cover
            self._ppid = self._ppid or self._proc.ppid()
            return self._ppid

    def name(self):
        """The process name. The return value is cached after first call."""
        # 023440.python.init.line676.comment Process name is only cached on Windows as on POSIX it may
        # 023441.python.init.line677.comment change, see:
        # 023442.python.init.line678.comment https://github.com/giampaolo/psutil/issues/692
        if WINDOWS and self._name is not None:
            return self._name
        name = self._proc.name()
        if POSIX and len(name) >= 15:
            # 023443.python.init.line683.comment On UNIX the name gets truncated to the first 15 characters.
            # 023444.python.init.line684.comment If it matches the first part of the cmdline we return that
            # 023445.python.init.line685.comment one instead because it's usually more explicative.
            # 023446.python.init.line686.comment Examples are "gnome-keyring-d" vs. "gnome-keyring-daemon".
            try:
                cmdline = self.cmdline()
            except (AccessDenied, ZombieProcess):
                # 023447.python.init.line690.comment Just pass and return the truncated name: it's better
                # 023448.python.init.line691.comment than nothing. Note: there are actual cases where a
                # 023449.python.init.line692.comment zombie process can return a name() but not a
                # 023450.python.init.line693.comment cmdline(), see:
                # 023451.python.init.line694.comment https://github.com/giampaolo/psutil/issues/2239
                pass
            else:
                if cmdline:
                    extended_name = os.path.basename(cmdline[0])
                    if extended_name.startswith(name):
                        name = extended_name
        self._name = name
        self._proc._name = name
        return name

    def exe(self):
        """The process executable as an absolute path.
        May also be an empty string.
        The return value is cached after first call.
        """

        def guess_it(fallback):
            # 023452.python.init.line712.comment try to guess exe from cmdline[0] in absence of a native
            # 023453.python.init.line713.comment exe representation
            cmdline = self.cmdline()
            if cmdline and hasattr(os, 'access') and hasattr(os, 'X_OK'):
                exe = cmdline[0]  # the possible exe
                # 023455.python.init.line717.comment Attempt to guess only in case of an absolute path.
                # 023456.python.init.line718.comment It is not safe otherwise as the process might have
                # 023457.python.init.line719.comment changed cwd.
                if (
                    os.path.isabs(exe)
                    and os.path.isfile(exe)
                    and os.access(exe, os.X_OK)
                ):
                    return exe
            if isinstance(fallback, AccessDenied):
                raise fallback
            return fallback

        if self._exe is None:
            try:
                exe = self._proc.exe()
            except AccessDenied as err:
                return guess_it(fallback=err)
            else:
                if not exe:
                    # 023458.python.init.line737.comment underlying implementation can legitimately return an
                    # 023459.python.init.line738.comment empty string; if that's the case we don't want to
                    # 023460.python.init.line739.comment raise AD while guessing from the cmdline
                    try:
                        exe = guess_it(fallback=exe)
                    except AccessDenied:
                        pass
                self._exe = exe
        return self._exe

    def cmdline(self):
        """The command line this process has been called with."""
        return self._proc.cmdline()

    def status(self):
        """The process current status as a STATUS_* constant."""
        try:
            return self._proc.status()
        except ZombieProcess:
            return STATUS_ZOMBIE

    def username(self):
        """The name of the user that owns the process.
        On UNIX this is calculated by using *real* process uid.
        """
        if POSIX:
            if pwd is None:
                # 023461.python.init.line764.comment might happen if python was installed from sources
                msg = "requires pwd module shipped with standard python"
                raise ImportError(msg)
            real_uid = self.uids().real
            try:
                return pwd.getpwuid(real_uid).pw_name
            except KeyError:
                # 023462.python.init.line771.comment the uid can't be resolved by the system
                return str(real_uid)
        else:
            return self._proc.username()

    def create_time(self):
        """The process creation time as a floating point number
        expressed in seconds since the epoch (seconds since January 1,
        1970, at midnight UTC). The return value, which is cached after
        first call, is based on the system clock, which means it may be
        affected by changes such as manual adjustments or time
        synchronization (e.g. NTP).
        """
        if self._create_time is None:
            self._create_time = self._proc.create_time()
        return self._create_time

    def cwd(self):
        """Process current working directory as an absolute path."""
        return self._proc.cwd()

    def nice(self, value=None):
        """Get or set process niceness (priority)."""
        if value is None:
            return self._proc.nice_get()
        else:
            self._raise_if_pid_reused()
            self._proc.nice_set(value)

    if POSIX:

        @memoize_when_activated
        def uids(self):
            """Return process UIDs as a (real, effective, saved)
            namedtuple.
            """
            return self._proc.uids()

        def gids(self):
            """Return process GIDs as a (real, effective, saved)
            namedtuple.
            """
            return self._proc.gids()

        def terminal(self):
            """The terminal associated with this process, if any,
            else None.
            """
            return self._proc.terminal()

        def num_fds(self):
            """Return the number of file descriptors opened by this
            process (POSIX only).
            """
            return self._proc.num_fds()

    # 023463.python.init.line827.comment Linux, BSD, AIX and Windows only
    if hasattr(_psplatform.Process, "io_counters"):

        def io_counters(self):
            """Return process I/O statistics as a
            (read_count, write_count, read_bytes, write_bytes)
            namedtuple.
            Those are the number of read/write calls performed and the
            amount of bytes read and written by the process.
            """
            return self._proc.io_counters()

    # 023464.python.init.line839.comment Linux and Windows
    if hasattr(_psplatform.Process, "ionice_get"):

        def ionice(self, ioclass=None, value=None):
            """Get or set process I/O niceness (priority).

            On Linux *ioclass* is one of the IOPRIO_CLASS_* constants.
            *value* is a number which goes from 0 to 7. The higher the
            value, the lower the I/O priority of the process.

            On Windows only *ioclass* is used and it can be set to 2
            (normal), 1 (low) or 0 (very low).

            Available on Linux and Windows > Vista only.
            """
            if ioclass is None:
                if value is not None:
                    msg = "'ioclass' argument must be specified"
                    raise ValueError(msg)
                return self._proc.ionice_get()
            else:
                self._raise_if_pid_reused()
                return self._proc.ionice_set(ioclass, value)

    # 023465.python.init.line863.comment Linux / FreeBSD only
    if hasattr(_psplatform.Process, "rlimit"):

        def rlimit(self, resource, limits=None):
            """Get or set process resource limits as a (soft, hard)
            tuple.

            *resource* is one of the RLIMIT_* constants.
            *limits* is supposed to be a (soft, hard) tuple.

            See "man prlimit" for further info.
            Available on Linux and FreeBSD only.
            """
            if limits is not None:
                self._raise_if_pid_reused()
            return self._proc.rlimit(resource, limits)

    # 023466.python.init.line880.comment Windows, Linux and FreeBSD only
    if hasattr(_psplatform.Process, "cpu_affinity_get"):

        def cpu_affinity(self, cpus=None):
            """Get or set process CPU affinity.
            If specified, *cpus* must be a list of CPUs for which you
            want to set the affinity (e.g. [0, 1]).
            If an empty list is passed, all egible CPUs are assumed
            (and set).
            (Windows, Linux and BSD only).
            """
            if cpus is None:
                return sorted(set(self._proc.cpu_affinity_get()))
            else:
                self._raise_if_pid_reused()
                if not cpus:
                    if hasattr(self._proc, "_get_eligible_cpus"):
                        cpus = self._proc._get_eligible_cpus()
                    else:
                        cpus = tuple(range(len(cpu_times(percpu=True))))
                self._proc.cpu_affinity_set(list(set(cpus)))

    # 023467.python.init.line902.comment Linux, FreeBSD, SunOS
    if hasattr(_psplatform.Process, "cpu_num"):

        def cpu_num(self):
            """Return what CPU this process is currently running on.
            The returned number should be <= psutil.cpu_count()
            and <= len(psutil.cpu_percent(percpu=True)).
            It may be used in conjunction with
            psutil.cpu_percent(percpu=True) to observe the system
            workload distributed across CPUs.
            """
            return self._proc.cpu_num()

    # 023468.python.init.line915.comment All platforms has it, but maybe not in the future.
    if hasattr(_psplatform.Process, "environ"):

        def environ(self):
            """The environment variables of the process as a dict.  Note: this
            might not reflect changes made after the process started.
            """
            return self._proc.environ()

    if WINDOWS:

        def num_handles(self):
            """Return the number of handles opened by this process
            (Windows only).
            """
            return self._proc.num_handles()

    def num_ctx_switches(self):
        """Return the number of voluntary and involuntary context
        switches performed by this process.
        """
        return self._proc.num_ctx_switches()

    def num_threads(self):
        """Return the number of threads used by this process."""
        return self._proc.num_threads()

    if hasattr(_psplatform.Process, "threads"):

        def threads(self):
            """Return threads opened by process as a list of
            (id, user_time, system_time) namedtuples representing
            thread id and thread CPU times (user/system).
            On OpenBSD this method requires root access.
            """
            return self._proc.threads()

    def children(self, recursive=False):
        """Return the children of this process as a list of Process
        instances, pre-emptively checking whether PID has been reused.
        If *recursive* is True return all the parent descendants.

        Example (A == this process):

         A ─┐
            │
            ├─ B (child) ─┐
            │             └─ X (grandchild) ─┐
            │                                └─ Y (great grandchild)
            ├─ C (child)
            └─ D (child)

        >>> import psutil
        >>> p = psutil.Process()
        >>> p.children()
        B, C, D
        >>> p.children(recursive=True)
        B, X, Y, C, D

        Note that in the example above if process X disappears
        process Y won't be listed as the reference to process A
        is lost.
        """
        self._raise_if_pid_reused()
        ppid_map = _ppid_map()
        # 023469.python.init.line980.comment Get a fresh (non-cached) ctime in case the system clock was
        # 023470.python.init.line981.comment updated. TODO: use a monotonic ctime on platforms where it's
        # 023471.python.init.line982.comment supported.
        proc_ctime = Process(self.pid).create_time()
        ret = []
        if not recursive:
            for pid, ppid in ppid_map.items():
                if ppid == self.pid:
                    try:
                        child = Process(pid)
                        # 023472.python.init.line990.comment if child happens to be older than its parent
                        # 023473.python.init.line991.comment (self) it means child's PID has been reused
                        if proc_ctime <= child.create_time():
                            ret.append(child)
                    except (NoSuchProcess, ZombieProcess):
                        pass
        else:
            # 023474.python.init.line997.comment Construct a {pid: [child pids]} dict
            reverse_ppid_map = collections.defaultdict(list)
            for pid, ppid in ppid_map.items():
                reverse_ppid_map[ppid].append(pid)
            # 023475.python.init.line1001.comment Recursively traverse that dict, starting from self.pid,
            # 023476.python.init.line1002.comment such that we only call Process() on actual children
            seen = set()
            stack = [self.pid]
            while stack:
                pid = stack.pop()
                if pid in seen:
                    # 023477.python.init.line1008.comment Since pids can be reused while the ppid_map is
                    # 023478.python.init.line1009.comment constructed, there may be rare instances where
                    # 023479.python.init.line1010.comment there's a cycle in the recorded process "tree".
                    continue
                seen.add(pid)
                for child_pid in reverse_ppid_map[pid]:
                    try:
                        child = Process(child_pid)
                        # 023480.python.init.line1016.comment if child happens to be older than its parent
                        # 023481.python.init.line1017.comment (self) it means child's PID has been reused
                        intime = proc_ctime <= child.create_time()
                        if intime:
                            ret.append(child)
                            stack.append(child_pid)
                    except (NoSuchProcess, ZombieProcess):
                        pass
        return ret

    def cpu_percent(self, interval=None):
        """Return a float representing the current process CPU
        utilization as a percentage.

        When *interval* is 0.0 or None (default) compares process times
        to system CPU times elapsed since last call, returning
        immediately (non-blocking). That means that the first time
        this is called it will return a meaningful 0.0 value.

        When *interval* is > 0.0 compares process times to system CPU
        times elapsed before and after the interval (blocking).

        In this case is recommended for accuracy that this function
        be called with at least 0.1 seconds between calls.

        A value > 100.0 can be returned in case of processes running
        multiple threads on different CPU cores.

        The returned value is explicitly NOT split evenly between
        all available logical CPUs. This means that a busy loop process
        running on a system with 2 logical CPUs will be reported as
        having 100% CPU utilization instead of 50%.

        Examples:

          >>> import psutil
          >>> p = psutil.Process(os.getpid())
          >>> # blocking
          >>> p.cpu_percent(interval=1)
          2.0
          >>> # non-blocking (percentage since last call)
          >>> p.cpu_percent(interval=None)
          2.9
          >>>
        """
        blocking = interval is not None and interval > 0.0
        if interval is not None and interval < 0:
            msg = f"interval is not positive (got {interval!r})"
            raise ValueError(msg)
        num_cpus = cpu_count() or 1

        def timer():
            return _timer() * num_cpus

        if blocking:
            st1 = timer()
            pt1 = self._proc.cpu_times()
            time.sleep(interval)
            st2 = timer()
            pt2 = self._proc.cpu_times()
        else:
            st1 = self._last_sys_cpu_times
            pt1 = self._last_proc_cpu_times
            st2 = timer()
            pt2 = self._proc.cpu_times()
            if st1 is None or pt1 is None:
                self._last_sys_cpu_times = st2
                self._last_proc_cpu_times = pt2
                return 0.0

        delta_proc = (pt2.user - pt1.user) + (pt2.system - pt1.system)
        delta_time = st2 - st1
        # 023482.python.init.line1088.comment reset values for next call in case of interval == None
        self._last_sys_cpu_times = st2
        self._last_proc_cpu_times = pt2

        try:
            # 023483.python.init.line1093.comment This is the utilization split evenly between all CPUs.
            # 023484.python.init.line1094.comment E.g. a busy loop process on a 2-CPU-cores system at this
            # 023485.python.init.line1095.comment point is reported as 50% instead of 100%.
            overall_cpus_percent = (delta_proc / delta_time) * 100
        except ZeroDivisionError:
            # 023486.python.init.line1098.comment interval was too low
            return 0.0
        else:
            # 023487.python.init.line1101.comment Note 1:
            # 023488.python.init.line1102.comment in order to emulate "top" we multiply the value for the num
            # 023489.python.init.line1103.comment of CPU cores. This way the busy process will be reported as
            # 023490.python.init.line1104.comment having 100% (or more) usage.
            # 023491.python.init.line1105.comment
            # 023492.python.init.line1106.comment Note 2:
            # 023493.python.init.line1107.comment taskmgr.exe on Windows differs in that it will show 50%
            # 023494.python.init.line1108.comment instead.
            # 023495.python.init.line1109.comment
            # 023496.python.init.line1110.comment Note 3:
            # 023497.python.init.line1111.comment a percentage > 100 is legitimate as it can result from a
            # 023498.python.init.line1112.comment process with multiple threads running on different CPU
            # 023499.python.init.line1113.comment cores (top does the same), see:
            # 023500.python.init.line1114.comment http://stackoverflow.com/questions/1032357
            # 023501.python.init.line1115.comment https://github.com/giampaolo/psutil/issues/474
            single_cpu_percent = overall_cpus_percent * num_cpus
            return round(single_cpu_percent, 1)

    @memoize_when_activated
    def cpu_times(self):
        """Return a (user, system, children_user, children_system)
        namedtuple representing the accumulated process time, in
        seconds.
        This is similar to os.times() but per-process.
        On macOS and Windows children_user and children_system are
        always set to 0.
        """
        return self._proc.cpu_times()

    @memoize_when_activated
    def memory_info(self):
        """Return a namedtuple with variable fields depending on the
        platform, representing memory information about the process.

        The "portable" fields available on all platforms are `rss` and `vms`.

        All numbers are expressed in bytes.
        """
        return self._proc.memory_info()

    def memory_full_info(self):
        """This method returns the same information as memory_info(),
        plus, on some platform (Linux, macOS, Windows), also provides
        additional metrics (USS, PSS and swap).
        The additional metrics provide a better representation of actual
        process memory usage.

        Namely USS is the memory which is unique to a process and which
        would be freed if the process was terminated right now.

        It does so by passing through the whole process address.
        As such it usually requires higher user privileges than
        memory_info() and is considerably slower.
        """
        return self._proc.memory_full_info()

    def memory_percent(self, memtype="rss"):
        """Compare process memory to total physical system memory and
        calculate process memory utilization as a percentage.
        *memtype* argument is a string that dictates what type of
        process memory you want to compare against (defaults to "rss").
        The list of available strings can be obtained like this:

        >>> psutil.Process().memory_info()._fields
        ('rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss')
        """
        valid_types = list(_psplatform.pfullmem._fields)
        if memtype not in valid_types:
            msg = (
                f"invalid memtype {memtype!r}; valid types are"
                f" {tuple(valid_types)!r}"
            )
            raise ValueError(msg)
        fun = (
            self.memory_info
            if memtype in _psplatform.pmem._fields
            else self.memory_full_info
        )
        metrics = fun()
        value = getattr(metrics, memtype)

        # 023502.python.init.line1182.comment use cached value if available
        total_phymem = _TOTAL_PHYMEM or virtual_memory().total
        if not total_phymem > 0:
            # 023503.python.init.line1185.comment we should never get here
            msg = (
                "can't calculate process memory percent because total physical"
                f" system memory is not positive ({total_phymem!r})"
            )
            raise ValueError(msg)
        return (value / float(total_phymem)) * 100

    if hasattr(_psplatform.Process, "memory_maps"):

        def memory_maps(self, grouped=True):
            """Return process' mapped memory regions as a list of namedtuples
            whose fields are variable depending on the platform.

            If *grouped* is True the mapped regions with the same 'path'
            are grouped together and the different memory fields are summed.

            If *grouped* is False every mapped region is shown as a single
            entity and the namedtuple will also include the mapped region's
            address space ('addr') and permission set ('perms').
            """
            it = self._proc.memory_maps()
            if grouped:
                d = {}
                for tupl in it:
                    path = tupl[2]
                    nums = tupl[3:]
                    try:
                        d[path] = list(map(lambda x, y: x + y, d[path], nums))
                    except KeyError:
                        d[path] = nums
                nt = _psplatform.pmmap_grouped
                return [nt(path, *d[path]) for path in d]
            else:
                nt = _psplatform.pmmap_ext
                return [nt(*x) for x in it]

    def open_files(self):
        """Return files opened by process as a list of
        (path, fd) namedtuples including the absolute file name
        and file descriptor number.
        """
        return self._proc.open_files()

    def net_connections(self, kind='inet'):
        """Return socket connections opened by process as a list of
        (fd, family, type, laddr, raddr, status) namedtuples.
        The *kind* parameter filters for connections that match the
        following criteria:

        +------------+----------------------------------------------------+
        | Kind Value | Connections using                                  |
        +------------+----------------------------------------------------+
        | inet       | IPv4 and IPv6                                      |
        | inet4      | IPv4                                               |
        | inet6      | IPv6                                               |
        | tcp        | TCP                                                |
        | tcp4       | TCP over IPv4                                      |
        | tcp6       | TCP over IPv6                                      |
        | udp        | UDP                                                |
        | udp4       | UDP over IPv4                                      |
        | udp6       | UDP over IPv6                                      |
        | unix       | UNIX socket (both UDP and TCP protocols)           |
        | all        | the sum of all the possible families and protocols |
        +------------+----------------------------------------------------+
        """
        _check_conn_kind(kind)
        return self._proc.net_connections(kind)

    @_common.deprecated_method(replacement="net_connections")
    def connections(self, kind="inet"):
        return self.net_connections(kind=kind)

    # 023504.python.init.line1258.comment --- signals

    if POSIX:

        def _send_signal(self, sig):
            assert not self.pid < 0, self.pid
            self._raise_if_pid_reused()

            pid, ppid, name = self.pid, self._ppid, self._name
            if pid == 0:
                # 023505.python.init.line1268.comment see "man 2 kill"
                msg = (
                    "preventing sending signal to process with PID 0 as it "
                    "would affect every process in the process group of the "
                    "calling process (os.getpid()) instead of PID 0"
                )
                raise ValueError(msg)
            try:
                os.kill(pid, sig)
            except ProcessLookupError as err:
                if OPENBSD and pid_exists(pid):
                    # 023506.python.init.line1279.comment We do this because os.kill() lies in case of
                    # 023507.python.init.line1280.comment zombie processes.
                    raise ZombieProcess(pid, name, ppid) from err
                self._gone = True
                raise NoSuchProcess(pid, name) from err
            except PermissionError as err:
                raise AccessDenied(pid, name) from err

    def send_signal(self, sig):
        """Send a signal *sig* to process pre-emptively checking
        whether PID has been reused (see signal module constants) .
        On Windows only SIGTERM is valid and is treated as an alias
        for kill().
        """
        if POSIX:
            self._send_signal(sig)
        else:  # pragma: no cover
            self._raise_if_pid_reused()
            if sig != signal.SIGTERM and not self.is_running():
                msg = "process no longer exists"
                raise NoSuchProcess(self.pid, self._name, msg=msg)
            self._proc.send_signal(sig)

    def suspend(self):
        """Suspend process execution with SIGSTOP pre-emptively checking
        whether PID has been reused.
        On Windows this has the effect of suspending all process threads.
        """
        if POSIX:
            self._send_signal(signal.SIGSTOP)
        else:  # pragma: no cover
            self._raise_if_pid_reused()
            self._proc.suspend()

    def resume(self):
        """Resume process execution with SIGCONT pre-emptively checking
        whether PID has been reused.
        On Windows this has the effect of resuming all process threads.
        """
        if POSIX:
            self._send_signal(signal.SIGCONT)
        else:  # pragma: no cover
            self._raise_if_pid_reused()
            self._proc.resume()

    def terminate(self):
        """Terminate the process with SIGTERM pre-emptively checking
        whether PID has been reused.
        On Windows this is an alias for kill().
        """
        if POSIX:
            self._send_signal(signal.SIGTERM)
        else:  # pragma: no cover
            self._raise_if_pid_reused()
            self._proc.kill()

    def kill(self):
        """Kill the current process with SIGKILL pre-emptively checking
        whether PID has been reused.
        """
        if POSIX:
            self._send_signal(signal.SIGKILL)
        else:  # pragma: no cover
            self._raise_if_pid_reused()
            self._proc.kill()

    def wait(self, timeout=None):
        """Wait for process to terminate and, if process is a children
        of os.getpid(), also return its exit code, else None.
        On Windows there's no such limitation (exit code is always
        returned).

        If the process is already terminated immediately return None
        instead of raising NoSuchProcess.

        If *timeout* (in seconds) is specified and process is still
        alive raise TimeoutExpired.

        To wait for multiple Process(es) use psutil.wait_procs().
        """
        if timeout is not None and not timeout >= 0:
            msg = "timeout must be a positive integer"
            raise ValueError(msg)
        if self._exitcode is not _SENTINEL:
            return self._exitcode
        self._exitcode = self._proc.wait(timeout)
        return self._exitcode


# 023513.python.init.line1368.comment The valid attr names which can be processed by Process.as_dict().
# 023514.python.init.line1369.comment fmt: off
_as_dict_attrnames = {
    x for x in dir(Process) if not x.startswith("_") and x not in
     {'send_signal', 'suspend', 'resume', 'terminate', 'kill', 'wait',
      'is_running', 'as_dict', 'parent', 'parents', 'children', 'rlimit',
      'connections', 'oneshot'}
}
# 023515.python.init.line1376.comment fmt: on


# 023516.python.init.line1379.comment =====================================================================
# 023517.python.init.line1380.comment --- Popen class
# 023518.python.init.line1381.comment =====================================================================


class Popen(Process):
    """Same as subprocess.Popen, but in addition it provides all
    psutil.Process methods in a single class.
    For the following methods which are common to both classes, psutil
    implementation takes precedence:

    * send_signal()
    * terminate()
    * kill()

    This is done in order to avoid killing another process in case its
    PID has been reused, fixing BPO-6973.

      >>> import psutil
      >>> from subprocess import PIPE
      >>> p = psutil.Popen(["python", "-c", "print 'hi'"], stdout=PIPE)
      >>> p.name()
      'python'
      >>> p.uids()
      user(real=1000, effective=1000, saved=1000)
      >>> p.username()
      'giampaolo'
      >>> p.communicate()
      ('hi', None)
      >>> p.terminate()
      >>> p.wait(timeout=2)
      0
      >>>
    """

    def __init__(self, *args, **kwargs):
        # 023519.python.init.line1415.comment Explicitly avoid to raise NoSuchProcess in case the process
        # 023520.python.init.line1416.comment spawned by subprocess.Popen terminates too quickly, see:
        # 023521.python.init.line1417.comment https://github.com/giampaolo/psutil/issues/193
        self.__subproc = subprocess.Popen(*args, **kwargs)
        self._init(self.__subproc.pid, _ignore_nsp=True)

    def __dir__(self):
        return sorted(set(dir(Popen) + dir(subprocess.Popen)))

    def __enter__(self):
        if hasattr(self.__subproc, '__enter__'):
            self.__subproc.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        if hasattr(self.__subproc, '__exit__'):
            return self.__subproc.__exit__(*args, **kwargs)
        else:
            if self.stdout:
                self.stdout.close()
            if self.stderr:
                self.stderr.close()
            try:
                # 023522.python.init.line1438.comment Flushing a BufferedWriter may raise an error.
                if self.stdin:
                    self.stdin.close()
            finally:
                # 023523.python.init.line1442.comment Wait for the process to terminate, to avoid zombies.
                self.wait()

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            try:
                return object.__getattribute__(self.__subproc, name)
            except AttributeError:
                msg = f"{self.__class__!r} has no attribute {name!r}"
                raise AttributeError(msg) from None

    def wait(self, timeout=None):
        if self.__subproc.returncode is not None:
            return self.__subproc.returncode
        ret = super().wait(timeout)
        self.__subproc.returncode = ret
        return ret


# 023524.python.init.line1463.comment =====================================================================
# 023525.python.init.line1464.comment --- system processes related functions
# 023526.python.init.line1465.comment =====================================================================


def pids():
    """Return a list of current running PIDs."""
    global _LOWEST_PID
    ret = sorted(_psplatform.pids())
    _LOWEST_PID = ret[0]
    return ret


def pid_exists(pid):
    """Return True if given PID exists in the current process list.
    This is faster than doing "pid in psutil.pids()" and
    should be preferred.
    """
    if pid < 0:
        return False
    elif pid == 0 and POSIX:
        # 023527.python.init.line1484.comment On POSIX we use os.kill() to determine PID existence.
        # 023528.python.init.line1485.comment According to "man 2 kill" PID 0 has a special meaning
        # 023529.python.init.line1486.comment though: it refers to <<every process in the process
        # 023530.python.init.line1487.comment group of the calling process>> and that is not we want
        # 023531.python.init.line1488.comment to do here.
        return pid in pids()
    else:
        return _psplatform.pid_exists(pid)


_pmap = {}
_pids_reused = set()


def process_iter(attrs=None, ad_value=None):
    """Return a generator yielding a Process instance for all
    running processes.

    Every new Process instance is only created once and then cached
    into an internal table which is updated every time this is used.
    Cache can optionally be cleared via `process_iter.cache_clear()`.

    The sorting order in which processes are yielded is based on
    their PIDs.

    *attrs* and *ad_value* have the same meaning as in
    Process.as_dict(). If *attrs* is specified as_dict() is called
    and the resulting dict is stored as a 'info' attribute attached
    to returned Process instance.
    If *attrs* is an empty list it will retrieve all process info
    (slow).
    """
    global _pmap

    def add(pid):
        proc = Process(pid)
        pmap[proc.pid] = proc
        return proc

    def remove(pid):
        pmap.pop(pid, None)

    pmap = _pmap.copy()
    a = set(pids())
    b = set(pmap.keys())
    new_pids = a - b
    gone_pids = b - a
    for pid in gone_pids:
        remove(pid)
    while _pids_reused:
        pid = _pids_reused.pop()
        debug(f"refreshing Process instance for reused PID {pid}")
        remove(pid)
    try:
        ls = sorted(list(pmap.items()) + list(dict.fromkeys(new_pids).items()))
        for pid, proc in ls:
            try:
                if proc is None:  # new process
                    proc = add(pid)
                if attrs is not None:
                    proc.info = proc.as_dict(attrs=attrs, ad_value=ad_value)
                yield proc
            except NoSuchProcess:
                remove(pid)
    finally:
        _pmap = pmap


process_iter.cache_clear = lambda: _pmap.clear()  # noqa: PLW0108
process_iter.cache_clear.__doc__ = "Clear process_iter() internal cache."


def wait_procs(procs, timeout=None, callback=None):
    """Convenience function which waits for a list of processes to
    terminate.

    Return a (gone, alive) tuple indicating which processes
    are gone and which ones are still alive.

    The gone ones will have a new *returncode* attribute indicating
    process exit status (may be None).

    *callback* is a function which gets called every time a process
    terminates (a Process instance is passed as callback argument).

    Function will return as soon as all processes terminate or when
    *timeout* occurs.
    Differently from Process.wait() it will not raise TimeoutExpired if
    *timeout* occurs.

    Typical use case is:

     - send SIGTERM to a list of processes
     - give them some time to terminate
     - send SIGKILL to those ones which are still alive

    Example:

    >>> def on_terminate(proc):
    ...     print("process {} terminated".format(proc))
    ...
    >>> for p in procs:
    ...    p.terminate()
    ...
    >>> gone, alive = wait_procs(procs, timeout=3, callback=on_terminate)
    >>> for p in alive:
    ...     p.kill()
    """

    def check_gone(proc, timeout):
        try:
            returncode = proc.wait(timeout=timeout)
        except (TimeoutExpired, subprocess.TimeoutExpired):
            pass
        else:
            if returncode is not None or not proc.is_running():
                # 023534.python.init.line1600.comment Set new Process instance attribute.
                proc.returncode = returncode
                gone.add(proc)
                if callback is not None:
                    callback(proc)

    if timeout is not None and not timeout >= 0:
        msg = f"timeout must be a positive integer, got {timeout}"
        raise ValueError(msg)
    gone = set()
    alive = set(procs)
    if callback is not None and not callable(callback):
        msg = f"callback {callback!r} is not a callable"
        raise TypeError(msg)
    if timeout is not None:
        deadline = _timer() + timeout

    while alive:
        if timeout is not None and timeout <= 0:
            break
        for proc in alive:
            # 023535.python.init.line1621.comment Make sure that every complete iteration (all processes)
            # 023536.python.init.line1622.comment will last max 1 sec.
            # 023537.python.init.line1623.comment We do this because we don't want to wait too long on a
            # 023538.python.init.line1624.comment single process: in case it terminates too late other
            # 023539.python.init.line1625.comment processes may disappear in the meantime and their PID
            # 023540.python.init.line1626.comment reused.
            max_timeout = 1.0 / len(alive)
            if timeout is not None:
                timeout = min((deadline - _timer()), max_timeout)
                if timeout <= 0:
                    break
                check_gone(proc, timeout)
            else:
                check_gone(proc, max_timeout)
        alive = alive - gone  # noqa: PLR6104

    if alive:
        # 023542.python.init.line1638.comment Last attempt over processes survived so far.
        # 023543.python.init.line1639.comment timeout == 0 won't make this function wait any further.
        for proc in alive:
            check_gone(proc, 0)
        alive = alive - gone  # noqa: PLR6104

    return (list(gone), list(alive))


# 023545.python.init.line1647.comment =====================================================================
# 023546.python.init.line1648.comment --- CPU related functions
# 023547.python.init.line1649.comment =====================================================================


def cpu_count(logical=True):
    """Return the number of logical CPUs in the system (same as
    os.cpu_count()).

    If *logical* is False return the number of physical cores only
    (e.g. hyper thread CPUs are excluded).

    Return None if undetermined.

    The return value is cached after first call.
    If desired cache can be cleared like this:

    >>> psutil.cpu_count.cache_clear()
    """
    if logical:
        ret = _psplatform.cpu_count_logical()
    else:
        ret = _psplatform.cpu_count_cores()
    if ret is not None and ret < 1:
        ret = None
    return ret


def cpu_times(percpu=False):
    """Return system-wide CPU times as a namedtuple.
    Every CPU time represents the seconds the CPU has spent in the
    given mode. The namedtuple's fields availability varies depending on the
    platform:

     - user
     - system
     - idle
     - nice (UNIX)
     - iowait (Linux)
     - irq (Linux, FreeBSD)
     - softirq (Linux)
     - steal (Linux >= 2.6.11)
     - guest (Linux >= 2.6.24)
     - guest_nice (Linux >= 3.2.0)

    When *percpu* is True return a list of namedtuples for each CPU.
    First element of the list refers to first CPU, second element
    to second CPU and so on.
    The order of the list is consistent across calls.
    """
    if not percpu:
        return _psplatform.cpu_times()
    else:
        return _psplatform.per_cpu_times()


try:
    _last_cpu_times = {threading.current_thread().ident: cpu_times()}
except Exception:  # noqa: BLE001
    # 023549.python.init.line1706.comment Don't want to crash at import time.
    _last_cpu_times = {}

try:
    _last_per_cpu_times = {
        threading.current_thread().ident: cpu_times(percpu=True)
    }
except Exception:  # noqa: BLE001
    # 023551.python.init.line1714.comment Don't want to crash at import time.
    _last_per_cpu_times = {}


def _cpu_tot_time(times):
    """Given a cpu_time() ntuple calculates the total CPU time
    (including idle time).
    """
    tot = sum(times)
    if LINUX:
        # 023552.python.init.line1724.comment On Linux guest times are already accounted in "user" or
        # 023553.python.init.line1725.comment "nice" times, so we subtract them from total.
        # 023554.python.init.line1726.comment Htop does the same. References:
        # 023555.python.init.line1727.comment https://github.com/giampaolo/psutil/pull/940
        # 023556.python.init.line1728.comment http://unix.stackexchange.com/questions/178045
        # 023557.python.init.line1729.comment https://github.com/torvalds/linux/blob/
        # 023558.python.init.line1730.comment 447976ef4fd09b1be88b316d1a81553f1aa7cd07/kernel/sched/
        # 023559.python.init.line1731.comment cputime.c#L158
        tot -= getattr(times, "guest", 0)  # Linux 2.6.24+
        tot -= getattr(times, "guest_nice", 0)  # Linux 3.2.0+
    return tot


def _cpu_busy_time(times):
    """Given a cpu_time() ntuple calculates the busy CPU time.
    We do so by subtracting all idle CPU times.
    """
    busy = _cpu_tot_time(times)
    busy -= times.idle
    # 023562.python.init.line1743.comment Linux: "iowait" is time during which the CPU does not do anything
    # 023563.python.init.line1744.comment (waits for IO to complete). On Linux IO wait is *not* accounted
    # 023564.python.init.line1745.comment in "idle" time so we subtract it. Htop does the same.
    # 023565.python.init.line1746.comment References:
    # 023566.python.init.line1747.comment https://github.com/torvalds/linux/blob/
    # 023567.python.init.line1748.comment 447976ef4fd09b1be88b316d1a81553f1aa7cd07/kernel/sched/cputime.c#L244
    busy -= getattr(times, "iowait", 0)
    return busy


def _cpu_times_deltas(t1, t2):
    assert t1._fields == t2._fields, (t1, t2)
    field_deltas = []
    for field in _psplatform.scputimes._fields:
        field_delta = getattr(t2, field) - getattr(t1, field)
        # 023568.python.init.line1758.comment CPU times are always supposed to increase over time
        # 023569.python.init.line1759.comment or at least remain the same and that's because time
        # 023570.python.init.line1760.comment cannot go backwards.
        # 023571.python.init.line1761.comment Surprisingly sometimes this might not be the case (at
        # 023572.python.init.line1762.comment least on Windows and Linux), see:
        # 023573.python.init.line1763.comment https://github.com/giampaolo/psutil/issues/392
        # 023574.python.init.line1764.comment https://github.com/giampaolo/psutil/issues/645
        # 023575.python.init.line1765.comment https://github.com/giampaolo/psutil/issues/1210
        # 023576.python.init.line1766.comment Trim negative deltas to zero to ignore decreasing fields.
        # 023577.python.init.line1767.comment top does the same. Reference:
        # 023578.python.init.line1768.comment https://gitlab.com/procps-ng/procps/blob/v3.3.12/top/top.c#L5063
        field_delta = max(0, field_delta)
        field_deltas.append(field_delta)
    return _psplatform.scputimes(*field_deltas)


def cpu_percent(interval=None, percpu=False):
    """Return a float representing the current system-wide CPU
    utilization as a percentage.

    When *interval* is > 0.0 compares system CPU times elapsed before
    and after the interval (blocking).

    When *interval* is 0.0 or None compares system CPU times elapsed
    since last call or module import, returning immediately (non
    blocking). That means the first time this is called it will
    return a meaningless 0.0 value which you should ignore.
    In this case is recommended for accuracy that this function be
    called with at least 0.1 seconds between calls.

    When *percpu* is True returns a list of floats representing the
    utilization as a percentage for each CPU.
    First element of the list refers to first CPU, second element
    to second CPU and so on.
    The order of the list is consistent across calls.

    Examples:

      >>> # blocking, system-wide
      >>> psutil.cpu_percent(interval=1)
      2.0
      >>>
      >>> # blocking, per-cpu
      >>> psutil.cpu_percent(interval=1, percpu=True)
      [2.0, 1.0]
      >>>
      >>> # non-blocking (percentage since last call)
      >>> psutil.cpu_percent(interval=None)
      2.9
      >>>
    """
    tid = threading.current_thread().ident
    blocking = interval is not None and interval > 0.0
    if interval is not None and interval < 0:
        msg = f"interval is not positive (got {interval})"
        raise ValueError(msg)

    def calculate(t1, t2):
        times_delta = _cpu_times_deltas(t1, t2)
        all_delta = _cpu_tot_time(times_delta)
        busy_delta = _cpu_busy_time(times_delta)

        try:
            busy_perc = (busy_delta / all_delta) * 100
        except ZeroDivisionError:
            return 0.0
        else:
            return round(busy_perc, 1)

    # 023579.python.init.line1827.comment system-wide usage
    if not percpu:
        if blocking:
            t1 = cpu_times()
            time.sleep(interval)
        else:
            t1 = _last_cpu_times.get(tid) or cpu_times()
        _last_cpu_times[tid] = cpu_times()
        return calculate(t1, _last_cpu_times[tid])
    # 023580.python.init.line1836.comment per-cpu usage
    else:
        ret = []
        if blocking:
            tot1 = cpu_times(percpu=True)
            time.sleep(interval)
        else:
            tot1 = _last_per_cpu_times.get(tid) or cpu_times(percpu=True)
        _last_per_cpu_times[tid] = cpu_times(percpu=True)
        for t1, t2 in zip(tot1, _last_per_cpu_times[tid]):
            ret.append(calculate(t1, t2))
        return ret


# 023581.python.init.line1850.comment Use a separate dict for cpu_times_percent(), so it's independent from
# 023582.python.init.line1851.comment cpu_percent() and they can both be used within the same program.
_last_cpu_times_2 = _last_cpu_times.copy()
_last_per_cpu_times_2 = _last_per_cpu_times.copy()


def cpu_times_percent(interval=None, percpu=False):
    """Same as cpu_percent() but provides utilization percentages
    for each specific CPU time as is returned by cpu_times().
    For instance, on Linux we'll get:

      >>> cpu_times_percent()
      cpupercent(user=4.8, nice=0.0, system=4.8, idle=90.5, iowait=0.0,
                 irq=0.0, softirq=0.0, steal=0.0, guest=0.0, guest_nice=0.0)
      >>>

    *interval* and *percpu* arguments have the same meaning as in
    cpu_percent().
    """
    tid = threading.current_thread().ident
    blocking = interval is not None and interval > 0.0
    if interval is not None and interval < 0:
        msg = f"interval is not positive (got {interval!r})"
        raise ValueError(msg)

    def calculate(t1, t2):
        nums = []
        times_delta = _cpu_times_deltas(t1, t2)
        all_delta = _cpu_tot_time(times_delta)
        # 023583.python.init.line1879.comment "scale" is the value to multiply each delta with to get percentages.
        # 023584.python.init.line1880.comment We use "max" to avoid division by zero (if all_delta is 0, then all
        # 023585.python.init.line1881.comment fields are 0 so percentages will be 0 too. all_delta cannot be a
        # 023586.python.init.line1882.comment fraction because cpu times are integers)
        scale = 100.0 / max(1, all_delta)
        for field_delta in times_delta:
            field_perc = field_delta * scale
            field_perc = round(field_perc, 1)
            # 023587.python.init.line1887.comment make sure we don't return negative values or values over 100%
            field_perc = min(max(0.0, field_perc), 100.0)
            nums.append(field_perc)
        return _psplatform.scputimes(*nums)

    # 023588.python.init.line1892.comment system-wide usage
    if not percpu:
        if blocking:
            t1 = cpu_times()
            time.sleep(interval)
        else:
            t1 = _last_cpu_times_2.get(tid) or cpu_times()
        _last_cpu_times_2[tid] = cpu_times()
        return calculate(t1, _last_cpu_times_2[tid])
    # 023589.python.init.line1901.comment per-cpu usage
    else:
        ret = []
        if blocking:
            tot1 = cpu_times(percpu=True)
            time.sleep(interval)
        else:
            tot1 = _last_per_cpu_times_2.get(tid) or cpu_times(percpu=True)
        _last_per_cpu_times_2[tid] = cpu_times(percpu=True)
        for t1, t2 in zip(tot1, _last_per_cpu_times_2[tid]):
            ret.append(calculate(t1, t2))
        return ret


def cpu_stats():
    """Return CPU statistics."""
    return _psplatform.cpu_stats()


if hasattr(_psplatform, "cpu_freq"):

    def cpu_freq(percpu=False):
        """Return CPU frequency as a namedtuple including current,
        min and max frequency expressed in Mhz.

        If *percpu* is True and the system supports per-cpu frequency
        retrieval (Linux only) a list of frequencies is returned for
        each CPU. If not a list with one element is returned.
        """
        ret = _psplatform.cpu_freq()
        if percpu:
            return ret
        else:
            num_cpus = float(len(ret))
            if num_cpus == 0:
                return None
            elif num_cpus == 1:
                return ret[0]
            else:
                currs, mins, maxs = 0.0, 0.0, 0.0
                set_none = False
                for cpu in ret:
                    currs += cpu.current
                    # 023590.python.init.line1944.comment On Linux if /proc/cpuinfo is used min/max are set
                    # 023591.python.init.line1945.comment to None.
                    if LINUX and cpu.min is None:
                        set_none = True
                        continue
                    mins += cpu.min
                    maxs += cpu.max

                current = currs / num_cpus

                if set_none:
                    min_ = max_ = None
                else:
                    min_ = mins / num_cpus
                    max_ = maxs / num_cpus

                return _common.scpufreq(current, min_, max_)

    __all__.append("cpu_freq")


if hasattr(os, "getloadavg") or hasattr(_psplatform, "getloadavg"):
    # 023592.python.init.line1966.comment Perform this hasattr check once on import time to either use the
    # 023593.python.init.line1967.comment platform based code or proxy straight from the os module.
    if hasattr(os, "getloadavg"):
        getloadavg = os.getloadavg
    else:
        getloadavg = _psplatform.getloadavg

    __all__.append("getloadavg")


# 023594.python.init.line1976.comment =====================================================================
# 023595.python.init.line1977.comment --- system memory related functions
# 023596.python.init.line1978.comment =====================================================================


def virtual_memory():
    """Return statistics about system memory usage as a namedtuple
    including the following fields, expressed in bytes:

     - total:
       total physical memory available.

     - available:
       the memory that can be given instantly to processes without the
       system going into swap.
       This is calculated by summing different memory values depending
       on the platform and it is supposed to be used to monitor actual
       memory usage in a cross platform fashion.

     - percent:
       the percentage usage calculated as (total - available) / total * 100

     - used:
        memory used, calculated differently depending on the platform and
        designed for informational purposes only:
        macOS: active + wired
        BSD: active + wired + cached
        Linux: total - free

     - free:
       memory not being used at all (zeroed) that is readily available;
       note that this doesn't reflect the actual memory available
       (use 'available' instead)

    Platform-specific fields:

     - active (UNIX):
       memory currently in use or very recently used, and so it is in RAM.

     - inactive (UNIX):
       memory that is marked as not used.

     - buffers (BSD, Linux):
       cache for things like file system metadata.

     - cached (BSD, macOS):
       cache for various things.

     - wired (macOS, BSD):
       memory that is marked to always stay in RAM. It is never moved to disk.

     - shared (BSD):
       memory that may be simultaneously accessed by multiple processes.

    The sum of 'used' and 'available' does not necessarily equal total.
    On Windows 'available' and 'free' are the same.
    """
    global _TOTAL_PHYMEM
    ret = _psplatform.virtual_memory()
    # 023597.python.init.line2035.comment cached for later use in Process.memory_percent()
    _TOTAL_PHYMEM = ret.total
    return ret


def swap_memory():
    """Return system swap memory statistics as a namedtuple including
    the following fields:

     - total:   total swap memory in bytes
     - used:    used swap memory in bytes
     - free:    free swap memory in bytes
     - percent: the percentage usage
     - sin:     no. of bytes the system has swapped in from disk (cumulative)
     - sout:    no. of bytes the system has swapped out from disk (cumulative)

    'sin' and 'sout' on Windows are meaningless and always set to 0.
    """
    return _psplatform.swap_memory()


# 023598.python.init.line2056.comment =====================================================================
# 023599.python.init.line2057.comment --- disks/partitions related functions
# 023600.python.init.line2058.comment =====================================================================


def disk_usage(path):
    """Return disk usage statistics about the given *path* as a
    namedtuple including total, used and free space expressed in bytes
    plus the percentage usage.
    """
    return _psplatform.disk_usage(path)


def disk_partitions(all=False):
    """Return mounted partitions as a list of
    (device, mountpoint, fstype, opts) namedtuple.
    'opts' field is a raw string separated by commas indicating mount
    options which may vary depending on the platform.

    If *all* parameter is False return physical devices only and ignore
    all others.
    """
    return _psplatform.disk_partitions(all)


def disk_io_counters(perdisk=False, nowrap=True):
    """Return system disk I/O statistics as a namedtuple including
    the following fields:

     - read_count:  number of reads
     - write_count: number of writes
     - read_bytes:  number of bytes read
     - write_bytes: number of bytes written
     - read_time:   time spent reading from disk (in ms)
     - write_time:  time spent writing to disk (in ms)

    Platform specific:

     - busy_time: (Linux, FreeBSD) time spent doing actual I/Os (in ms)
     - read_merged_count (Linux): number of merged reads
     - write_merged_count (Linux): number of merged writes

    If *perdisk* is True return the same information for every
    physical disk installed on the system as a dictionary
    with partition names as the keys and the namedtuple
    described above as the values.

    If *nowrap* is True it detects and adjust the numbers which overflow
    and wrap (restart from 0) and add "old value" to "new value" so that
    the returned numbers will always be increasing or remain the same,
    but never decrease.
    "disk_io_counters.cache_clear()" can be used to invalidate the
    cache.

    On recent Windows versions 'diskperf -y' command may need to be
    executed first otherwise this function won't find any disk.
    """
    kwargs = dict(perdisk=perdisk) if LINUX else {}
    rawdict = _psplatform.disk_io_counters(**kwargs)
    if not rawdict:
        return {} if perdisk else None
    if nowrap:
        rawdict = _wrap_numbers(rawdict, 'psutil.disk_io_counters')
    nt = getattr(_psplatform, "sdiskio", _common.sdiskio)
    if perdisk:
        for disk, fields in rawdict.items():
            rawdict[disk] = nt(*fields)
        return rawdict
    else:
        return nt(*(sum(x) for x in zip(*rawdict.values())))


disk_io_counters.cache_clear = functools.partial(
    _wrap_numbers.cache_clear, 'psutil.disk_io_counters'
)
disk_io_counters.cache_clear.__doc__ = "Clears nowrap argument cache"


# 023601.python.init.line2134.comment =====================================================================
# 023602.python.init.line2135.comment --- network related functions
# 023603.python.init.line2136.comment =====================================================================


def net_io_counters(pernic=False, nowrap=True):
    """Return network I/O statistics as a namedtuple including
    the following fields:

     - bytes_sent:   number of bytes sent
     - bytes_recv:   number of bytes received
     - packets_sent: number of packets sent
     - packets_recv: number of packets received
     - errin:        total number of errors while receiving
     - errout:       total number of errors while sending
     - dropin:       total number of incoming packets which were dropped
     - dropout:      total number of outgoing packets which were dropped
                     (always 0 on macOS and BSD)

    If *pernic* is True return the same information for every
    network interface installed on the system as a dictionary
    with network interface names as the keys and the namedtuple
    described above as the values.

    If *nowrap* is True it detects and adjust the numbers which overflow
    and wrap (restart from 0) and add "old value" to "new value" so that
    the returned numbers will always be increasing or remain the same,
    but never decrease.
    "net_io_counters.cache_clear()" can be used to invalidate the
    cache.
    """
    rawdict = _psplatform.net_io_counters()
    if not rawdict:
        return {} if pernic else None
    if nowrap:
        rawdict = _wrap_numbers(rawdict, 'psutil.net_io_counters')
    if pernic:
        for nic, fields in rawdict.items():
            rawdict[nic] = _common.snetio(*fields)
        return rawdict
    else:
        return _common.snetio(*[sum(x) for x in zip(*rawdict.values())])


net_io_counters.cache_clear = functools.partial(
    _wrap_numbers.cache_clear, 'psutil.net_io_counters'
)
net_io_counters.cache_clear.__doc__ = "Clears nowrap argument cache"


def net_connections(kind='inet'):
    """Return system-wide socket connections as a list of
    (fd, family, type, laddr, raddr, status, pid) namedtuples.
    In case of limited privileges 'fd' and 'pid' may be set to -1
    and None respectively.
    The *kind* parameter filters for connections that fit the
    following criteria:

    +------------+----------------------------------------------------+
    | Kind Value | Connections using                                  |
    +------------+----------------------------------------------------+
    | inet       | IPv4 and IPv6                                      |
    | inet4      | IPv4                                               |
    | inet6      | IPv6                                               |
    | tcp        | TCP                                                |
    | tcp4       | TCP over IPv4                                      |
    | tcp6       | TCP over IPv6                                      |
    | udp        | UDP                                                |
    | udp4       | UDP over IPv4                                      |
    | udp6       | UDP over IPv6                                      |
    | unix       | UNIX socket (both UDP and TCP protocols)           |
    | all        | the sum of all the possible families and protocols |
    +------------+----------------------------------------------------+

    On macOS this function requires root privileges.
    """
    _check_conn_kind(kind)
    return _psplatform.net_connections(kind)


def net_if_addrs():
    """Return the addresses associated to each NIC (network interface
    card) installed on the system as a dictionary whose keys are the
    NIC names and value is a list of namedtuples for each address
    assigned to the NIC. Each namedtuple includes 5 fields:

     - family: can be either socket.AF_INET, socket.AF_INET6 or
               psutil.AF_LINK, which refers to a MAC address.
     - address: is the primary address and it is always set.
     - netmask: and 'broadcast' and 'ptp' may be None.
     - ptp: stands for "point to point" and references the
            destination address on a point to point interface
            (typically a VPN).
     - broadcast: and *ptp* are mutually exclusive.

    Note: you can have more than one address of the same family
    associated with each interface.
    """
    rawlist = _psplatform.net_if_addrs()
    rawlist.sort(key=lambda x: x[1])  # sort by family
    ret = collections.defaultdict(list)
    for name, fam, addr, mask, broadcast, ptp in rawlist:
        try:
            fam = socket.AddressFamily(fam)
        except ValueError:
            if WINDOWS and fam == -1:
                fam = _psplatform.AF_LINK
            elif (
                hasattr(_psplatform, "AF_LINK") and fam == _psplatform.AF_LINK
            ):
                # 023605.python.init.line2244.comment Linux defines AF_LINK as an alias for AF_PACKET.
                # 023606.python.init.line2245.comment We re-set the family here so that repr(family)
                # 023607.python.init.line2246.comment will show AF_LINK rather than AF_PACKET
                fam = _psplatform.AF_LINK

        if fam == _psplatform.AF_LINK:
            # 023608.python.init.line2250.comment The underlying C function may return an incomplete MAC
            # 023609.python.init.line2251.comment address in which case we fill it with null bytes, see:
            # 023610.python.init.line2252.comment https://github.com/giampaolo/psutil/issues/786
            separator = ":" if POSIX else "-"
            while addr.count(separator) < 5:
                addr += f"{separator}00"

        nt = _common.snicaddr(fam, addr, mask, broadcast, ptp)

        # 023611.python.init.line2259.comment On Windows broadcast is None, so we determine it via
        # 023612.python.init.line2260.comment ipaddress module.
        if WINDOWS and fam in {socket.AF_INET, socket.AF_INET6}:
            try:
                broadcast = _common.broadcast_addr(nt)
            except Exception as err:  # noqa: BLE001
                debug(err)
            else:
                if broadcast is not None:
                    nt._replace(broadcast=broadcast)

        ret[name].append(nt)

    return dict(ret)


def net_if_stats():
    """Return information about each NIC (network interface card)
    installed on the system as a dictionary whose keys are the
    NIC names and value is a namedtuple with the following fields:

     - isup: whether the interface is up (bool)
     - duplex: can be either NIC_DUPLEX_FULL, NIC_DUPLEX_HALF or
               NIC_DUPLEX_UNKNOWN
     - speed: the NIC speed expressed in mega bits (MB); if it can't
              be determined (e.g. 'localhost') it will be set to 0.
     - mtu: the maximum transmission unit expressed in bytes.
    """
    return _psplatform.net_if_stats()


# 023614.python.init.line2290.comment =====================================================================
# 023615.python.init.line2291.comment --- sensors
# 023616.python.init.line2292.comment =====================================================================


# 023617.python.init.line2295.comment Linux, macOS
if hasattr(_psplatform, "sensors_temperatures"):

    def sensors_temperatures(fahrenheit=False):
        """Return hardware temperatures. Each entry is a namedtuple
        representing a certain hardware sensor (it may be a CPU, an
        hard disk or something else, depending on the OS and its
        configuration).
        All temperatures are expressed in celsius unless *fahrenheit*
        is set to True.
        """

        def convert(n):
            if n is not None:
                return (float(n) * 9 / 5) + 32 if fahrenheit else n

        ret = collections.defaultdict(list)
        rawdict = _psplatform.sensors_temperatures()

        for name, values in rawdict.items():
            while values:
                label, current, high, critical = values.pop(0)
                current = convert(current)
                high = convert(high)
                critical = convert(critical)

                if high and not critical:
                    critical = high
                elif critical and not high:
                    high = critical

                ret[name].append(
                    _common.shwtemp(label, current, high, critical)
                )

        return dict(ret)

    __all__.append("sensors_temperatures")


# 023618.python.init.line2335.comment Linux
if hasattr(_psplatform, "sensors_fans"):

    def sensors_fans():
        """Return fans speed. Each entry is a namedtuple
        representing a certain hardware sensor.
        All speed are expressed in RPM (rounds per minute).
        """
        return _psplatform.sensors_fans()

    __all__.append("sensors_fans")


# 023619.python.init.line2348.comment Linux, Windows, FreeBSD, macOS
if hasattr(_psplatform, "sensors_battery"):

    def sensors_battery():
        """Return battery information. If no battery is installed
        returns None.

         - percent: battery power left as a percentage.
         - secsleft: a rough approximation of how many seconds are left
                     before the battery runs out of power. May be
                     POWER_TIME_UNLIMITED or POWER_TIME_UNLIMITED.
         - power_plugged: True if the AC power cable is connected.
        """
        return _psplatform.sensors_battery()

    __all__.append("sensors_battery")


# 023620.python.init.line2366.comment =====================================================================
# 023621.python.init.line2367.comment --- other system related functions
# 023622.python.init.line2368.comment =====================================================================


def boot_time():
    """Return the system boot time expressed in seconds since the epoch
    (seconds since January 1, 1970, at midnight UTC). The returned
    value is based on the system clock, which means it may be affected
    by changes such as manual adjustments or time synchronization (e.g.
    NTP).
    """
    return _psplatform.boot_time()


def users():
    """Return users currently connected on the system as a list of
    namedtuples including the following fields.

     - user: the name of the user
     - terminal: the tty or pseudo-tty associated with the user, if any.
     - host: the host name associated with the entry, if any.
     - started: the creation time as a floating point number expressed in
       seconds since the epoch.
    """
    return _psplatform.users()


# 023623.python.init.line2394.comment =====================================================================
# 023624.python.init.line2395.comment --- Windows services
# 023625.python.init.line2396.comment =====================================================================


if WINDOWS:

    def win_service_iter():
        """Return a generator yielding a WindowsService instance for all
        Windows services installed.
        """
        return _psplatform.win_service_iter()

    def win_service_get(name):
        """Get a Windows service by *name*.
        Raise NoSuchProcess if no service with such name exists.
        """
        return _psplatform.win_service_get(name)


# 023626.python.init.line2414.comment =====================================================================


def _set_debug(value):
    """Enable or disable PSUTIL_DEBUG option, which prints debugging
    messages to stderr.
    """
    import psutil._common

    psutil._common.PSUTIL_DEBUG = bool(value)
    _psplatform.cext.set_debug(bool(value))


del memoize_when_activated
