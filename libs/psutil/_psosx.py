# 024370.python.psosx.line1.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 024371.python.psosx.line2.comment Use of this source code is governed by a BSD-style license that can be
# 024372.python.psosx.line3.comment found in the LICENSE file.

"""macOS platform implementation."""

import errno
import functools
import os
from collections import namedtuple

from . import _common
from . import _psposix
from . import _psutil_osx as cext
from . import _psutil_posix as cext_posix
from ._common import AccessDenied
from ._common import NoSuchProcess
from ._common import ZombieProcess
from ._common import conn_tmap
from ._common import conn_to_ntuple
from ._common import debug
from ._common import isfile_strict
from ._common import memoize_when_activated
from ._common import parse_environ_block
from ._common import usage_percent

__extra__all__ = []


# 024373.python.psosx.line30.comment =====================================================================
# 024374.python.psosx.line31.comment --- globals
# 024375.python.psosx.line32.comment =====================================================================


PAGESIZE = cext_posix.getpagesize()
AF_LINK = cext_posix.AF_LINK

TCP_STATUSES = {
    cext.TCPS_ESTABLISHED: _common.CONN_ESTABLISHED,
    cext.TCPS_SYN_SENT: _common.CONN_SYN_SENT,
    cext.TCPS_SYN_RECEIVED: _common.CONN_SYN_RECV,
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

PROC_STATUSES = {
    cext.SIDL: _common.STATUS_IDLE,
    cext.SRUN: _common.STATUS_RUNNING,
    cext.SSLEEP: _common.STATUS_SLEEPING,
    cext.SSTOP: _common.STATUS_STOPPED,
    cext.SZOMB: _common.STATUS_ZOMBIE,
}

kinfo_proc_map = dict(
    ppid=0,
    ruid=1,
    euid=2,
    suid=3,
    rgid=4,
    egid=5,
    sgid=6,
    ttynr=7,
    ctime=8,
    status=9,
    name=10,
)

pidtaskinfo_map = dict(
    cpuutime=0,
    cpustime=1,
    rss=2,
    vms=3,
    pfaults=4,
    pageins=5,
    numthreads=6,
    volctxsw=7,
)


# 024376.python.psosx.line87.comment =====================================================================
# 024377.python.psosx.line88.comment --- named tuples
# 024378.python.psosx.line89.comment =====================================================================


# 024379.python.psosx.line92.comment fmt: off
# 024380.python.psosx.line93.comment psutil.cpu_times()
scputimes = namedtuple('scputimes', ['user', 'nice', 'system', 'idle'])
# 024381.python.psosx.line95.comment psutil.virtual_memory()
svmem = namedtuple(
    'svmem', ['total', 'available', 'percent', 'used', 'free',
              'active', 'inactive', 'wired'])
# 024382.python.psosx.line99.comment psutil.Process.memory_info()
pmem = namedtuple('pmem', ['rss', 'vms', 'pfaults', 'pageins'])
# 024383.python.psosx.line101.comment psutil.Process.memory_full_info()
pfullmem = namedtuple('pfullmem', pmem._fields + ('uss', ))
# 024384.python.psosx.line103.comment fmt: on


# 024385.python.psosx.line106.comment =====================================================================
# 024386.python.psosx.line107.comment --- memory
# 024387.python.psosx.line108.comment =====================================================================


def virtual_memory():
    """System virtual memory as a namedtuple."""
    total, active, inactive, wired, free, speculative = cext.virtual_mem()
    # 024388.python.psosx.line114.comment This is how Zabbix calculate avail and used mem:
    # 024389.python.psosx.line115.comment https://github.com/zabbix/zabbix/blob/master/src/libs/zbxsysinfo/osx/memory.c
    # 024390.python.psosx.line116.comment Also see: https://github.com/giampaolo/psutil/issues/1277
    avail = inactive + free
    used = active + wired
    # 024391.python.psosx.line119.comment This is NOT how Zabbix calculates free mem but it matches "free"
    # 024392.python.psosx.line120.comment cmdline utility.
    free -= speculative
    percent = usage_percent((total - avail), total, round_=1)
    return svmem(total, avail, percent, used, free, active, inactive, wired)


def swap_memory():
    """Swap system memory as a (total, used, free, sin, sout) tuple."""
    total, used, free, sin, sout = cext.swap_mem()
    percent = usage_percent(used, total, round_=1)
    return _common.sswap(total, used, free, percent, sin, sout)


# 024393.python.psosx.line133.comment =====================================================================
# 024394.python.psosx.line134.comment --- CPU
# 024395.python.psosx.line135.comment =====================================================================


def cpu_times():
    """Return system CPU times as a namedtuple."""
    user, nice, system, idle = cext.cpu_times()
    return scputimes(user, nice, system, idle)


def per_cpu_times():
    """Return system CPU times as a named tuple."""
    ret = []
    for cpu_t in cext.per_cpu_times():
        user, nice, system, idle = cpu_t
        item = scputimes(user, nice, system, idle)
        ret.append(item)
    return ret


def cpu_count_logical():
    """Return the number of logical CPUs in the system."""
    return cext.cpu_count_logical()


def cpu_count_cores():
    """Return the number of CPU cores in the system."""
    return cext.cpu_count_cores()


def cpu_stats():
    ctx_switches, interrupts, soft_interrupts, syscalls, _traps = (
        cext.cpu_stats()
    )
    return _common.scpustats(
        ctx_switches, interrupts, soft_interrupts, syscalls
    )


if cext.has_cpu_freq():  # not always available on ARM64

    def cpu_freq():
        """Return CPU frequency.
        On macOS per-cpu frequency is not supported.
        Also, the returned frequency never changes, see:
        https://arstechnica.com/civis/viewtopic.php?f=19&t=465002.
        """
        curr, min_, max_ = cext.cpu_freq()
        return [_common.scpufreq(curr, min_, max_)]


# 024397.python.psosx.line185.comment =====================================================================
# 024398.python.psosx.line186.comment --- disks
# 024399.python.psosx.line187.comment =====================================================================


disk_usage = _psposix.disk_usage
disk_io_counters = cext.disk_io_counters


def disk_partitions(all=False):
    """Return mounted disk partitions as a list of namedtuples."""
    retlist = []
    partitions = cext.disk_partitions()
    for partition in partitions:
        device, mountpoint, fstype, opts = partition
        if device == 'none':
            device = ''
        if not all:
            if not os.path.isabs(device) or not os.path.exists(device):
                continue
        ntuple = _common.sdiskpart(device, mountpoint, fstype, opts)
        retlist.append(ntuple)
    return retlist


# 024400.python.psosx.line210.comment =====================================================================
# 024401.python.psosx.line211.comment --- sensors
# 024402.python.psosx.line212.comment =====================================================================


def sensors_battery():
    """Return battery information."""
    try:
        percent, minsleft, power_plugged = cext.sensors_battery()
    except NotImplementedError:
        # 024403.python.psosx.line220.comment no power source - return None according to interface
        return None
    power_plugged = power_plugged == 1
    if power_plugged:
        secsleft = _common.POWER_TIME_UNLIMITED
    elif minsleft == -1:
        secsleft = _common.POWER_TIME_UNKNOWN
    else:
        secsleft = minsleft * 60
    return _common.sbattery(percent, secsleft, power_plugged)


# 024404.python.psosx.line232.comment =====================================================================
# 024405.python.psosx.line233.comment --- network
# 024406.python.psosx.line234.comment =====================================================================


net_io_counters = cext.net_io_counters
net_if_addrs = cext_posix.net_if_addrs


def net_connections(kind='inet'):
    """System-wide network connections."""
    # 024407.python.psosx.line243.comment Note: on macOS this will fail with AccessDenied unless
    # 024408.python.psosx.line244.comment the process is owned by root.
    ret = []
    for pid in pids():
        try:
            cons = Process(pid).net_connections(kind)
        except NoSuchProcess:
            continue
        else:
            if cons:
                for c in cons:
                    c = list(c) + [pid]
                    ret.append(_common.sconn(*c))
    return ret


def net_if_stats():
    """Get NIC stats (isup, duplex, speed, mtu)."""
    names = net_io_counters().keys()
    ret = {}
    for name in names:
        try:
            mtu = cext_posix.net_if_mtu(name)
            flags = cext_posix.net_if_flags(name)
            duplex, speed = cext_posix.net_if_duplex_speed(name)
        except OSError as err:
            # 024409.python.psosx.line269.comment https://github.com/giampaolo/psutil/issues/1279
            if err.errno != errno.ENODEV:
                raise
        else:
            if hasattr(_common, 'NicDuplex'):
                duplex = _common.NicDuplex(duplex)
            output_flags = ','.join(flags)
            isup = 'running' in flags
            ret[name] = _common.snicstats(
                isup, duplex, speed, mtu, output_flags
            )
    return ret


# 024410.python.psosx.line283.comment =====================================================================
# 024411.python.psosx.line284.comment --- other system functions
# 024412.python.psosx.line285.comment =====================================================================


def boot_time():
    """The system boot time expressed in seconds since the epoch."""
    return cext.boot_time()


try:
    INIT_BOOT_TIME = boot_time()
except Exception as err:  # noqa: BLE001
    # 024414.python.psosx.line296.comment Don't want to crash at import time.
    debug(f"ignoring exception on import: {err!r}")
    INIT_BOOT_TIME = 0


def adjust_proc_create_time(ctime):
    """Account for system clock updates."""
    if INIT_BOOT_TIME == 0:
        return ctime

    diff = INIT_BOOT_TIME - boot_time()
    if diff == 0 or abs(diff) < 1:
        return ctime

    debug("system clock was updated; adjusting process create_time()")
    if diff < 0:
        return ctime - diff
    return ctime + diff


def users():
    """Return currently connected users as a list of namedtuples."""
    retlist = []
    rawlist = cext_posix.users()
    for item in rawlist:
        user, tty, hostname, tstamp, pid = item
        if tty == '~':
            continue  # reboot or shutdown
        if not tstamp:
            continue
        nt = _common.suser(user, tty or None, hostname or None, tstamp, pid)
        retlist.append(nt)
    return retlist


# 024416.python.psosx.line331.comment =====================================================================
# 024417.python.psosx.line332.comment --- processes
# 024418.python.psosx.line333.comment =====================================================================


def pids():
    ls = cext.pids()
    if 0 not in ls:
        # 024419.python.psosx.line339.comment On certain macOS versions pids() C doesn't return PID 0 but
        # 024420.python.psosx.line340.comment "ps" does and the process is querable via sysctl():
        # 024421.python.psosx.line341.comment https://travis-ci.org/giampaolo/psutil/jobs/309619941
        try:
            Process(0).create_time()
            ls.insert(0, 0)
        except NoSuchProcess:
            pass
        except AccessDenied:
            ls.insert(0, 0)
    return ls


pid_exists = _psposix.pid_exists


def is_zombie(pid):
    try:
        st = cext.proc_kinfo_oneshot(pid)[kinfo_proc_map['status']]
        return st == cext.SZOMB
    except OSError:
        return False


def wrap_exceptions(fun):
    """Decorator which translates bare OSError exceptions into
    NoSuchProcess and AccessDenied.
    """

    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        pid, ppid, name = self.pid, self._ppid, self._name
        try:
            return fun(self, *args, **kwargs)
        except ProcessLookupError as err:
            if is_zombie(pid):
                raise ZombieProcess(pid, name, ppid) from err
            raise NoSuchProcess(pid, name) from err
        except PermissionError as err:
            raise AccessDenied(pid, name) from err

    return wrapper


class Process:
    """Wrapper class around underlying C implementation."""

    __slots__ = ["_cache", "_name", "_ppid", "pid"]

    def __init__(self, pid):
        self.pid = pid
        self._name = None
        self._ppid = None

    @wrap_exceptions
    @memoize_when_activated
    def _get_kinfo_proc(self):
        # 024422.python.psosx.line396.comment Note: should work with all PIDs without permission issues.
        ret = cext.proc_kinfo_oneshot(self.pid)
        assert len(ret) == len(kinfo_proc_map)
        return ret

    @wrap_exceptions
    @memoize_when_activated
    def _get_pidtaskinfo(self):
        # 024423.python.psosx.line404.comment Note: should work for PIDs owned by user only.
        ret = cext.proc_pidtaskinfo_oneshot(self.pid)
        assert len(ret) == len(pidtaskinfo_map)
        return ret

    def oneshot_enter(self):
        self._get_kinfo_proc.cache_activate(self)
        self._get_pidtaskinfo.cache_activate(self)

    def oneshot_exit(self):
        self._get_kinfo_proc.cache_deactivate(self)
        self._get_pidtaskinfo.cache_deactivate(self)

    @wrap_exceptions
    def name(self):
        name = self._get_kinfo_proc()[kinfo_proc_map['name']]
        return name if name is not None else cext.proc_name(self.pid)

    @wrap_exceptions
    def exe(self):
        return cext.proc_exe(self.pid)

    @wrap_exceptions
    def cmdline(self):
        return cext.proc_cmdline(self.pid)

    @wrap_exceptions
    def environ(self):
        return parse_environ_block(cext.proc_environ(self.pid))

    @wrap_exceptions
    def ppid(self):
        self._ppid = self._get_kinfo_proc()[kinfo_proc_map['ppid']]
        return self._ppid

    @wrap_exceptions
    def cwd(self):
        return cext.proc_cwd(self.pid)

    @wrap_exceptions
    def uids(self):
        rawtuple = self._get_kinfo_proc()
        return _common.puids(
            rawtuple[kinfo_proc_map['ruid']],
            rawtuple[kinfo_proc_map['euid']],
            rawtuple[kinfo_proc_map['suid']],
        )

    @wrap_exceptions
    def gids(self):
        rawtuple = self._get_kinfo_proc()
        return _common.puids(
            rawtuple[kinfo_proc_map['rgid']],
            rawtuple[kinfo_proc_map['egid']],
            rawtuple[kinfo_proc_map['sgid']],
        )

    @wrap_exceptions
    def terminal(self):
        tty_nr = self._get_kinfo_proc()[kinfo_proc_map['ttynr']]
        tmap = _psposix.get_terminal_map()
        try:
            return tmap[tty_nr]
        except KeyError:
            return None

    @wrap_exceptions
    def memory_info(self):
        rawtuple = self._get_pidtaskinfo()
        return pmem(
            rawtuple[pidtaskinfo_map['rss']],
            rawtuple[pidtaskinfo_map['vms']],
            rawtuple[pidtaskinfo_map['pfaults']],
            rawtuple[pidtaskinfo_map['pageins']],
        )

    @wrap_exceptions
    def memory_full_info(self):
        basic_mem = self.memory_info()
        uss = cext.proc_memory_uss(self.pid)
        return pfullmem(*basic_mem + (uss,))

    @wrap_exceptions
    def cpu_times(self):
        rawtuple = self._get_pidtaskinfo()
        return _common.pcputimes(
            rawtuple[pidtaskinfo_map['cpuutime']],
            rawtuple[pidtaskinfo_map['cpustime']],
            # 024424.python.psosx.line492.comment children user / system times are not retrievable (set to 0)
            0.0,
            0.0,
        )

    @wrap_exceptions
    def create_time(self, monotonic=False):
        ctime = self._get_kinfo_proc()[kinfo_proc_map['ctime']]
        if not monotonic:
            ctime = adjust_proc_create_time(ctime)
        return ctime

    @wrap_exceptions
    def num_ctx_switches(self):
        # 024425.python.psosx.line506.comment Unvoluntary value seems not to be available;
        # 024426.python.psosx.line507.comment getrusage() numbers seems to confirm this theory.
        # 024427.python.psosx.line508.comment We set it to 0.
        vol = self._get_pidtaskinfo()[pidtaskinfo_map['volctxsw']]
        return _common.pctxsw(vol, 0)

    @wrap_exceptions
    def num_threads(self):
        return self._get_pidtaskinfo()[pidtaskinfo_map['numthreads']]

    @wrap_exceptions
    def open_files(self):
        if self.pid == 0:
            return []
        files = []
        rawlist = cext.proc_open_files(self.pid)
        for path, fd in rawlist:
            if isfile_strict(path):
                ntuple = _common.popenfile(path, fd)
                files.append(ntuple)
        return files

    @wrap_exceptions
    def net_connections(self, kind='inet'):
        families, types = conn_tmap[kind]
        rawlist = cext.proc_net_connections(self.pid, families, types)
        ret = []
        for item in rawlist:
            fd, fam, type, laddr, raddr, status = item
            nt = conn_to_ntuple(
                fd, fam, type, laddr, raddr, status, TCP_STATUSES
            )
            ret.append(nt)
        return ret

    @wrap_exceptions
    def num_fds(self):
        if self.pid == 0:
            return 0
        return cext.proc_num_fds(self.pid)

    @wrap_exceptions
    def wait(self, timeout=None):
        return _psposix.wait_pid(self.pid, timeout, self._name)

    @wrap_exceptions
    def nice_get(self):
        return cext_posix.getpriority(self.pid)

    @wrap_exceptions
    def nice_set(self, value):
        return cext_posix.setpriority(self.pid, value)

    @wrap_exceptions
    def status(self):
        code = self._get_kinfo_proc()[kinfo_proc_map['status']]
        # 024428.python.psosx.line562.comment XXX is '?' legit? (we're not supposed to return it anyway)
        return PROC_STATUSES.get(code, '?')

    @wrap_exceptions
    def threads(self):
        rawlist = cext.proc_threads(self.pid)
        retlist = []
        for thread_id, utime, stime in rawlist:
            ntuple = _common.pthread(thread_id, utime, stime)
            retlist.append(ntuple)
        return retlist
