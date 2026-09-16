# 024485.python.pssunos.line1.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 024486.python.pssunos.line2.comment Use of this source code is governed by a BSD-style license that can be
# 024487.python.pssunos.line3.comment found in the LICENSE file.

"""Sun OS Solaris platform implementation."""

import errno
import functools
import os
import socket
import subprocess
import sys
from collections import namedtuple
from socket import AF_INET

from . import _common
from . import _psposix
from . import _psutil_posix as cext_posix
from . import _psutil_sunos as cext
from ._common import AF_INET6
from ._common import ENCODING
from ._common import AccessDenied
from ._common import NoSuchProcess
from ._common import ZombieProcess
from ._common import debug
from ._common import get_procfs_path
from ._common import isfile_strict
from ._common import memoize_when_activated
from ._common import sockfam_to_enum
from ._common import socktype_to_enum
from ._common import usage_percent

__extra__all__ = ["CONN_IDLE", "CONN_BOUND", "PROCFS_PATH"]


# 024488.python.pssunos.line36.comment =====================================================================
# 024489.python.pssunos.line37.comment --- globals
# 024490.python.pssunos.line38.comment =====================================================================


PAGE_SIZE = cext_posix.getpagesize()
AF_LINK = cext_posix.AF_LINK
IS_64_BIT = sys.maxsize > 2**32

CONN_IDLE = "IDLE"
CONN_BOUND = "BOUND"

PROC_STATUSES = {
    cext.SSLEEP: _common.STATUS_SLEEPING,
    cext.SRUN: _common.STATUS_RUNNING,
    cext.SZOMB: _common.STATUS_ZOMBIE,
    cext.SSTOP: _common.STATUS_STOPPED,
    cext.SIDL: _common.STATUS_IDLE,
    cext.SONPROC: _common.STATUS_RUNNING,  # same as run
    cext.SWAIT: _common.STATUS_WAITING,
}

TCP_STATUSES = {
    cext.TCPS_ESTABLISHED: _common.CONN_ESTABLISHED,
    cext.TCPS_SYN_SENT: _common.CONN_SYN_SENT,
    cext.TCPS_SYN_RCVD: _common.CONN_SYN_RECV,
    cext.TCPS_FIN_WAIT_1: _common.CONN_FIN_WAIT1,
    cext.TCPS_FIN_WAIT_2: _common.CONN_FIN_WAIT2,
    cext.TCPS_TIME_WAIT: _common.CONN_TIME_WAIT,
    cext.TCPS_CLOSED: _common.CONN_CLOSE,
    cext.TCPS_CLOSE_WAIT: _common.CONN_CLOSE_WAIT,
    cext.TCPS_LAST_ACK: _common.CONN_LAST_ACK,
    cext.TCPS_LISTEN: _common.CONN_LISTEN,
    cext.TCPS_CLOSING: _common.CONN_CLOSING,
    cext.PSUTIL_CONN_NONE: _common.CONN_NONE,
    cext.TCPS_IDLE: CONN_IDLE,  # sunos specific
    cext.TCPS_BOUND: CONN_BOUND,  # sunos specific
}

proc_info_map = dict(
    ppid=0,
    rss=1,
    vms=2,
    create_time=3,
    nice=4,
    num_threads=5,
    status=6,
    ttynr=7,
    uid=8,
    euid=9,
    gid=10,
    egid=11,
)


# 024494.python.pssunos.line91.comment =====================================================================
# 024495.python.pssunos.line92.comment --- named tuples
# 024496.python.pssunos.line93.comment =====================================================================


