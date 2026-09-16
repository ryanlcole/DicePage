# 023742.python.psaix.line1.comment Copyright (c) 2009, Giampaolo Rodola'
# 023743.python.psaix.line2.comment Copyright (c) 2017, Arnon Yaari
# 023744.python.psaix.line3.comment All rights reserved.
# 023745.python.psaix.line4.comment Use of this source code is governed by a BSD-style license that can be
# 023746.python.psaix.line5.comment found in the LICENSE file.

"""AIX platform implementation."""

import functools
import glob
import os
import re
import subprocess
import sys
from collections import namedtuple

from . import _common
from . import _psposix
from . import _psutil_aix as cext
from . import _psutil_posix as cext_posix
from ._common import NIC_DUPLEX_FULL
from ._common import NIC_DUPLEX_HALF
from ._common import NIC_DUPLEX_UNKNOWN
from ._common import AccessDenied
from ._common import NoSuchProcess
from ._common import ZombieProcess
from ._common import conn_to_ntuple
from ._common import get_procfs_path
from ._common import memoize_when_activated
from ._common import usage_percent

__extra__all__ = ["PROCFS_PATH"]


# 023747.python.psaix.line35.comment =====================================================================
# 023748.python.psaix.line36.comment --- globals
# 023749.python.psaix.line37.comment =====================================================================


HAS_THREADS = hasattr(cext, "proc_threads")
HAS_NET_IO_COUNTERS = hasattr(cext, "net_io_counters")
HAS_PROC_IO_COUNTERS = hasattr(cext, "proc_io_counters")

PAGE_SIZE = cext_posix.getpagesize()
AF_LINK = cext_posix.AF_LINK

PROC_STATUSES = {
    cext.SIDL: _common.STATUS_IDLE,
    cext.SZOMB: _common.STATUS_ZOMBIE,
    cext.SACTIVE: _common.STATUS_RUNNING,
    cext.SSWAP: _common.STATUS_RUNNING,  # TODO what status is this?
    cext.SSTOP: _common.STATUS_STOPPED,
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
)


# 023751.python.psaix.line82.comment =====================================================================
# 023752.python.psaix.line83.comment --- named tuples
# 023753.python.psaix.line84.comment =====================================================================


# 023754.python.psaix.line87.comment psutil.Process.memory_info()
pmem = namedtuple('pmem', ['rss', 'vms'])
# 023755.python.psaix.line89.comment psutil.Process.memory_full_info()
pfullmem = pmem
# 023756.python.psaix.line91.comment psutil.Process.cpu_times()
scputimes = namedtuple('scputimes', ['user', 'system', 'idle', 'iowait'])
# 023757.python.psaix.line93.comment psutil.virtual_memory()
svmem = namedtuple('svmem', ['total', 'available', 'percent', 'used', 'free'])


# 023758.python.psaix.line97.comment =====================================================================
# 023759.python.psaix.line98.comment --- memory
# 023760.python.psaix.line99.comment =====================================================================


def virtual_memory():
    total, avail, free, _pinned, inuse = cext.virtual_mem()
    percent = usage_percent((total - avail), total, round_=1)
    return svmem(total, avail, percent, inuse, free)


def swap_memory():
    """Swap system memory as a (total, used, free, sin, sout) tuple."""
    total, free, sin, sout = cext.swap_mem()
    used = total - free
    percent = usage_percent(used, total, round_=1)
    return _common.sswap(total, used, free, percent, sin, sout)


# 023761.python.psaix.line116.comment =====================================================================
# 023762.python.psaix.line117.comment --- CPU
# 023763.python.psaix.line118.comment =====================================================================


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
        # 023764.python.psaix.line138.comment mimic os.cpu_count() behavior
        return None