# 024497.python.pssunos.line96.comment psutil.cpu_times()
scputimes = namedtuple('scputimes', ['user', 'system', 'idle', 'iowait'])
# 024498.python.pssunos.line98.comment psutil.cpu_times(percpu=True)
pcputimes = namedtuple(
    'pcputimes', ['user', 'system', 'children_user', 'children_system']
)
# 024499.python.pssunos.line102.comment psutil.virtual_memory()
svmem = namedtuple('svmem', ['total', 'available', 'percent', 'used', 'free'])
# 024500.python.pssunos.line104.comment psutil.Process.memory_info()
pmem = namedtuple('pmem', ['rss', 'vms'])
pfullmem = pmem
# 024501.python.pssunos.line107.comment psutil.Process.memory_maps(grouped=True)
pmmap_grouped = namedtuple(
    'pmmap_grouped', ['path', 'rss', 'anonymous', 'locked']
)
# 024502.python.pssunos.line111.comment psutil.Process.memory_maps(grouped=False)
pmmap_ext = namedtuple(
    'pmmap_ext', 'addr perms ' + ' '.join(pmmap_grouped._fields)
)


# 024503.python.pssunos.line117.comment =====================================================================
# 024504.python.pssunos.line118.comment --- memory
# 024505.python.pssunos.line119.comment =====================================================================


def virtual_memory():
    """Report virtual memory metrics."""
    # 024506.python.pssunos.line124.comment we could have done this with kstat, but IMHO this is good enough
    total = os.sysconf('SC_PHYS_PAGES') * PAGE_SIZE
    # 024507.python.pssunos.line126.comment note: there's no difference on Solaris
    free = avail = os.sysconf('SC_AVPHYS_PAGES') * PAGE_SIZE
    used = total - free
    percent = usage_percent(used, total, round_=1)
    return svmem(total, avail, percent, used, free)


def swap_memory():
    """Report swap memory metrics."""
    sin, sout = cext.swap_mem()
    # 024508.python.pssunos.line136.comment XXX
    # 024509.python.pssunos.line137.comment we are supposed to get total/free by doing so:
    # 024510.python.pssunos.line138.comment http://cvs.opensolaris.org/source/xref/onnv/onnv-gate/
    # 024511.python.pssunos.line139.comment usr/src/cmd/swap/swap.c
    # 024512.python.pssunos.line140.comment ...nevertheless I can't manage to obtain the same numbers as 'swap'
    # 024513.python.pssunos.line141.comment cmdline utility, so let's parse its output (sigh!)
    p = subprocess.Popen(
        [
            '/usr/bin/env',
            f"PATH=/usr/sbin:/sbin:{os.environ['PATH']}",
            'swap',
            '-l',
        ],
        stdout=subprocess.PIPE,
    )
    stdout, _ = p.communicate()
    stdout = stdout.decode(sys.stdout.encoding)
    if p.returncode != 0:
        msg = f"'swap -l' failed (retcode={p.returncode})"
        raise RuntimeError(msg)

    lines = stdout.strip().split('\n')[1:]
    if not lines:
        msg = 'no swap device(s) configured'
        raise RuntimeError(msg)
    total = free = 0
    for line in lines:
        line = line.split()
        t, f = line[3:5]
        total += int(int(t) * 512)
        free += int(int(f) * 512)
    used = total - free
    percent = usage_percent(used, total, round_=1)
    return _common.sswap(
        total, used, free, percent, sin * PAGE_SIZE, sout * PAGE_SIZE
    )


# 024514.python.pssunos.line174.comment =====================================================================
# 024515.python.pssunos.line175.comment --- CPU
# 024516.python.pssunos.line176.comment =====================================================================


def cpu_times():
    """Return system-wide CPU times as a named tuple."""
    ret = cext.per_cpu_times()
    return scputimes(*[sum(x) for x in zip(*ret)])


def per_cpu_times():
    """Return system per-CPU times as a list of named tuples."""
    ret = cext.per_cpu_times()
    return [scputimes(*x) for x in ret]


def cpu_count_logical():
    """Return the number of logical CPUs in the system."""
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        # 024517.python.pssunos.line196.comment mimic os.cpu_count() behavior
        return None


def cpu_count_cores():
    """Return the number of CPU cores in the system."""
    return cext.cpu_count_cores()


def cpu_stats():
    """Return various CPU stats as a named tuple."""
    ctx_switches, interrupts, syscalls, _traps = cext.cpu_stats()
    soft_interrupts = 0
    return _common.scpustats(
        ctx_switches, interrupts, soft_interrupts, syscalls
    )