def cpu_count_cores():
    cmd = ["lsdev", "-Cc", "processor"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout, stderr = (x.decode(sys.stdout.encoding) for x in (stdout, stderr))
    if p.returncode != 0:
        msg = f"{cmd!r} command error\n{stderr}"
        raise RuntimeError(msg)
    processors = stdout.strip().splitlines()
    return len(processors) or None


def cpu_stats():
    """Return various CPU stats as a named tuple."""
    ctx_switches, interrupts, soft_interrupts, syscalls = cext.cpu_stats()
    return _common.scpustats(
        ctx_switches, interrupts, soft_interrupts, syscalls
    )


# 023765.python.psaix.line162.comment =====================================================================
# 023766.python.psaix.line163.comment --- disks
# 023767.python.psaix.line164.comment =====================================================================


disk_io_counters = cext.disk_io_counters
disk_usage = _psposix.disk_usage


def disk_partitions(all=False):
    """Return system disk partitions."""
    # 023768.python.psaix.line173.comment TODO - the filtering logic should be better checked so that
    # 023769.python.psaix.line174.comment it tries to reflect 'df' as much as possible
    retlist = []
    partitions = cext.disk_partitions()
    for partition in partitions:
        device, mountpoint, fstype, opts = partition
        if device == 'none':
            device = ''
        if not all:
            # 023770.python.psaix.line182.comment Differently from, say, Linux, we don't have a list of
            # 023771.python.psaix.line183.comment common fs types so the best we can do, AFAIK, is to
            # 023772.python.psaix.line184.comment filter by filesystem having a total size > 0.
            if not disk_usage(mountpoint).total:
                continue
        ntuple = _common.sdiskpart(device, mountpoint, fstype, opts)
        retlist.append(ntuple)
    return retlist


# 023773.python.psaix.line192.comment =====================================================================
# 023774.python.psaix.line193.comment --- network
# 023775.python.psaix.line194.comment =====================================================================


net_if_addrs = cext_posix.net_if_addrs

if HAS_NET_IO_COUNTERS:
    net_io_counters = cext.net_io_counters


def net_connections(kind, _pid=-1):
    """Return socket connections.  If pid == -1 return system-wide
    connections (as opposed to connections opened by one process only).
    """
    families, types = _common.conn_tmap[kind]
    rawlist = cext.net_connections(_pid)
    ret = []
    for item in rawlist:
        fd, fam, type_, laddr, raddr, status, pid = item
        if fam not in families:
            continue
        if type_ not in types:
            continue
        nt = conn_to_ntuple(
            fd,
            fam,
            type_,
            laddr,
            raddr,
            status,
            TCP_STATUSES,
            pid=pid if _pid == -1 else None,
        )
        ret.append(nt)
    return ret


def net_if_stats():
    """Get NIC stats (isup, duplex, speed, mtu)."""
    duplex_map = {"Full": NIC_DUPLEX_FULL, "Half": NIC_DUPLEX_HALF}
    names = {x[0] for x in net_if_addrs()}
    ret = {}
    for name in names:
        mtu = cext_posix.net_if_mtu(name)
        flags = cext_posix.net_if_flags(name)

        # 023776.python.psaix.line239.comment try to get speed and duplex
        # 023777.python.psaix.line240.comment TODO: rewrite this in C (entstat forks, so use truss -f to follow.
        # 023778.python.psaix.line241.comment looks like it is using an undocumented ioctl?)
        duplex = ""
        speed = 0
        p = subprocess.Popen(
            ["/usr/bin/entstat", "-d", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        stdout, stderr = (
            x.decode(sys.stdout.encoding) for x in (stdout, stderr)
        )
        if p.returncode == 0:
            re_result = re.search(
                r"Running: (\d+) Mbps.*?(\w+) Duplex", stdout
            )
            if re_result is not None:
                speed = int(re_result.group(1))
                duplex = re_result.group(2)

        output_flags = ','.join(flags)
        isup = 'running' in flags
        duplex = duplex_map.get(duplex, NIC_DUPLEX_UNKNOWN)
        ret[name] = _common.snicstats(isup, duplex, speed, mtu, output_flags)
    return ret


# 023779.python.psaix.line268.comment =====================================================================
# 023780.python.psaix.line269.comment --- other system functions
# 023781.python.psaix.line270.comment =====================================================================


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
        # 023782.python.psaix.line285.comment note: the underlying C function includes entries about
        # 023783.python.psaix.line286.comment system boot, run level and others.  We might want
        # 023784.python.psaix.line287.comment to use them in the future.
        if not user_process:
            continue
        if hostname in localhost:
            hostname = 'localhost'
        nt = _common.suser(user, tty, hostname, tstamp, pid)
        retlist.append(nt)
    return retlist


# 023785.python.psaix.line297.comment =====================================================================
# 023786.python.psaix.line298.comment --- processes
# 023787.python.psaix.line299.comment =====================================================================


def pids():
    """Returns a list of PIDs currently running on the system."""
    return [int(x) for x in os.listdir(get_procfs_path()) if x.isdigit()]


def pid_exists(pid):
    """Check for the existence of a unix pid."""
    return os.path.exists(os.path.join(get_procfs_path(), str(pid), "psinfo"))


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
            # 023788.python.psaix.line323.comment ENOENT (no such file or directory) gets raised on open().
            # 023789.python.psaix.line324.comment ESRCH (no such process) can get raised on read() if
            # 023790.python.psaix.line325.comment process is gone in meantime.
            if not pid_exists(pid):
                raise NoSuchProcess(pid, name) from err
            raise ZombieProcess(pid, name, ppid) from err
        except PermissionError as err:
            raise AccessDenied(pid, name) from err

    return wrapper


class Process:
    """Wrapper class around underlying C implementation."""

    __slots__ = ["_cache", "_name", "_ppid", "_procfs_path", "pid"]

    def __init__(self, pid):
        self.pid = pid
        self._name = None
        self._ppid = None
        self._procfs_path = get_procfs_path()

    def oneshot_enter(self):
        self._proc_basic_info.cache_activate(self)
        self._proc_cred.cache_activate(self)

    def oneshot_exit(self):
        self._proc_basic_info.cache_deactivate(self)
        self._proc_cred.cache_deactivate(self)

    @wrap_exceptions
    @memoize_when_activated
    def _proc_basic_info(self):
        return cext.proc_basic_info(self.pid, self._procfs_path)

    @wrap_exceptions
    @memoize_when_activated
    def _proc_cred(self):
        return cext.proc_cred(self.pid, self._procfs_path)

    @wrap_exceptions
    def name(self):
        if self.pid == 0:
            return "swapper"
        # 023791.python.psaix.line368.comment note: max 16 characters
        return cext.proc_name(self.pid, self._procfs_path).rstrip("\x00")

    @wrap_exceptions
    def exe(self):
        # 023792.python.psaix.line373.comment there is no way to get executable path in AIX other than to guess,
        # 023793.python.psaix.line374.comment and guessing is more complex than what's in the wrapping class
        cmdline = self.cmdline()
        if not cmdline:
            return ''
        exe = cmdline[0]
        if os.path.sep in exe:
            # 023794.python.psaix.line380.comment relative or absolute path
            if not os.path.isabs(exe):
                # 023795.python.psaix.line382.comment if cwd has changed, we're out of luck - this may be wrong!
                exe = os.path.abspath(os.path.join(self.cwd(), exe))
            if (
                os.path.isabs(exe)
                and os.path.isfile(exe)
                and os.access(exe, os.X_OK)
            ):
                return exe
            # 023796.python.psaix.line390.comment not found, move to search in PATH using basename only
            exe = os.path.basename(exe)
        # 023797.python.psaix.line392.comment search for exe name PATH
        for path in os.environ["PATH"].split(":"):
            possible_exe = os.path.abspath(os.path.join(path, exe))
            if os.path.isfile(possible_exe) and os.access(
                possible_exe, os.X_OK
            ):
                return possible_exe
        return ''

    @wrap_exceptions
    def cmdline(self):
        return cext.proc_args(self.pid)

    @wrap_exceptions
    def environ(self):
        return cext.proc_environ(self.pid)

    @wrap_exceptions
    def create_time(self):
        return self._proc_basic_info()[proc_info_map['create_time']]

    @wrap_exceptions
    def num_threads(self):
        return self._proc_basic_info()[proc_info_map['num_threads']]

    if HAS_THREADS:

        @wrap_exceptions
        def threads(self):
            rawlist = cext.proc_threads(self.pid)
            retlist = []
            for thread_id, utime, stime in rawlist:
                ntuple = _common.pthread(thread_id, utime, stime)
                retlist.append(ntuple)
            # 023798.python.psaix.line426.comment The underlying C implementation retrieves all OS threads
            # 023799.python.psaix.line427.comment and filters them by PID.  At this point we can't tell whether
            # 023800.python.psaix.line428.comment an empty list means there were no connections for process or
            # 023801.python.psaix.line429.comment process is no longer active so we force NSP in case the PID
            # 023802.python.psaix.line430.comment is no longer there.
            if not retlist:
                # 023803.python.psaix.line432.comment will raise NSP if process is gone
                os.stat(f"{self._procfs_path}/{self.pid}")
            return retlist

    @wrap_exceptions
    def net_connections(self, kind='inet'):
        ret = net_connections(kind, _pid=self.pid)
        # 023804.python.psaix.line439.comment The underlying C implementation retrieves all OS connections
        # 023805.python.psaix.line440.comment and filters them by PID.  At this point we can't tell whether
        # 023806.python.psaix.line441.comment an empty list means there were no connections for process or
        # 023807.python.psaix.line442.comment process is no longer active so we force NSP in case the PID
        # 023808.python.psaix.line443.comment is no longer there.
        if not ret:
            # 023809.python.psaix.line445.comment will raise NSP if process is gone
            os.stat(f"{self._procfs_path}/{self.pid}")
        return ret

    @wrap_exceptions
    def nice_get(self):
        return cext_posix.getpriority(self.pid)

    @wrap_exceptions
    def nice_set(self, value):
        return cext_posix.setpriority(self.pid, value)

    @wrap_exceptions
    def ppid(self):
        self._ppid = self._proc_basic_info()[proc_info_map['ppid']]
        return self._ppid

    @wrap_exceptions
    def uids(self):
        real, effective, saved, _, _, _ = self._proc_cred()
        return _common.puids(real, effective, saved)

    @wrap_exceptions
    def gids(self):
        _, _, _, real, effective, saved = self._proc_cred()
        return _common.puids(real, effective, saved)

    @wrap_exceptions
    def cpu_times(self):
        t = cext.proc_cpu_times(self.pid, self._procfs_path)
        return _common.pcputimes(*t)

    @wrap_exceptions
    def terminal(self):
        ttydev = self._proc_basic_info()[proc_info_map['ttynr']]
        # 023810.python.psaix.line480.comment convert from 64-bit dev_t to 32-bit dev_t and then map the device
        ttydev = ((ttydev & 0x0000FFFF00000000) >> 16) | (ttydev & 0xFFFF)
        # 023811.python.psaix.line482.comment try to match rdev of /dev/pts/* files ttydev
        for dev in glob.glob("/dev/**/*"):
            if os.stat(dev).st_rdev == ttydev:
                return dev
        return None

    @wrap_exceptions
    def cwd(self):
        procfs_path = self._procfs_path
        try:
            result = os.readlink(f"{procfs_path}/{self.pid}/cwd")
            return result.rstrip('/')
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
        # 023813.python.psaix.line510.comment XXX is '?' legit? (we're not supposed to return it anyway)
        return PROC_STATUSES.get(code, '?')

    def open_files(self):
        # 023814.python.psaix.line514.comment TODO rewrite without using procfiles (stat /proc/pid/fd/* and then
        # 023815.python.psaix.line515.comment find matching name of the inode)
        p = subprocess.Popen(
            ["/usr/bin/procfiles", "-n", str(self.pid)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        stdout, stderr = (
            x.decode(sys.stdout.encoding) for x in (stdout, stderr)
        )
        if "no such process" in stderr.lower():
            raise NoSuchProcess(self.pid, self._name)
        procfiles = re.findall(r"(\d+): S_IFREG.*name:(.*)\n", stdout)
        retlist = []
        for fd, path in procfiles:
            path = path.strip()
            if path.startswith("//"):
                path = path[1:]
            if path.lower() == "cannot be retrieved":
                continue
            retlist.append(_common.popenfile(path, int(fd)))
        return retlist

    @wrap_exceptions
    def num_fds(self):
        if self.pid == 0:  # no /proc/0/fd
            return 0
        return len(os.listdir(f"{self._procfs_path}/{self.pid}/fd"))

    @wrap_exceptions
    def num_ctx_switches(self):
        return _common.pctxsw(*cext.proc_num_ctx_switches(self.pid))

    @wrap_exceptions
    def wait(self, timeout=None):
        return _psposix.wait_pid(self.pid, timeout, self._name)

    if HAS_PROC_IO_COUNTERS:

        @wrap_exceptions
        def io_counters(self):
            try:
                rc, wc, rb, wb = cext.proc_io_counters(self.pid)
            except OSError as err:
                # 023817.python.psaix.line559.comment if process is terminated, proc_io_counters returns OSError
                # 023818.python.psaix.line560.comment instead of NSP
                if not pid_exists(self.pid):
                    raise NoSuchProcess(self.pid, self._name) from err
                raise
            return _common.pio(rc, wc, rb, wb)