# 024518.python.pssunos.line214.comment =====================================================================
# 024519.python.pssunos.line215.comment --- disks
# 024520.python.pssunos.line216.comment =====================================================================


disk_io_counters = cext.disk_io_counters
disk_usage = _psposix.disk_usage


def disk_partitions(all=False):
    """Return system disk partitions."""
    # 024521.python.pssunos.line225.comment TODO - the filtering logic should be better checked so that
    # 024522.python.pssunos.line226.comment it tries to reflect 'df' as much as possible
    retlist = []
    partitions = cext.disk_partitions()
    for partition in partitions:
        device, mountpoint, fstype, opts = partition
        if device == 'none':
            device = ''
        if not all:
            # 024523.python.pssunos.line234.comment Differently from, say, Linux, we don't have a list of
            # 024524.python.pssunos.line235.comment common fs types so the best we can do, AFAIK, is to
            # 024525.python.pssunos.line236.comment filter by filesystem having a total size > 0.
            try:
                if not disk_usage(mountpoint).total:
                    continue
            except OSError as err:
                # 024526.python.pssunos.line241.comment https://github.com/giampaolo/psutil/issues/1674
                debug(f"skipping {mountpoint!r}: {err}")
                continue
        ntuple = _common.sdiskpart(device, mountpoint, fstype, opts)
        retlist.append(ntuple)
    return retlist


# 024527.python.pssunos.line249.comment =====================================================================
# 024528.python.pssunos.line250.comment --- network
# 024529.python.pssunos.line251.comment =====================================================================


net_io_counters = cext.net_io_counters
net_if_addrs = cext_posix.net_if_addrs


def net_connections(kind, _pid=-1):
    """Return socket connections.  If pid == -1 return system-wide
    connections (as opposed to connections opened by one process only).
    Only INET sockets are returned (UNIX are not).
    """
    families, types = _common.conn_tmap[kind]
    rawlist = cext.net_connections(_pid)
    ret = set()
    for item in rawlist:
        fd, fam, type_, laddr, raddr, status, pid = item
        if fam not in families:
            continue
        if type_ not in types:
            continue
        # 024530.python.pssunos.line272.comment TODO: refactor and use _common.conn_to_ntuple.
        if fam in {AF_INET, AF_INET6}:
            if laddr:
                laddr = _common.addr(*laddr)
            if raddr:
                raddr = _common.addr(*raddr)
        status = TCP_STATUSES[status]
        fam = sockfam_to_enum(fam)
        type_ = socktype_to_enum(type_)
        if _pid == -1:
            nt = _common.sconn(fd, fam, type_, laddr, raddr, status, pid)
        else:
            nt = _common.pconn(fd, fam, type_, laddr, raddr, status)
        ret.add(nt)
    return list(ret)


def net_if_stats():
    """Get NIC stats (isup, duplex, speed, mtu)."""
    ret = cext.net_if_stats()
    for name, items in ret.items():
        isup, duplex, speed, mtu = items
        if hasattr(_common, 'NicDuplex'):
            duplex = _common.NicDuplex(duplex)
        ret[name] = _common.snicstats(isup, duplex, speed, mtu, '')
    return ret


# 024531.python.pssunos.line300.comment =====================================================================
# 024532.python.pssunos.line301.comment --- other system functions
# 024533.python.pssunos.line302.comment =====================================================================


def boot_time():
    """The system boot time expressed in seconds since the epoch."""
    return cext.boot_time()


def users():
    """Return currently connected users as a list of namedtuples."""
    retlist = []
    rawlist = cext_posix.users()
    localhost = (':0.0', ':0')
    for item in rawlist:
        user, tty, hostname, tstamp, user_process, pid = item
        # 024534.python.pssunos.line317.comment note: the underlying C function includes entries about
        # 024535.python.pssunos.line318.comment system boot, run level and others.  We might want
        # 024536.python.pssunos.line319.comment to use them in the future.
        if not user_process:
            continue
        if hostname in localhost:
            hostname = 'localhost'
        nt = _common.suser(user, tty, hostname, tstamp, pid)
        retlist.append(nt)
    return retlist


# 024537.python.pssunos.line329.comment =====================================================================
# 024538.python.pssunos.line330.comment --- processes
# 024539.python.pssunos.line331.comment =====================================================================


def pids():
    """Returns a list of PIDs currently running on the system."""
    path = get_procfs_path().encode(ENCODING)
    return [int(x) for x in os.listdir(path) if x.isdigit()]


def pid_exists(pid):
    """Check for the existence of a unix pid."""
    return _psposix.pid_exists(pid)


def wrap_exceptions(fun):
    """Call callable into a try/except clause and translate ENOENT,
    EACCES and EPERM in NoSuchProcess or AccessDenied exceptions.
    """

    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        pid, ppid, name = self.pid, self._ppid, self._name
        try:
            return fun(self, *args, **kwargs)
        except (FileNotFoundError, ProcessLookupError) as err:
            # 024540.python.pssunos.line356.comment ENOENT (no such file or directory) gets raised on open().
            # 024541.python.pssunos.line357.comment ESRCH (no such process) can get raised on read() if
            # 024542.python.pssunos.line358.comment process is gone in meantime.
            if not pid_exists(pid):
                raise NoSuchProcess(pid, name) from err
            raise ZombieProcess(pid, name, ppid) from err
        except PermissionError as err:
            raise AccessDenied(pid, name) from err
        except OSError as err:
            if pid == 0:
                if 0 in pids():
                    raise AccessDenied(pid, name) from err
                raise
            raise

    return wrapper


class Process:
    """Wrapper class around underlying C implementation."""

    __slots__ = ["_cache", "_name", "_ppid", "_procfs_path", "pid"]

    def __init__(self, pid):
        self.pid = pid
        self._name = None
        self._ppid = None
        self._procfs_path = get_procfs_path()

    def _assert_alive(self):
        """Raise NSP if the process disappeared on us."""
        # 024543.python.pssunos.line387.comment For those C function who do not raise NSP, possibly returning
        # 024544.python.pssunos.line388.comment incorrect or incomplete result.
        os.stat(f"{self._procfs_path}/{self.pid}")

    def oneshot_enter(self):
        self._proc_name_and_args.cache_activate(self)
        self._proc_basic_info.cache_activate(self)
        self._proc_cred.cache_activate(self)

    def oneshot_exit(self):
        self._proc_name_and_args.cache_deactivate(self)
        self._proc_basic_info.cache_deactivate(self)
        self._proc_cred.cache_deactivate(self)

    @wrap_exceptions
    @memoize_when_activated
    def _proc_name_and_args(self):
        return cext.proc_name_and_args(self.pid, self._procfs_path)

    @wrap_exceptions
    @memoize_when_activated
    def _proc_basic_info(self):
        if self.pid == 0 and not os.path.exists(
            f"{self._procfs_path}/{self.pid}/psinfo"
        ):
            raise AccessDenied(self.pid)
        ret = cext.proc_basic_info(self.pid, self._procfs_path)
        assert len(ret) == len(proc_info_map)
        return ret

    @wrap_exceptions
    @memoize_when_activated
    def _proc_cred(self):
        return cext.proc_cred(self.pid, self._procfs_path)

    @wrap_exceptions
    def name(self):
        # 024545.python.pssunos.line424.comment note: max len == 15
        return self._proc_name_and_args()[0]

    @wrap_exceptions
    def exe(self):
        try:
            return os.readlink(f"{self._procfs_path}/{self.pid}/path/a.out")
        except OSError:
            pass  # continue and guess the exe name from the cmdline
        # 024547.python.pssunos.line433.comment Will be guessed later from cmdline but we want to explicitly
        # 024548.python.pssunos.line434.comment invoke cmdline here in order to get an AccessDenied
        # 024549.python.pssunos.line435.comment exception if the user has not enough privileges.
        self.cmdline()
        return ""

    @wrap_exceptions
    def cmdline(self):
        return self._proc_name_and_args()[1].split(' ')

    @wrap_exceptions
    def environ(self):
        return cext.proc_environ(self.pid, self._procfs_path)

    @wrap_exceptions
    def create_time(self):
        return self._proc_basic_info()[proc_info_map['create_time']]

    @wrap_exceptions
    def num_threads(self):
        return self._proc_basic_info()[proc_info_map['num_threads']]

    @wrap_exceptions
    def nice_get(self):
        # 024550.python.pssunos.line457.comment Note #1: getpriority(3) doesn't work for realtime processes.
        # 024551.python.pssunos.line458.comment Psinfo is what ps uses, see:
        # 024552.python.pssunos.line459.comment https://github.com/giampaolo/psutil/issues/1194
        return self._proc_basic_info()[proc_info_map['nice']]

    @wrap_exceptions
    def nice_set(self, value):
        if self.pid in {2, 3}:
            # 024553.python.pssunos.line465.comment Special case PIDs: internally setpriority(3) return ESRCH
            # 024554.python.pssunos.line466.comment (no such process), no matter what.
            # 024555.python.pssunos.line467.comment The process actually exists though, as it has a name,
            # 024556.python.pssunos.line468.comment creation time, etc.
            raise AccessDenied(self.pid, self._name)
        return cext_posix.setpriority(self.pid, value)

    @wrap_exceptions
    def ppid(self):
        self._ppid = self._proc_basic_info()[proc_info_map['ppid']]
        return self._ppid

    @wrap_exceptions
    def uids(self):
        try:
            real, effective, saved, _, _, _ = self._proc_cred()
        except AccessDenied:
            real = self._proc_basic_info()[proc_info_map['uid']]
            effective = self._proc_basic_info()[proc_info_map['euid']]
            saved = None
        return _common.puids(real, effective, saved)

    @wrap_exceptions
    def gids(self):
        try:
            _, _, _, real, effective, saved = self._proc_cred()
        except AccessDenied:
            real = self._proc_basic_info()[proc_info_map['gid']]
            effective = self._proc_basic_info()[proc_info_map['egid']]
            saved = None
        return _common.puids(real, effective, saved)

    @wrap_exceptions
    def cpu_times(self):
        try:
            times = cext.proc_cpu_times(self.pid, self._procfs_path)
        except OSError as err:
            if err.errno == errno.EOVERFLOW and not IS_64_BIT:
                # 024557.python.pssunos.line503.comment We may get here if we attempt to query a 64bit process
                # 024558.python.pssunos.line504.comment with a 32bit python.
                # 024559.python.pssunos.line505.comment Error originates from read() and also tools like "cat"
                # 024560.python.pssunos.line506.comment fail in the same way (!).
                # 024561.python.pssunos.line507.comment Since there simply is no way to determine CPU times we
                # 024562.python.pssunos.line508.comment return 0.0 as a fallback. See:
                # 024563.python.pssunos.line509.comment https://github.com/giampaolo/psutil/issues/857
                times = (0.0, 0.0, 0.0, 0.0)
            else:
                raise
        return _common.pcputimes(*times)

    @wrap_exceptions
    def cpu_num(self):
        return cext.proc_cpu_num(self.pid, self._procfs_path)

    @wrap_exceptions
    def terminal(self):
        procfs_path = self._procfs_path
        hit_enoent = False
        tty = wrap_exceptions(self._proc_basic_info()[proc_info_map['ttynr']])
        if tty != cext.PRNODEV:
            for x in (0, 1, 2, 255):
                try:
                    return os.readlink(f"{procfs_path}/{self.pid}/path/{x}")
                except FileNotFoundError:
                    hit_enoent = True
                    continue
        if hit_enoent:
            self._assert_alive()

    @wrap_exceptions
    def cwd(self):
        # 024564.python.pssunos.line536.comment /proc/PID/path/cwd may not be resolved by readlink() even if
        # 024565.python.pssunos.line537.comment it exists (ls shows it). If that's the case and the process
        # 024566.python.pssunos.line538.comment is still alive return None (we can return None also on BSD).
        # 024567.python.pssunos.line539.comment Reference: https://groups.google.com/g/comp.unix.solaris/c/tcqvhTNFCAs
        procfs_path = self._procfs_path
        try:
            return os.readlink(f"{procfs_path}/{self.pid}/path/cwd")
        except FileNotFoundError:
            os.stat(f"{procfs_path}/{self.pid}")  # raise NSP or AD
            return ""

    @wrap_exceptions
    def memory_info(self):
        ret = self._proc_basic_info()
        rss = ret[proc_info_map['rss']] * 1024
        vms = ret[proc_info_map['vms']] * 1024
        return pmem(rss, vms)

    memory_full_info = memory_info

    @wrap_exceptions
    def status(self):
        code = self._proc_basic_info()[proc_info_map['status']]
        # 024569.python.pssunos.line559.comment XXX is '?' legit? (we're not supposed to return it anyway)
        return PROC_STATUSES.get(code, '?')

    @wrap_exceptions
    def threads(self):
        procfs_path = self._procfs_path
        ret = []
        tids = os.listdir(f"{procfs_path}/{self.pid}/lwp")
        hit_enoent = False
        for tid in tids:
            tid = int(tid)
            try:
                utime, stime = cext.query_process_thread(
                    self.pid, tid, procfs_path
                )
            except OSError as err:
                if err.errno == errno.EOVERFLOW and not IS_64_BIT:
                    # 024570.python.pssunos.line576.comment We may get here if we attempt to query a 64bit process
                    # 024571.python.pssunos.line577.comment with a 32bit python.
                    # 024572.python.pssunos.line578.comment Error originates from read() and also tools like "cat"
                    # 024573.python.pssunos.line579.comment fail in the same way (!).
                    # 024574.python.pssunos.line580.comment Since there simply is no way to determine CPU times we
                    # 024575.python.pssunos.line581.comment return 0.0 as a fallback. See:
                    # 024576.python.pssunos.line582.comment https://github.com/giampaolo/psutil/issues/857
                    continue
                # 024577.python.pssunos.line584.comment ENOENT == thread gone in meantime
                if err.errno == errno.ENOENT:
                    hit_enoent = True
                    continue
                raise
            else:
                nt = _common.pthread(tid, utime, stime)
                ret.append(nt)
        if hit_enoent:
            self._assert_alive()
        return ret

    @wrap_exceptions
    def open_files(self):
        retlist = []
        hit_enoent = False
        procfs_path = self._procfs_path
        pathdir = f"{procfs_path}/{self.pid}/path"
        for fd in os.listdir(f"{procfs_path}/{self.pid}/fd"):
            path = os.path.join(pathdir, fd)
            if os.path.islink(path):
                try:
                    file = os.readlink(path)
                except FileNotFoundError:
                    hit_enoent = True
                    continue
                else:
                    if isfile_strict(file):
                        retlist.append(_common.popenfile(file, int(fd)))
        if hit_enoent:
            self._assert_alive()
        return retlist

    def _get_unix_sockets(self, pid):
        """Get UNIX sockets used by process by parsing 'pfiles' output."""
        # 024578.python.pssunos.line619.comment TODO: rewrite this in C (...but the damn netstat source code
        # 024579.python.pssunos.line620.comment does not include this part! Argh!!)
        cmd = ["pfiles", str(pid)]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        stdout, stderr = (
            x.decode(sys.stdout.encoding) for x in (stdout, stderr)
        )
        if p.returncode != 0:
            if 'permission denied' in stderr.lower():
                raise AccessDenied(self.pid, self._name)
            if 'no such process' in stderr.lower():
                raise NoSuchProcess(self.pid, self._name)
            msg = f"{cmd!r} command error\n{stderr}"
            raise RuntimeError(msg)

        lines = stdout.split('\n')[2:]
        for i, line in enumerate(lines):
            line = line.lstrip()
            if line.startswith('sockname: AF_UNIX'):
                path = line.split(' ', 2)[2]
                type = lines[i - 2].strip()
                if type == 'SOCK_STREAM':
                    type = socket.SOCK_STREAM
                elif type == 'SOCK_DGRAM':
                    type = socket.SOCK_DGRAM
                else:
                    type = -1
                yield (-1, socket.AF_UNIX, type, path, "", _common.CONN_NONE)

    @wrap_exceptions
    def net_connections(self, kind='inet'):
        ret = net_connections(kind, _pid=self.pid)
        # 024580.python.pssunos.line654.comment The underlying C implementation retrieves all OS connections
        # 024581.python.pssunos.line655.comment and filters them by PID.  At this point we can't tell whether
        # 024582.python.pssunos.line656.comment an empty list means there were no connections for process or
        # 024583.python.pssunos.line657.comment process is no longer active so we force NSP in case the PID
        # 024584.python.pssunos.line658.comment is no longer there.
        if not ret:
            # 024585.python.pssunos.line660.comment will raise NSP if process is gone
            os.stat(f"{self._procfs_path}/{self.pid}")

        # 024586.python.pssunos.line663.comment UNIX sockets
        if kind in {'all', 'unix'}:
            ret.extend([
                _common.pconn(*conn)
                for conn in self._get_unix_sockets(self.pid)
            ])
        return ret

    nt_mmap_grouped = namedtuple('mmap', 'path rss anon locked')
    nt_mmap_ext = namedtuple('mmap', 'addr perms path rss anon locked')

    @wrap_exceptions
    def memory_maps(self):
        def toaddr(start, end):
            return "{}-{}".format(
                hex(start)[2:].strip('L'), hex(end)[2:].strip('L')
            )

        procfs_path = self._procfs_path
        retlist = []
        try:
            rawlist = cext.proc_memory_maps(self.pid, procfs_path)
        except OSError as err:
            if err.errno == errno.EOVERFLOW and not IS_64_BIT:
                # 024587.python.pssunos.line687.comment We may get here if we attempt to query a 64bit process
                # 024588.python.pssunos.line688.comment with a 32bit python.
                # 024589.python.pssunos.line689.comment Error originates from read() and also tools like "cat"
                # 024590.python.pssunos.line690.comment fail in the same way (!).
                # 024591.python.pssunos.line691.comment Since there simply is no way to determine CPU times we
                # 024592.python.pssunos.line692.comment return 0.0 as a fallback. See:
                # 024593.python.pssunos.line693.comment https://github.com/giampaolo/psutil/issues/857
                return []
            else:
                raise
        hit_enoent = False
        for item in rawlist:
            addr, addrsize, perm, name, rss, anon, locked = item
            addr = toaddr(addr, addrsize)
            if not name.startswith('['):
                try:
                    name = os.readlink(f"{procfs_path}/{self.pid}/path/{name}")
                except OSError as err:
                    if err.errno == errno.ENOENT:
                        # 024594.python.pssunos.line706.comment sometimes the link may not be resolved by
                        # 024595.python.pssunos.line707.comment readlink() even if it exists (ls shows it).
                        # 024596.python.pssunos.line708.comment If that's the case we just return the
                        # 024597.python.pssunos.line709.comment unresolved link path.
                        # 024598.python.pssunos.line710.comment This seems an inconsistency with /proc similar
                        # 024599.python.pssunos.line711.comment to: http://goo.gl/55XgO
                        name = f"{procfs_path}/{self.pid}/path/{name}"
                        hit_enoent = True
                    else:
                        raise
            retlist.append((addr, perm, name, rss, anon, locked))
        if hit_enoent:
            self._assert_alive()
        return retlist

    @wrap_exceptions
    def num_fds(self):
        return len(os.listdir(f"{self._procfs_path}/{self.pid}/fd"))

    @wrap_exceptions
    def num_ctx_switches(self):
        return _common.pctxsw(
            *cext.proc_num_ctx_switches(self.pid, self._procfs_path)
        )

    @wrap_exceptions
    def wait(self, timeout=None):
        return _psposix.wait_pid(self.pid, timeout, self._name)
