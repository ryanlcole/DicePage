# 023956.python.pslinux.line1.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 023957.python.pslinux.line2.comment Use of this source code is governed by a BSD-style license that can be
# 023958.python.pslinux.line3.comment found in the LICENSE file.

"""Linux platform implementation."""


import base64
import collections
import enum
import errno
import functools
import glob
import os
import re
import resource
import socket
import struct
import sys
import warnings
from collections import defaultdict
from collections import namedtuple

from . import _common
from . import _psposix
from . import _psutil_linux as cext
from . import _psutil_posix as cext_posix
from ._common import ENCODING
from ._common import NIC_DUPLEX_FULL
from ._common import NIC_DUPLEX_HALF
from ._common import NIC_DUPLEX_UNKNOWN
from ._common import AccessDenied
from ._common import NoSuchProcess
from ._common import ZombieProcess
from ._common import bcat
from ._common import cat
from ._common import debug
from ._common import decode
from ._common import get_procfs_path
from ._common import isfile_strict
from ._common import memoize
from ._common import memoize_when_activated
from ._common import open_binary
from ._common import open_text
from ._common import parse_environ_block
from ._common import path_exists_strict
from ._common import supports_ipv6
from ._common import usage_percent

# 023959.python.pslinux.line50.comment fmt: off
__extra__all__ = [
    'PROCFS_PATH',
    # 023960.python.pslinux.line53.comment io prio constants
    "IOPRIO_CLASS_NONE", "IOPRIO_CLASS_RT", "IOPRIO_CLASS_BE",
    "IOPRIO_CLASS_IDLE",
    # 023961.python.pslinux.line56.comment connection status constants
    "CONN_ESTABLISHED", "CONN_SYN_SENT", "CONN_SYN_RECV", "CONN_FIN_WAIT1",
    "CONN_FIN_WAIT2", "CONN_TIME_WAIT", "CONN_CLOSE", "CONN_CLOSE_WAIT",
    "CONN_LAST_ACK", "CONN_LISTEN", "CONN_CLOSING",
]

if hasattr(resource, "prlimit"):
    __extra__all__.extend(
        [x for x in dir(cext) if x.startswith('RLIM') and x.isupper()]
    )
# 023962.python.pslinux.line66.comment fmt: on


# 023963.python.pslinux.line69.comment =====================================================================
# 023964.python.pslinux.line70.comment --- globals
# 023965.python.pslinux.line71.comment =====================================================================


POWER_SUPPLY_PATH = "/sys/class/power_supply"
HAS_PROC_SMAPS = os.path.exists(f"/proc/{os.getpid()}/smaps")
HAS_PROC_SMAPS_ROLLUP = os.path.exists(f"/proc/{os.getpid()}/smaps_rollup")
HAS_PROC_IO_PRIORITY = hasattr(cext, "proc_ioprio_get")
HAS_CPU_AFFINITY = hasattr(cext, "proc_cpu_affinity_get")

# 023966.python.pslinux.line80.comment Number of clock ticks per second
CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
PAGESIZE = cext_posix.getpagesize()
LITTLE_ENDIAN = sys.byteorder == 'little'
UNSET = object()

# 023967.python.pslinux.line86.comment "man iostat" states that sectors are equivalent with blocks and have
# 023968.python.pslinux.line87.comment a size of 512 bytes. Despite this value can be queried at runtime
# 023969.python.pslinux.line88.comment via /sys/block/{DISK}/queue/hw_sector_size and results may vary
# 023970.python.pslinux.line89.comment between 1k, 2k, or 4k... 512 appears to be a magic constant used
# 023971.python.pslinux.line90.comment throughout Linux source code:
# 023972.python.pslinux.line91.comment * https://stackoverflow.com/a/38136179/376587
# 023973.python.pslinux.line92.comment * https://lists.gt.net/linux/kernel/2241060
# 023974.python.pslinux.line93.comment * https://github.com/giampaolo/psutil/issues/1305
# 023975.python.pslinux.line94.comment * https://github.com/torvalds/linux/blob/
# 023976.python.pslinux.line95.comment 4f671fe2f9523a1ea206f63fe60a7c7b3a56d5c7/include/linux/bio.h#L99
# 023977.python.pslinux.line96.comment * https://lkml.org/lkml/2015/8/17/234
DISK_SECTOR_SIZE = 512

AddressFamily = enum.IntEnum(
    'AddressFamily', {'AF_LINK': int(socket.AF_PACKET)}
)
AF_LINK = AddressFamily.AF_LINK


# 023978.python.pslinux.line105.comment ioprio_* constants http://linux.die.net/man/2/ioprio_get
class IOPriority(enum.IntEnum):
    IOPRIO_CLASS_NONE = 0
    IOPRIO_CLASS_RT = 1
    IOPRIO_CLASS_BE = 2
    IOPRIO_CLASS_IDLE = 3


globals().update(IOPriority.__members__)

# 023979.python.pslinux.line115.comment See:
# 023980.python.pslinux.line116.comment https://github.com/torvalds/linux/blame/master/fs/proc/array.c
# 023981.python.pslinux.line117.comment ...and (TASK_* constants):
# 023982.python.pslinux.line118.comment https://github.com/torvalds/linux/blob/master/include/linux/sched.h
PROC_STATUSES = {
    "R": _common.STATUS_RUNNING,
    "S": _common.STATUS_SLEEPING,
    "D": _common.STATUS_DISK_SLEEP,
    "T": _common.STATUS_STOPPED,
    "t": _common.STATUS_TRACING_STOP,
    "Z": _common.STATUS_ZOMBIE,
    "X": _common.STATUS_DEAD,
    "x": _common.STATUS_DEAD,
    "K": _common.STATUS_WAKE_KILL,
    "W": _common.STATUS_WAKING,
    "I": _common.STATUS_IDLE,
    "P": _common.STATUS_PARKED,
}

# 023983.python.pslinux.line134.comment https://github.com/torvalds/linux/blob/master/include/net/tcp_states.h
TCP_STATUSES = {
    "01": _common.CONN_ESTABLISHED,
    "02": _common.CONN_SYN_SENT,
    "03": _common.CONN_SYN_RECV,
    "04": _common.CONN_FIN_WAIT1,
    "05": _common.CONN_FIN_WAIT2,
    "06": _common.CONN_TIME_WAIT,
    "07": _common.CONN_CLOSE,
    "08": _common.CONN_CLOSE_WAIT,
    "09": _common.CONN_LAST_ACK,
    "0A": _common.CONN_LISTEN,
    "0B": _common.CONN_CLOSING,
}


# 023984.python.pslinux.line150.comment =====================================================================
# 023985.python.pslinux.line151.comment --- named tuples
# 023986.python.pslinux.line152.comment =====================================================================


# 023987.python.pslinux.line155.comment fmt: off
# 023988.python.pslinux.line156.comment psutil.virtual_memory()
svmem = namedtuple(
    'svmem', ['total', 'available', 'percent', 'used', 'free',
              'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'])
# 023989.python.pslinux.line160.comment psutil.disk_io_counters()
sdiskio = namedtuple(
    'sdiskio', ['read_count', 'write_count',
                'read_bytes', 'write_bytes',
                'read_time', 'write_time',
                'read_merged_count', 'write_merged_count',
                'busy_time'])
# 023990.python.pslinux.line167.comment psutil.Process().open_files()
popenfile = namedtuple(
    'popenfile', ['path', 'fd', 'position', 'mode', 'flags'])
# 023991.python.pslinux.line170.comment psutil.Process().memory_info()
pmem = namedtuple('pmem', 'rss vms shared text lib data dirty')
# 023992.python.pslinux.line172.comment psutil.Process().memory_full_info()
pfullmem = namedtuple('pfullmem', pmem._fields + ('uss', 'pss', 'swap'))
# 023993.python.pslinux.line174.comment psutil.Process().memory_maps(grouped=True)
pmmap_grouped = namedtuple(
    'pmmap_grouped',
    ['path', 'rss', 'size', 'pss', 'shared_clean', 'shared_dirty',
     'private_clean', 'private_dirty', 'referenced', 'anonymous', 'swap'])
# 023994.python.pslinux.line179.comment psutil.Process().memory_maps(grouped=False)
pmmap_ext = namedtuple(
    'pmmap_ext', 'addr perms ' + ' '.join(pmmap_grouped._fields))
# 023995.python.pslinux.line182.comment psutil.Process.io_counters()
pio = namedtuple('pio', ['read_count', 'write_count',
                         'read_bytes', 'write_bytes',
                         'read_chars', 'write_chars'])
# 023996.python.pslinux.line186.comment psutil.Process.cpu_times()
pcputimes = namedtuple('pcputimes',
                       ['user', 'system', 'children_user', 'children_system',
                        'iowait'])
# 023997.python.pslinux.line190.comment fmt: on


# 023998.python.pslinux.line193.comment =====================================================================
# 023999.python.pslinux.line194.comment --- utils
# 024000.python.pslinux.line195.comment =====================================================================


def readlink(path):
    """Wrapper around os.readlink()."""
    assert isinstance(path, str), path
    path = os.readlink(path)
    # 024001.python.pslinux.line202.comment readlink() might return paths containing null bytes ('\x00')
    # 024002.python.pslinux.line203.comment resulting in "TypeError: must be encoded string without NULL
    # 024003.python.pslinux.line204.comment bytes, not str" errors when the string is passed to other
    # 024004.python.pslinux.line205.comment fs-related functions (os.*, open(), ...).
    # 024005.python.pslinux.line206.comment Apparently everything after '\x00' is garbage (we can have
    # 024006.python.pslinux.line207.comment ' (deleted)', 'new' and possibly others), see:
    # 024007.python.pslinux.line208.comment https://github.com/giampaolo/psutil/issues/717
    path = path.split('\x00')[0]
    # 024008.python.pslinux.line210.comment Certain paths have ' (deleted)' appended. Usually this is
    # 024009.python.pslinux.line211.comment bogus as the file actually exists. Even if it doesn't we
    # 024010.python.pslinux.line212.comment don't care.
    if path.endswith(' (deleted)') and not path_exists_strict(path):
        path = path[:-10]
    return path


def file_flags_to_mode(flags):
    """Convert file's open() flags into a readable string.
    Used by Process.open_files().
    """
    modes_map = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    mode = modes_map[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]
    if flags & os.O_APPEND:
        mode = mode.replace('w', 'a', 1)
    mode = mode.replace('w+', 'r+')
    # 024011.python.pslinux.line227.comment possible values: r, w, a, r+, a+
    return mode


def is_storage_device(name):
    """Return True if the given name refers to a root device (e.g.
    "sda", "nvme0n1") as opposed to a logical partition (e.g.  "sda1",
    "nvme0n1p1"). If name is a virtual device (e.g. "loop1", "ram")
    return True.
    """
    # 024012.python.pslinux.line237.comment Re-adapted from iostat source code, see:
    # 024013.python.pslinux.line238.comment https://github.com/sysstat/sysstat/blob/
    # 024014.python.pslinux.line239.comment 97912938cd476645b267280069e83b1c8dc0e1c7/common.c#L208
    # 024015.python.pslinux.line240.comment Some devices may have a slash in their name (e.g. cciss/c0d0...).
    name = name.replace('/', '!')
    including_virtual = True
    if including_virtual:
        path = f"/sys/block/{name}"
    else:
        path = f"/sys/block/{name}/device"
    return os.access(path, os.F_OK)


@memoize
def set_scputimes_ntuple(procfs_path):
    """Set a namedtuple of variable fields depending on the CPU times
    available on this Linux kernel version which may be:
    (user, nice, system, idle, iowait, irq, softirq, [steal, [guest,
     [guest_nice]]])
    Used by cpu_times() function.
    """
    global scputimes
    with open_binary(f"{procfs_path}/stat") as f:
        values = f.readline().split()[1:]
    fields = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq']
    vlen = len(values)
    if vlen >= 8:
        # 024016.python.pslinux.line264.comment Linux >= 2.6.11
        fields.append('steal')
    if vlen >= 9:
        # 024017.python.pslinux.line267.comment Linux >= 2.6.24
        fields.append('guest')
    if vlen >= 10:
        # 024018.python.pslinux.line270.comment Linux >= 3.2.0
        fields.append('guest_nice')
    scputimes = namedtuple('scputimes', fields)


try:
    set_scputimes_ntuple("/proc")
except Exception as err:  # noqa: BLE001
    # 024020.python.pslinux.line278.comment Don't want to crash at import time.
    debug(f"ignoring exception on import: {err!r}")
    scputimes = namedtuple('scputimes', 'user system idle')(0.0, 0.0, 0.0)


# 024021.python.pslinux.line283.comment =====================================================================
# 024022.python.pslinux.line284.comment --- system memory
# 024023.python.pslinux.line285.comment =====================================================================


def calculate_avail_vmem(mems):
    """Fallback for kernels < 3.14 where /proc/meminfo does not provide
    "MemAvailable", see:
    https://blog.famzah.net/2014/09/24/.

    This code reimplements the algorithm outlined here:
    https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/
        commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773

    We use this function also when "MemAvailable" returns 0 (possibly a
    kernel bug, see: https://github.com/giampaolo/psutil/issues/1915).
    In that case this routine matches "free" CLI tool result ("available"
    column).

    XXX: on recent kernels this calculation may differ by ~1.5% compared
    to "MemAvailable:", as it's calculated slightly differently.
    It is still way more realistic than doing (free + cached) though.
    See:
    * https://gitlab.com/procps-ng/procps/issues/42
    * https://github.com/famzah/linux-memavailable-procfs/issues/2
    """
    # 024024.python.pslinux.line309.comment Note about "fallback" value. According to:
    # 024025.python.pslinux.line310.comment https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/
    # 024026.python.pslinux.line311.comment commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773
    # 024027.python.pslinux.line312.comment ...long ago "available" memory was calculated as (free + cached),
    # 024028.python.pslinux.line313.comment We use fallback when one of these is missing from /proc/meminfo:
    # 024029.python.pslinux.line314.comment "Active(file)": introduced in 2.6.28 / Dec 2008
    # 024030.python.pslinux.line315.comment "Inactive(file)": introduced in 2.6.28 / Dec 2008
    # 024031.python.pslinux.line316.comment "SReclaimable": introduced in 2.6.19 / Nov 2006
    # 024032.python.pslinux.line317.comment /proc/zoneinfo: introduced in 2.6.13 / Aug 2005
    free = mems[b'MemFree:']
    fallback = free + mems.get(b"Cached:", 0)
    try:
        lru_active_file = mems[b'Active(file):']
        lru_inactive_file = mems[b'Inactive(file):']
        slab_reclaimable = mems[b'SReclaimable:']
    except KeyError as err:
        debug(
            f"{err.args[0]} is missing from /proc/meminfo; using an"
            " approximation for calculating available memory"
        )
        return fallback
    try:
        f = open_binary(f"{get_procfs_path()}/zoneinfo")
    except OSError:
        return fallback  # kernel 2.6.13

    watermark_low = 0
    with f:
        for line in f:
            line = line.strip()
            if line.startswith(b'low'):
                watermark_low += int(line.split()[1])
    watermark_low *= PAGESIZE

    avail = free - watermark_low
    pagecache = lru_active_file + lru_inactive_file
    pagecache -= min(pagecache / 2, watermark_low)
    avail += pagecache
    avail += slab_reclaimable - min(slab_reclaimable / 2.0, watermark_low)
    return int(avail)


def virtual_memory():
    """Report virtual memory stats.
    This implementation mimics procps-ng-3.3.12, aka "free" CLI tool:
    https://gitlab.com/procps-ng/procps/blob/
        24fd2605c51fccc375ab0287cec33aa767f06718/proc/sysinfo.c#L778-791
    The returned values are supposed to match both "free" and "vmstat -s"
    CLI tools.
    """
    missing_fields = []
    mems = {}
    with open_binary(f"{get_procfs_path()}/meminfo") as f:
        for line in f:
            fields = line.split()
            mems[fields[0]] = int(fields[1]) * 1024

    # 024034.python.pslinux.line366.comment /proc doc states that the available fields in /proc/meminfo vary
    # 024035.python.pslinux.line367.comment by architecture and compile options, but these 3 values are also
    # 024036.python.pslinux.line368.comment returned by sysinfo(2); as such we assume they are always there.
    total = mems[b'MemTotal:']
    free = mems[b'MemFree:']
    try:
        buffers = mems[b'Buffers:']
    except KeyError:
        # 024037.python.pslinux.line374.comment https://github.com/giampaolo/psutil/issues/1010
        buffers = 0
        missing_fields.append('buffers')
    try:
        cached = mems[b"Cached:"]
    except KeyError:
        cached = 0
        missing_fields.append('cached')
    else:
        # 024038.python.pslinux.line383.comment "free" cmdline utility sums reclaimable to cached.
        # 024039.python.pslinux.line384.comment Older versions of procps used to add slab memory instead.
        # 024040.python.pslinux.line385.comment This got changed in:
        # 024041.python.pslinux.line386.comment https://gitlab.com/procps-ng/procps/commit/
        # 024042.python.pslinux.line387.comment 05d751c4f076a2f0118b914c5e51cfbb4762ad8e
        cached += mems.get(b"SReclaimable:", 0)  # since kernel 2.6.19

    try:
        shared = mems[b'Shmem:']  # since kernel 2.6.32
    except KeyError:
        try:
            shared = mems[b'MemShared:']  # kernels 2.4
        except KeyError:
            shared = 0
            missing_fields.append('shared')

    try:
        active = mems[b"Active:"]
    except KeyError:
        active = 0
        missing_fields.append('active')

    try:
        inactive = mems[b"Inactive:"]
    except KeyError:
        try:
            inactive = (
                mems[b"Inact_dirty:"]
                + mems[b"Inact_clean:"]
                + mems[b"Inact_laundry:"]
            )
        except KeyError:
            inactive = 0
            missing_fields.append('inactive')

    try:
        slab = mems[b"Slab:"]
    except KeyError:
        slab = 0

    # 024046.python.pslinux.line423.comment - starting from 4.4.0 we match free's "available" column.
    # 024047.python.pslinux.line424.comment Before 4.4.0 we calculated it as (free + buffers + cached)
    # 024048.python.pslinux.line425.comment which matched htop.
    # 024049.python.pslinux.line426.comment - free and htop available memory differs as per:
    # 024050.python.pslinux.line427.comment http://askubuntu.com/a/369589
    # 024051.python.pslinux.line428.comment http://unix.stackexchange.com/a/65852/168884
    # 024052.python.pslinux.line429.comment - MemAvailable has been introduced in kernel 3.14
    try:
        avail = mems[b'MemAvailable:']
    except KeyError:
        avail = calculate_avail_vmem(mems)
    else:
        if avail == 0:
            # 024053.python.pslinux.line436.comment Yes, it can happen (probably a kernel bug):
            # 024054.python.pslinux.line437.comment https://github.com/giampaolo/psutil/issues/1915
            # 024055.python.pslinux.line438.comment In this case "free" CLI tool makes an estimate. We do the same,
            # 024056.python.pslinux.line439.comment and it matches "free" CLI tool.
            avail = calculate_avail_vmem(mems)

    if avail < 0:
        avail = 0
        missing_fields.append('available')
    elif avail > total:
        # 024057.python.pslinux.line446.comment If avail is greater than total or our calculation overflows,
        # 024058.python.pslinux.line447.comment that's symptomatic of running within a LCX container where such
        # 024059.python.pslinux.line448.comment values will be dramatically distorted over those of the host.
        # 024060.python.pslinux.line449.comment https://gitlab.com/procps-ng/procps/blob/
        # 024061.python.pslinux.line450.comment 24fd2605c51fccc375ab0287cec33aa767f06718/proc/sysinfo.c#L764
        avail = free

    used = total - avail

    percent = usage_percent((total - avail), total, round_=1)

    # 024062.python.pslinux.line457.comment Warn about missing metrics which are set to 0.
    if missing_fields:
        msg = "{} memory stats couldn't be determined and {} set to 0".format(
            ", ".join(missing_fields),
            "was" if len(missing_fields) == 1 else "were",
        )
        warnings.warn(msg, RuntimeWarning, stacklevel=2)

    return svmem(
        total,
        avail,
        percent,
        used,
        free,
        active,
        inactive,
        buffers,
        cached,
        shared,
        slab,
    )


def swap_memory():
    """Return swap memory metrics."""
    mems = {}
    with open_binary(f"{get_procfs_path()}/meminfo") as f:
        for line in f:
            fields = line.split()
            mems[fields[0]] = int(fields[1]) * 1024
    # 024063.python.pslinux.line487.comment We prefer /proc/meminfo over sysinfo() syscall so that
    # 024064.python.pslinux.line488.comment psutil.PROCFS_PATH can be used in order to allow retrieval
    # 024065.python.pslinux.line489.comment for linux containers, see:
    # 024066.python.pslinux.line490.comment https://github.com/giampaolo/psutil/issues/1015
    try:
        total = mems[b'SwapTotal:']
        free = mems[b'SwapFree:']
    except KeyError:
        _, _, _, _, total, free, unit_multiplier = cext.linux_sysinfo()
        total *= unit_multiplier
        free *= unit_multiplier

    used = total - free
    percent = usage_percent(used, total, round_=1)
    # 024067.python.pslinux.line501.comment get pgin/pgouts
    try:
        f = open_binary(f"{get_procfs_path()}/vmstat")
    except OSError as err:
        # 024068.python.pslinux.line505.comment see https://github.com/giampaolo/psutil/issues/722
        msg = (
            "'sin' and 'sout' swap memory stats couldn't "
            f"be determined and were set to 0 ({err})"
        )
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        sin = sout = 0
    else:
        with f:
            sin = sout = None
            for line in f:
                # 024069.python.pslinux.line516.comment values are expressed in 4 kilo bytes, we want
                # 024070.python.pslinux.line517.comment bytes instead
                if line.startswith(b'pswpin'):
                    sin = int(line.split(b' ')[1]) * 4 * 1024
                elif line.startswith(b'pswpout'):
                    sout = int(line.split(b' ')[1]) * 4 * 1024
                if sin is not None and sout is not None:
                    break
            else:
                # 024071.python.pslinux.line525.comment we might get here when dealing with exotic Linux
                # 024072.python.pslinux.line526.comment flavors, see:
                # 024073.python.pslinux.line527.comment https://github.com/giampaolo/psutil/issues/313
                msg = "'sin' and 'sout' swap memory stats couldn't "
                msg += "be determined and were set to 0"
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                sin = sout = 0
    return _common.sswap(total, used, free, percent, sin, sout)


# 024074.python.pslinux.line535.comment =====================================================================
# 024075.python.pslinux.line536.comment --- CPU
# 024076.python.pslinux.line537.comment =====================================================================


def cpu_times():
    """Return a named tuple representing the following system-wide
    CPU times:
    (user, nice, system, idle, iowait, irq, softirq [steal, [guest,
     [guest_nice]]])
    Last 3 fields may not be available on all Linux kernel versions.
    """
    procfs_path = get_procfs_path()
    set_scputimes_ntuple(procfs_path)
    with open_binary(f"{procfs_path}/stat") as f:
        values = f.readline().split()
    fields = values[1 : len(scputimes._fields) + 1]
    fields = [float(x) / CLOCK_TICKS for x in fields]
    return scputimes(*fields)


def per_cpu_times():
    """Return a list of namedtuple representing the CPU times
    for every CPU available on the system.
    """
    procfs_path = get_procfs_path()
    set_scputimes_ntuple(procfs_path)
    cpus = []
    with open_binary(f"{procfs_path}/stat") as f:
        # 024077.python.pslinux.line564.comment get rid of the first line which refers to system wide CPU stats
        f.readline()
        for line in f:
            if line.startswith(b'cpu'):
                values = line.split()
                fields = values[1 : len(scputimes._fields) + 1]
                fields = [float(x) / CLOCK_TICKS for x in fields]
                entry = scputimes(*fields)
                cpus.append(entry)
        return cpus


def cpu_count_logical():
    """Return the number of logical CPUs in the system."""
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        # 024078.python.pslinux.line581.comment as a second fallback we try to parse /proc/cpuinfo
        num = 0
        with open_binary(f"{get_procfs_path()}/cpuinfo") as f:
            for line in f:
                if line.lower().startswith(b'processor'):
                    num += 1

        # 024079.python.pslinux.line588.comment unknown format (e.g. amrel/sparc architectures), see:
        # 024080.python.pslinux.line589.comment https://github.com/giampaolo/psutil/issues/200
        # 024081.python.pslinux.line590.comment try to parse /proc/stat as a last resort
        if num == 0:
            search = re.compile(r'cpu\d')
            with open_text(f"{get_procfs_path()}/stat") as f:
                for line in f:
                    line = line.split(' ')[0]
                    if search.match(line):
                        num += 1

        if num == 0:
            # 024082.python.pslinux.line600.comment mimic os.cpu_count()
            return None
        return num


def cpu_count_cores():
    """Return the number of CPU cores in the system."""
    # 024083.python.pslinux.line607.comment Method #1
    ls = set()
    # 024084.python.pslinux.line609.comment These 2 files are the same but */core_cpus_list is newer while
    # 024085.python.pslinux.line610.comment */thread_siblings_list is deprecated and may disappear in the future.
    # 024086.python.pslinux.line611.comment https://www.kernel.org/doc/Documentation/admin-guide/cputopology.rst
    # 024087.python.pslinux.line612.comment https://github.com/giampaolo/psutil/pull/1727#issuecomment-707624964
    # 024088.python.pslinux.line613.comment https://lkml.org/lkml/2019/2/26/41
    p1 = "/sys/devices/system/cpu/cpu[0-9]*/topology/core_cpus_list"
    p2 = "/sys/devices/system/cpu/cpu[0-9]*/topology/thread_siblings_list"
    for path in glob.glob(p1) or glob.glob(p2):
        with open_binary(path) as f:
            ls.add(f.read().strip())
    result = len(ls)
    if result != 0:
        return result

    # 024089.python.pslinux.line623.comment Method #2
    mapping = {}
    current_info = {}
    with open_binary(f"{get_procfs_path()}/cpuinfo") as f:
        for line in f:
            line = line.strip().lower()
            if not line:
                # 024090.python.pslinux.line630.comment new section
                try:
                    mapping[current_info[b'physical id']] = current_info[
                        b'cpu cores'
                    ]
                except KeyError:
                    pass
                current_info = {}
            elif line.startswith((b'physical id', b'cpu cores')):
                # 024091.python.pslinux.line639.comment ongoing section
                key, value = line.split(b'\t:', 1)
                current_info[key] = int(value)

    result = sum(mapping.values())
    return result or None  # mimic os.cpu_count()


def cpu_stats():
    """Return various CPU stats as a named tuple."""
    with open_binary(f"{get_procfs_path()}/stat") as f:
        ctx_switches = None
        interrupts = None
        soft_interrupts = None
        for line in f:
            if line.startswith(b'ctxt'):
                ctx_switches = int(line.split()[1])
            elif line.startswith(b'intr'):
                interrupts = int(line.split()[1])
            elif line.startswith(b'softirq'):
                soft_interrupts = int(line.split()[1])
            if (
                ctx_switches is not None
                and soft_interrupts is not None
                and interrupts is not None
            ):
                break
    syscalls = 0
    return _common.scpustats(
        ctx_switches, interrupts, soft_interrupts, syscalls
    )


def _cpu_get_cpuinfo_freq():
    """Return current CPU frequency from cpuinfo if available."""
    with open_binary(f"{get_procfs_path()}/cpuinfo") as f:
        return [
            float(line.split(b':', 1)[1])
            for line in f
            if line.lower().startswith(b'cpu mhz')
        ]


if os.path.exists("/sys/devices/system/cpu/cpufreq/policy0") or os.path.exists(
    "/sys/devices/system/cpu/cpu0/cpufreq"
):

    def cpu_freq():
        """Return frequency metrics for all CPUs.
        Contrarily to other OSes, Linux updates these values in
        real-time.
        """
        cpuinfo_freqs = _cpu_get_cpuinfo_freq()
        paths = glob.glob(
            "/sys/devices/system/cpu/cpufreq/policy[0-9]*"
        ) or glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq")
        paths.sort(key=lambda x: int(re.search(r"[0-9]+", x).group()))
        ret = []
        pjoin = os.path.join
        for i, path in enumerate(paths):
            if len(paths) == len(cpuinfo_freqs):
                # 024093.python.pslinux.line700.comment take cached value from cpuinfo if available, see:
                # 024094.python.pslinux.line701.comment https://github.com/giampaolo/psutil/issues/1851
                curr = cpuinfo_freqs[i] * 1000
            else:
                curr = bcat(pjoin(path, "scaling_cur_freq"), fallback=None)
            if curr is None:
                # 024095.python.pslinux.line706.comment Likely an old RedHat, see:
                # 024096.python.pslinux.line707.comment https://github.com/giampaolo/psutil/issues/1071
                curr = bcat(pjoin(path, "cpuinfo_cur_freq"), fallback=None)
                if curr is None:
                    online_path = f"/sys/devices/system/cpu/cpu{i}/online"
                    # 024097.python.pslinux.line711.comment if cpu core is offline, set to all zeroes
                    if cat(online_path, fallback=None) == "0\n":
                        ret.append(_common.scpufreq(0.0, 0.0, 0.0))
                        continue
                    msg = "can't find current frequency file"
                    raise NotImplementedError(msg)
            curr = int(curr) / 1000
            max_ = int(bcat(pjoin(path, "scaling_max_freq"))) / 1000
            min_ = int(bcat(pjoin(path, "scaling_min_freq"))) / 1000
            ret.append(_common.scpufreq(curr, min_, max_))
        return ret

else:

    def cpu_freq():
        """Alternate implementation using /proc/cpuinfo.
        min and max frequencies are not available and are set to None.
        """
        return [_common.scpufreq(x, 0.0, 0.0) for x in _cpu_get_cpuinfo_freq()]


# 024098.python.pslinux.line732.comment =====================================================================
# 024099.python.pslinux.line733.comment --- network
# 024100.python.pslinux.line734.comment =====================================================================


net_if_addrs = cext_posix.net_if_addrs


class _Ipv6UnsupportedError(Exception):
    pass


class NetConnections:
    """A wrapper on top of /proc/net/* files, retrieving per-process
    and system-wide open connections (TCP, UDP, UNIX) similarly to
    "netstat -an".

    Note: in case of UNIX sockets we're only able to determine the
    local endpoint/path, not the one it's connected to.
    According to [1] it would be possible but not easily.

    [1] http://serverfault.com/a/417946
    """

    def __init__(self):
        # 024101.python.pslinux.line757.comment The string represents the basename of the corresponding
        # 024102.python.pslinux.line758.comment /proc/net/{proto_name} file.
        tcp4 = ("tcp", socket.AF_INET, socket.SOCK_STREAM)
        tcp6 = ("tcp6", socket.AF_INET6, socket.SOCK_STREAM)
        udp4 = ("udp", socket.AF_INET, socket.SOCK_DGRAM)
        udp6 = ("udp6", socket.AF_INET6, socket.SOCK_DGRAM)
        unix = ("unix", socket.AF_UNIX, None)
        self.tmap = {
            "all": (tcp4, tcp6, udp4, udp6, unix),
            "tcp": (tcp4, tcp6),
            "tcp4": (tcp4,),
            "tcp6": (tcp6,),
            "udp": (udp4, udp6),
            "udp4": (udp4,),
            "udp6": (udp6,),
            "unix": (unix,),
            "inet": (tcp4, tcp6, udp4, udp6),
            "inet4": (tcp4, udp4),
            "inet6": (tcp6, udp6),
        }
        self._procfs_path = None

    def get_proc_inodes(self, pid):
        inodes = defaultdict(list)
        for fd in os.listdir(f"{self._procfs_path}/{pid}/fd"):
            try:
                inode = readlink(f"{self._procfs_path}/{pid}/fd/{fd}")
            except (FileNotFoundError, ProcessLookupError):
                # 024103.python.pslinux.line785.comment ENOENT == file which is gone in the meantime;
                # 024104.python.pslinux.line786.comment os.stat(f"/proc/{self.pid}") will be done later
                # 024105.python.pslinux.line787.comment to force NSP (if it's the case)
                continue
            except OSError as err:
                if err.errno == errno.EINVAL:
                    # 024106.python.pslinux.line791.comment not a link
                    continue
                if err.errno == errno.ENAMETOOLONG:
                    # 024107.python.pslinux.line794.comment file name too long
                    debug(err)
                    continue
                raise
            else:
                if inode.startswith('socket:['):
                    # 024108.python.pslinux.line800.comment the process is using a socket
                    inode = inode[8:][:-1]
                    inodes[inode].append((pid, int(fd)))
        return inodes

    def get_all_inodes(self):
        inodes = {}
        for pid in pids():
            try:
                inodes.update(self.get_proc_inodes(pid))
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                # 024109.python.pslinux.line811.comment os.listdir() is gonna raise a lot of access denied
                # 024110.python.pslinux.line812.comment exceptions in case of unprivileged user; that's fine
                # 024111.python.pslinux.line813.comment as we'll just end up returning a connection with PID
                # 024112.python.pslinux.line814.comment and fd set to None anyway.
                # 024113.python.pslinux.line815.comment Both netstat -an and lsof does the same so it's
                # 024114.python.pslinux.line816.comment unlikely we can do any better.
                # 024115.python.pslinux.line817.comment ENOENT just means a PID disappeared on us.
                continue
        return inodes

    @staticmethod
    def decode_address(addr, family):
        """Accept an "ip:port" address as displayed in /proc/net/*
        and convert it into a human readable form, like:

        "0500000A:0016" -> ("10.0.0.5", 22)
        "0000000000000000FFFF00000100007F:9E49" -> ("::ffff:127.0.0.1", 40521)

        The IP address portion is a little or big endian four-byte
        hexadecimal number; that is, the least significant byte is listed
        first, so we need to reverse the order of the bytes to convert it
        to an IP address.
        The port is represented as a two-byte hexadecimal number.

        Reference:
        http://linuxdevcenter.com/pub/a/linux/2000/11/16/LinuxAdmin.html
        """
        ip, port = addr.split(':')
        port = int(port, 16)
        # 024116.python.pslinux.line840.comment this usually refers to a local socket in listen mode with
        # 024117.python.pslinux.line841.comment no end-points connected
        if not port:
            return ()
        ip = ip.encode('ascii')
        if family == socket.AF_INET:
            # 024118.python.pslinux.line846.comment see: https://github.com/giampaolo/psutil/issues/201
            if LITTLE_ENDIAN:
                ip = socket.inet_ntop(family, base64.b16decode(ip)[::-1])
            else:
                ip = socket.inet_ntop(family, base64.b16decode(ip))
        else:  # IPv6
            ip = base64.b16decode(ip)
            try:
                # 024120.python.pslinux.line854.comment see: https://github.com/giampaolo/psutil/issues/201
                if LITTLE_ENDIAN:
                    ip = socket.inet_ntop(
                        socket.AF_INET6,
                        struct.pack('>4I', *struct.unpack('<4I', ip)),
                    )
                else:
                    ip = socket.inet_ntop(
                        socket.AF_INET6,
                        struct.pack('<4I', *struct.unpack('<4I', ip)),
                    )
            except ValueError:
                # 024121.python.pslinux.line866.comment see: https://github.com/giampaolo/psutil/issues/623
                if not supports_ipv6():
                    raise _Ipv6UnsupportedError from None
                raise
        return _common.addr(ip, port)

    @staticmethod
    def process_inet(file, family, type_, inodes, filter_pid=None):
        """Parse /proc/net/tcp* and /proc/net/udp* files."""
        if file.endswith('6') and not os.path.exists(file):
            # 024122.python.pslinux.line876.comment IPv6 not supported
            return
        with open_text(file) as f:
            f.readline()  # skip the first line
            for lineno, line in enumerate(f, 1):
                try:
                    _, laddr, raddr, status, _, _, _, _, _, inode = (
                        line.split()[:10]
                    )
                except ValueError:
                    msg = (
                        f"error while parsing {file}; malformed line"
                        f" {lineno} {line!r}"
                    )
                    raise RuntimeError(msg) from None
                if inode in inodes:
                    # 024124.python.pslinux.line892.comment # We assume inet sockets are unique, so we error
                    # 024125.python.pslinux.line893.comment # out if there are multiple references to the
                    # 024126.python.pslinux.line894.comment # same inode. We won't do this for UNIX sockets.
                    # 024127.python.pslinux.line895.comment if len(inodes[inode]) > 1 and family != socket.AF_UNIX:
                    # 024128.python.pslinux.line896.comment raise ValueError("ambiguous inode with multiple "
                    # 024129.python.pslinux.line897.comment "PIDs references")
                    pid, fd = inodes[inode][0]
                else:
                    pid, fd = None, -1
                if filter_pid is not None and filter_pid != pid:
                    continue
                else:
                    if type_ == socket.SOCK_STREAM:
                        status = TCP_STATUSES[status]
                    else:
                        status = _common.CONN_NONE
                    try:
                        laddr = NetConnections.decode_address(laddr, family)
                        raddr = NetConnections.decode_address(raddr, family)
                    except _Ipv6UnsupportedError:
                        continue
                    yield (fd, family, type_, laddr, raddr, status, pid)

    @staticmethod
    def process_unix(file, family, inodes, filter_pid=None):
        """Parse /proc/net/unix files."""
        with open_text(file) as f:
            f.readline()  # skip the first line
            for line in f:
                tokens = line.split()
                try:
                    _, _, _, _, type_, _, inode = tokens[0:7]
                except ValueError:
                    if ' ' not in line:
                        # 024131.python.pslinux.line926.comment see: https://github.com/giampaolo/psutil/issues/766
                        continue
                    msg = (
                        f"error while parsing {file}; malformed line {line!r}"
                    )
                    raise RuntimeError(msg)  # noqa: B904
                if inode in inodes:  # noqa: SIM108
                    # 024134.python.pslinux.line933.comment With UNIX sockets we can have a single inode
                    # 024135.python.pslinux.line934.comment referencing many file descriptors.
                    pairs = inodes[inode]
                else:
                    pairs = [(None, -1)]
                for pid, fd in pairs:
                    if filter_pid is not None and filter_pid != pid:
                        continue
                    else:
                        path = tokens[-1] if len(tokens) == 8 else ''
                        type_ = _common.socktype_to_enum(int(type_))
                        # 024136.python.pslinux.line944.comment XXX: determining the remote endpoint of a
                        # 024137.python.pslinux.line945.comment UNIX socket on Linux is not possible, see:
                        # 024138.python.pslinux.line946.comment https://serverfault.com/questions/252723/
                        raddr = ""
                        status = _common.CONN_NONE
                        yield (fd, family, type_, path, raddr, status, pid)

    def retrieve(self, kind, pid=None):
        self._procfs_path = get_procfs_path()
        if pid is not None:
            inodes = self.get_proc_inodes(pid)
            if not inodes:
                # 024139.python.pslinux.line956.comment no connections for this process
                return []
        else:
            inodes = self.get_all_inodes()
        ret = set()
        for proto_name, family, type_ in self.tmap[kind]:
            path = f"{self._procfs_path}/net/{proto_name}"
            if family in {socket.AF_INET, socket.AF_INET6}:
                ls = self.process_inet(
                    path, family, type_, inodes, filter_pid=pid
                )
            else:
                ls = self.process_unix(path, family, inodes, filter_pid=pid)
            for fd, family, type_, laddr, raddr, status, bound_pid in ls:
                if pid:
                    conn = _common.pconn(
                        fd, family, type_, laddr, raddr, status
                    )
                else:
                    conn = _common.sconn(
                        fd, family, type_, laddr, raddr, status, bound_pid
                    )
                ret.add(conn)
        return list(ret)


_net_connections = NetConnections()


def net_connections(kind='inet'):
    """Return system-wide open connections."""
    return _net_connections.retrieve(kind)


def net_io_counters():
    """Return network I/O statistics for every network interface
    installed on the system as a dict of raw tuples.
    """
    with open_text(f"{get_procfs_path()}/net/dev") as f:
        lines = f.readlines()
    retdict = {}
    for line in lines[2:]:
        colon = line.rfind(':')
        assert colon > 0, repr(line)
        name = line[:colon].strip()
        fields = line[colon + 1 :].strip().split()

        (
            # 024140.python.pslinux.line1004.comment in
            bytes_recv,
            packets_recv,
            errin,
            dropin,
            _fifoin,  # unused
            _framein,  # unused
            _compressedin,  # unused
            _multicastin,  # unused
            # 024145.python.pslinux.line1013.comment out
            bytes_sent,
            packets_sent,
            errout,
            dropout,
            _fifoout,  # unused
            _collisionsout,  # unused
            _carrierout,  # unused
            _compressedout,  # unused
        ) = map(int, fields)

        retdict[name] = (
            bytes_sent,
            bytes_recv,
            packets_sent,
            packets_recv,
            errin,
            errout,
            dropin,
            dropout,
        )
    return retdict


def net_if_stats():
    """Get NIC stats (isup, duplex, speed, mtu)."""
    duplex_map = {
        cext.DUPLEX_FULL: NIC_DUPLEX_FULL,
        cext.DUPLEX_HALF: NIC_DUPLEX_HALF,
        cext.DUPLEX_UNKNOWN: NIC_DUPLEX_UNKNOWN,
    }
    names = net_io_counters().keys()
    ret = {}
    for name in names:
        try:
            mtu = cext_posix.net_if_mtu(name)
            flags = cext_posix.net_if_flags(name)
            duplex, speed = cext.net_if_duplex_speed(name)
        except OSError as err:
            # 024150.python.pslinux.line1052.comment https://github.com/giampaolo/psutil/issues/1279
            if err.errno != errno.ENODEV:
                raise
            debug(err)
        else:
            output_flags = ','.join(flags)
            isup = 'running' in flags
            ret[name] = _common.snicstats(
                isup, duplex_map[duplex], speed, mtu, output_flags
            )
    return ret


# 024151.python.pslinux.line1065.comment =====================================================================
# 024152.python.pslinux.line1066.comment --- disks
# 024153.python.pslinux.line1067.comment =====================================================================


disk_usage = _psposix.disk_usage


def disk_io_counters(perdisk=False):
    """Return disk I/O statistics for every disk installed on the
    system as a dict of raw tuples.
    """

    def read_procfs():
        # 024154.python.pslinux.line1079.comment OK, this is a bit confusing. The format of /proc/diskstats can
        # 024155.python.pslinux.line1080.comment have 3 variations.
        # 024156.python.pslinux.line1081.comment On Linux 2.4 each line has always 15 fields, e.g.:
        # 024157.python.pslinux.line1082.comment "3     0   8 hda 8 8 8 8 8 8 8 8 8 8 8"
        # 024158.python.pslinux.line1083.comment On Linux 2.6+ each line *usually* has 14 fields, and the disk
        # 024159.python.pslinux.line1084.comment name is in another position, like this:
        # 024160.python.pslinux.line1085.comment "3    0   hda 8 8 8 8 8 8 8 8 8 8 8"
        # 024161.python.pslinux.line1086.comment ...unless (Linux 2.6) the line refers to a partition instead
        # 024162.python.pslinux.line1087.comment of a disk, in which case the line has less fields (7):
        # 024163.python.pslinux.line1088.comment "3    1   hda1 8 8 8 8"
        # 024164.python.pslinux.line1089.comment 4.18+ has 4 fields added:
        # 024165.python.pslinux.line1090.comment "3    0   hda 8 8 8 8 8 8 8 8 8 8 8 0 0 0 0"
        # 024166.python.pslinux.line1091.comment 5.5 has 2 more fields.
        # 024167.python.pslinux.line1092.comment See:
        # 024168.python.pslinux.line1093.comment https://www.kernel.org/doc/Documentation/iostats.txt
        # 024169.python.pslinux.line1094.comment https://www.kernel.org/doc/Documentation/ABI/testing/procfs-diskstats
        with open_text(f"{get_procfs_path()}/diskstats") as f:
            lines = f.readlines()
        for line in lines:
            fields = line.split()
            flen = len(fields)
            # 024170.python.pslinux.line1100.comment fmt: off
            if flen == 15:
                # 024171.python.pslinux.line1102.comment Linux 2.4
                name = fields[3]
                reads = int(fields[2])
                (reads_merged, rbytes, rtime, writes, writes_merged,
                    wbytes, wtime, _, busy_time, _) = map(int, fields[4:14])
            elif flen == 14 or flen >= 18:
                # 024172.python.pslinux.line1108.comment Linux 2.6+, line referring to a disk
                name = fields[2]
                (reads, reads_merged, rbytes, rtime, writes, writes_merged,
                    wbytes, wtime, _, busy_time, _) = map(int, fields[3:14])
            elif flen == 7:
                # 024173.python.pslinux.line1113.comment Linux 2.6+, line referring to a partition
                name = fields[2]
                reads, rbytes, writes, wbytes = map(int, fields[3:])
                rtime = wtime = reads_merged = writes_merged = busy_time = 0
            else:
                msg = f"not sure how to interpret line {line!r}"
                raise ValueError(msg)
            yield (name, reads, writes, rbytes, wbytes, rtime, wtime,
                   reads_merged, writes_merged, busy_time)
            # 024174.python.pslinux.line1122.comment fmt: on

    def read_sysfs():
        for block in os.listdir('/sys/block'):
            for root, _, files in os.walk(os.path.join('/sys/block', block)):
                if 'stat' not in files:
                    continue
                with open_text(os.path.join(root, 'stat')) as f:
                    fields = f.read().strip().split()
                name = os.path.basename(root)
                # 024175.python.pslinux.line1132.comment fmt: off
                (reads, reads_merged, rbytes, rtime, writes, writes_merged,
                    wbytes, wtime, _, busy_time) = map(int, fields[:10])
                yield (name, reads, writes, rbytes, wbytes, rtime,
                       wtime, reads_merged, writes_merged, busy_time)
                # 024176.python.pslinux.line1137.comment fmt: on

    if os.path.exists(f"{get_procfs_path()}/diskstats"):
        gen = read_procfs()
    elif os.path.exists('/sys/block'):
        gen = read_sysfs()
    else:
        msg = (
            f"{get_procfs_path()}/diskstats nor /sys/block are available on"
            " this system"
        )
        raise NotImplementedError(msg)

    retdict = {}
    for entry in gen:
        # 024177.python.pslinux.line1152.comment fmt: off
        (name, reads, writes, rbytes, wbytes, rtime, wtime, reads_merged,
            writes_merged, busy_time) = entry
        if not perdisk and not is_storage_device(name):
            # 024178.python.pslinux.line1156.comment perdisk=False means we want to calculate totals so we skip
            # 024179.python.pslinux.line1157.comment partitions (e.g. 'sda1', 'nvme0n1p1') and only include
            # 024180.python.pslinux.line1158.comment base disk devices (e.g. 'sda', 'nvme0n1'). Base disks
            # 024181.python.pslinux.line1159.comment include a total of all their partitions + some extra size
            # 024182.python.pslinux.line1160.comment of their own:
            # 024183.python.pslinux.line1161.comment $ cat /proc/diskstats
            # 024184.python.pslinux.line1162.comment 259       0 sda 10485760 ...
            # 024185.python.pslinux.line1163.comment 259       1 sda1 5186039 ...
            # 024186.python.pslinux.line1164.comment 259       1 sda2 5082039 ...
            # 024187.python.pslinux.line1165.comment See:
            # 024188.python.pslinux.line1166.comment https://github.com/giampaolo/psutil/pull/1313
            continue

        rbytes *= DISK_SECTOR_SIZE
        wbytes *= DISK_SECTOR_SIZE
        retdict[name] = (reads, writes, rbytes, wbytes, rtime, wtime,
                         reads_merged, writes_merged, busy_time)
        # 024189.python.pslinux.line1173.comment fmt: on

    return retdict


class RootFsDeviceFinder:
    """disk_partitions() may return partitions with device == "/dev/root"
    or "rootfs". This container class uses different strategies to try to
    obtain the real device path. Resources:
    https://bootlin.com/blog/find-root-device/
    https://www.systutorials.com/how-to-find-the-disk-where-root-is-on-in-bash-on-linux/.
    """

    __slots__ = ['major', 'minor']

    def __init__(self):
        dev = os.stat("/").st_dev
        self.major = os.major(dev)
        self.minor = os.minor(dev)

    def ask_proc_partitions(self):
        with open_text(f"{get_procfs_path()}/partitions") as f:
            for line in f.readlines()[2:]:
                fields = line.split()
                if len(fields) < 4:  # just for extra safety
                    continue
                major = int(fields[0]) if fields[0].isdigit() else None
                minor = int(fields[1]) if fields[1].isdigit() else None
                name = fields[3]
                if major == self.major and minor == self.minor:
                    if name:  # just for extra safety
                        return f"/dev/{name}"

    def ask_sys_dev_block(self):
        path = f"/sys/dev/block/{self.major}:{self.minor}/uevent"
        with open_text(path) as f:
            for line in f:
                if line.startswith("DEVNAME="):
                    name = line.strip().rpartition("DEVNAME=")[2]
                    if name:  # just for extra safety
                        return f"/dev/{name}"

    def ask_sys_class_block(self):
        needle = f"{self.major}:{self.minor}"
        files = glob.iglob("/sys/class/block/*/dev")
        for file in files:
            try:
                f = open_text(file)
            except FileNotFoundError:  # race condition
                continue
            else:
                with f:
                    data = f.read().strip()
                    if data == needle:
                        name = os.path.basename(os.path.dirname(file))
                        return f"/dev/{name}"

    def find(self):
        path = None
        if path is None:
            try:
                path = self.ask_proc_partitions()
            except OSError as err:
                debug(err)
        if path is None:
            try:
                path = self.ask_sys_dev_block()
            except OSError as err:
                debug(err)
        if path is None:
            try:
                path = self.ask_sys_class_block()
            except OSError as err:
                debug(err)
        # 024194.python.pslinux.line1247.comment We use exists() because the "/dev/*" part of the path is hard
        # 024195.python.pslinux.line1248.comment coded, so we want to be sure.
        if path is not None and os.path.exists(path):
            return path


def disk_partitions(all=False):
    """Return mounted disk partitions as a list of namedtuples."""
    fstypes = set()
    procfs_path = get_procfs_path()
    if not all:
        with open_text(f"{procfs_path}/filesystems") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("nodev"):
                    fstypes.add(line.strip())
                else:
                    # 024196.python.pslinux.line1264.comment ignore all lines starting with "nodev" except "nodev zfs"
                    fstype = line.split("\t")[1]
                    if fstype == "zfs":
                        fstypes.add("zfs")

    # 024197.python.pslinux.line1269.comment See: https://github.com/giampaolo/psutil/issues/1307
    if procfs_path == "/proc" and os.path.isfile('/etc/mtab'):
        mounts_path = os.path.realpath("/etc/mtab")
    else:
        mounts_path = os.path.realpath(f"{procfs_path}/self/mounts")

    retlist = []
    partitions = cext.disk_partitions(mounts_path)
    for partition in partitions:
        device, mountpoint, fstype, opts = partition
        if device == 'none':
            device = ''
        if device in {"/dev/root", "rootfs"}:
            device = RootFsDeviceFinder().find() or device
        if not all:
            if not device or fstype not in fstypes:
                continue
        ntuple = _common.sdiskpart(device, mountpoint, fstype, opts)
        retlist.append(ntuple)

    return retlist


# 024198.python.pslinux.line1292.comment =====================================================================
# 024199.python.pslinux.line1293.comment --- sensors
# 024200.python.pslinux.line1294.comment =====================================================================


def sensors_temperatures():
    """Return hardware (CPU and others) temperatures as a dict
    including hardware name, label, current, max and critical
    temperatures.

    Implementation notes:
    - /sys/class/hwmon looks like the most recent interface to
      retrieve this info, and this implementation relies on it
      only (old distros will probably use something else)
    - lm-sensors on Ubuntu 16.04 relies on /sys/class/hwmon
    - /sys/class/thermal/thermal_zone* is another one but it's more
      difficult to parse
    """
    ret = collections.defaultdict(list)
    basenames = glob.glob('/sys/class/hwmon/hwmon*/temp*_*')
    # 024201.python.pslinux.line1312.comment CentOS has an intermediate /device directory:
    # 024202.python.pslinux.line1313.comment https://github.com/giampaolo/psutil/issues/971
    # 024203.python.pslinux.line1314.comment https://github.com/nicolargo/glances/issues/1060
    basenames.extend(glob.glob('/sys/class/hwmon/hwmon*/device/temp*_*'))
    basenames = sorted({x.split('_')[0] for x in basenames})

    # 024204.python.pslinux.line1318.comment Only add the coretemp hwmon entries if they're not already in
    # 024205.python.pslinux.line1319.comment /sys/class/hwmon/
    # 024206.python.pslinux.line1320.comment https://github.com/giampaolo/psutil/issues/1708
    # 024207.python.pslinux.line1321.comment https://github.com/giampaolo/psutil/pull/1648
    basenames2 = glob.glob(
        '/sys/devices/platform/coretemp.*/hwmon/hwmon*/temp*_*'
    )
    repl = re.compile(r"/sys/devices/platform/coretemp.*/hwmon/")
    for name in basenames2:
        altname = repl.sub('/sys/class/hwmon/', name)
        if altname not in basenames:
            basenames.append(name)

    for base in basenames:
        try:
            path = base + '_input'
            current = float(bcat(path)) / 1000.0
            path = os.path.join(os.path.dirname(base), 'name')
            unit_name = cat(path).strip()
        except (OSError, ValueError):
            # 024208.python.pslinux.line1338.comment A lot of things can go wrong here, so let's just skip the
            # 024209.python.pslinux.line1339.comment whole entry. Sure thing is Linux's /sys/class/hwmon really
            # 024210.python.pslinux.line1340.comment is a stinky broken mess.
            # 024211.python.pslinux.line1341.comment https://github.com/giampaolo/psutil/issues/1009
            # 024212.python.pslinux.line1342.comment https://github.com/giampaolo/psutil/issues/1101
            # 024213.python.pslinux.line1343.comment https://github.com/giampaolo/psutil/issues/1129
            # 024214.python.pslinux.line1344.comment https://github.com/giampaolo/psutil/issues/1245
            # 024215.python.pslinux.line1345.comment https://github.com/giampaolo/psutil/issues/1323
            continue

        high = bcat(base + '_max', fallback=None)
        critical = bcat(base + '_crit', fallback=None)
        label = cat(base + '_label', fallback='').strip()

        if high is not None:
            try:
                high = float(high) / 1000.0
            except ValueError:
                high = None
        if critical is not None:
            try:
                critical = float(critical) / 1000.0
            except ValueError:
                critical = None

        ret[unit_name].append((label, current, high, critical))

    # 024216.python.pslinux.line1365.comment Indication that no sensors were detected in /sys/class/hwmon/
    if not basenames:
        basenames = glob.glob('/sys/class/thermal/thermal_zone*')
        basenames = sorted(set(basenames))

        for base in basenames:
            try:
                path = os.path.join(base, 'temp')
                current = float(bcat(path)) / 1000.0
                path = os.path.join(base, 'type')
                unit_name = cat(path).strip()
            except (OSError, ValueError) as err:
                debug(err)
                continue

            trip_paths = glob.glob(base + '/trip_point*')
            trip_points = {
                '_'.join(os.path.basename(p).split('_')[0:3])
                for p in trip_paths
            }
            critical = None
            high = None
            for trip_point in trip_points:
                path = os.path.join(base, trip_point + "_type")
                trip_type = cat(path, fallback='').strip()
                if trip_type == 'critical':
                    critical = bcat(
                        os.path.join(base, trip_point + "_temp"), fallback=None
                    )
                elif trip_type == 'high':
                    high = bcat(
                        os.path.join(base, trip_point + "_temp"), fallback=None
                    )

                if high is not None:
                    try:
                        high = float(high) / 1000.0
                    except ValueError:
                        high = None
                if critical is not None:
                    try:
                        critical = float(critical) / 1000.0
                    except ValueError:
                        critical = None

            ret[unit_name].append(('', current, high, critical))

    return dict(ret)


def sensors_fans():
    """Return hardware fans info (for CPU and other peripherals) as a
    dict including hardware label and current speed.

    Implementation notes:
    - /sys/class/hwmon looks like the most recent interface to
      retrieve this info, and this implementation relies on it
      only (old distros will probably use something else)
    - lm-sensors on Ubuntu 16.04 relies on /sys/class/hwmon
    """
    ret = collections.defaultdict(list)
    basenames = glob.glob('/sys/class/hwmon/hwmon*/fan*_*')
    if not basenames:
        # 024217.python.pslinux.line1428.comment CentOS has an intermediate /device directory:
        # 024218.python.pslinux.line1429.comment https://github.com/giampaolo/psutil/issues/971
        basenames = glob.glob('/sys/class/hwmon/hwmon*/device/fan*_*')

    basenames = sorted({x.split("_")[0] for x in basenames})
    for base in basenames:
        try:
            current = int(bcat(base + '_input'))
        except OSError as err:
            debug(err)
            continue
        unit_name = cat(os.path.join(os.path.dirname(base), 'name')).strip()
        label = cat(base + '_label', fallback='').strip()
        ret[unit_name].append(_common.sfan(label, current))

    return dict(ret)


def sensors_battery():
    """Return battery information.
    Implementation note: it appears /sys/class/power_supply/BAT0/
    directory structure may vary and provide files with the same
    meaning but under different names, see:
    https://github.com/giampaolo/psutil/issues/966.
    """
    null = object()

    def multi_bcat(*paths):
        """Attempt to read the content of multiple files which may
        not exist. If none of them exist return None.
        """
        for path in paths:
            ret = bcat(path, fallback=null)
            if ret != null:
                try:
                    return int(ret)
                except ValueError:
                    return ret.strip()
        return None

    bats = [
        x
        for x in os.listdir(POWER_SUPPLY_PATH)
        if x.startswith('BAT') or 'battery' in x.lower()
    ]
    if not bats:
        return None
    # 024219.python.pslinux.line1475.comment Get the first available battery. Usually this is "BAT0", except
    # 024220.python.pslinux.line1476.comment some rare exceptions:
    # 024221.python.pslinux.line1477.comment https://github.com/giampaolo/psutil/issues/1238
    root = os.path.join(POWER_SUPPLY_PATH, min(bats))

    # 024222.python.pslinux.line1480.comment Base metrics.
    energy_now = multi_bcat(root + "/energy_now", root + "/charge_now")
    power_now = multi_bcat(root + "/power_now", root + "/current_now")
    energy_full = multi_bcat(root + "/energy_full", root + "/charge_full")
    time_to_empty = multi_bcat(root + "/time_to_empty_now")

    # 024223.python.pslinux.line1486.comment Percent. If we have energy_full the percentage will be more
    # 024224.python.pslinux.line1487.comment accurate compared to reading /capacity file (float vs. int).
    if energy_full is not None and energy_now is not None:
        try:
            percent = 100.0 * energy_now / energy_full
        except ZeroDivisionError:
            percent = 0.0
    else:
        percent = int(cat(root + "/capacity", fallback=-1))
        if percent == -1:
            return None

    # 024225.python.pslinux.line1498.comment Is AC power cable plugged in?
    # 024226.python.pslinux.line1499.comment Note: AC0 is not always available and sometimes (e.g. CentOS7)
    # 024227.python.pslinux.line1500.comment it's called "AC".
    power_plugged = None
    online = multi_bcat(
        os.path.join(POWER_SUPPLY_PATH, "AC0/online"),
        os.path.join(POWER_SUPPLY_PATH, "AC/online"),
    )
    if online is not None:
        power_plugged = online == 1
    else:
        status = cat(root + "/status", fallback="").strip().lower()
        if status == "discharging":
            power_plugged = False
        elif status in {"charging", "full"}:
            power_plugged = True

    # 024228.python.pslinux.line1515.comment Seconds left.
    # 024229.python.pslinux.line1516.comment Note to self: we may also calculate the charging ETA as per:
    # 024230.python.pslinux.line1517.comment https://github.com/thialfihar/dotfiles/blob/
    # 024231.python.pslinux.line1518.comment 013937745fd9050c30146290e8f963d65c0179e6/bin/battery.py#L55
    if power_plugged:
        secsleft = _common.POWER_TIME_UNLIMITED
    elif energy_now is not None and power_now is not None:
        try:
            secsleft = int(energy_now / abs(power_now) * 3600)
        except ZeroDivisionError:
            secsleft = _common.POWER_TIME_UNKNOWN
    elif time_to_empty is not None:
        secsleft = int(time_to_empty * 60)
        if secsleft < 0:
            secsleft = _common.POWER_TIME_UNKNOWN
    else:
        secsleft = _common.POWER_TIME_UNKNOWN

    return _common.sbattery(percent, secsleft, power_plugged)


# 024232.python.pslinux.line1536.comment =====================================================================
# 024233.python.pslinux.line1537.comment --- other system functions
# 024234.python.pslinux.line1538.comment =====================================================================


def users():
    """Return currently connected users as a list of namedtuples."""
    retlist = []
    rawlist = cext_posix.users()
    for item in rawlist:
        user, tty, hostname, tstamp, pid = item
        nt = _common.suser(user, tty or None, hostname, tstamp, pid)
        retlist.append(nt)
    return retlist


def boot_time():
    """Return the system boot time expressed in seconds since the epoch."""
    path = f"{get_procfs_path()}/stat"
    with open_binary(path) as f:
        for line in f:
            if line.startswith(b'btime'):
                return float(line.strip().split()[1])
        msg = f"line 'btime' not found in {path}"
        raise RuntimeError(msg)


# 024235.python.pslinux.line1563.comment =====================================================================
# 024236.python.pslinux.line1564.comment --- processes
# 024237.python.pslinux.line1565.comment =====================================================================


def pids():
    """Returns a list of PIDs currently running on the system."""
    path = get_procfs_path().encode(ENCODING)
    return [int(x) for x in os.listdir(path) if x.isdigit()]


def pid_exists(pid):
    """Check for the existence of a unix PID. Linux TIDs are not
    supported (always return False).
    """
    if not _psposix.pid_exists(pid):
        return False
    else:
        # 024238.python.pslinux.line1581.comment Linux's apparently does not distinguish between PIDs and TIDs
        # 024239.python.pslinux.line1582.comment (thread IDs).
        # 024240.python.pslinux.line1583.comment listdir("/proc") won't show any TID (only PIDs) but
        # 024241.python.pslinux.line1584.comment os.stat("/proc/{tid}") will succeed if {tid} exists.
        # 024242.python.pslinux.line1585.comment os.kill() can also be passed a TID. This is quite confusing.
        # 024243.python.pslinux.line1586.comment In here we want to enforce this distinction and support PIDs
        # 024244.python.pslinux.line1587.comment only, see:
        # 024245.python.pslinux.line1588.comment https://github.com/giampaolo/psutil/issues/687
        try:
            # 024246.python.pslinux.line1590.comment Note: already checked that this is faster than using a
            # 024247.python.pslinux.line1591.comment regular expr. Also (a lot) faster than doing
            # 024248.python.pslinux.line1592.comment 'return pid in pids()'
            path = f"{get_procfs_path()}/{pid}/status"
            with open_binary(path) as f:
                for line in f:
                    if line.startswith(b"Tgid:"):
                        tgid = int(line.split()[1])
                        # 024249.python.pslinux.line1598.comment If tgid and pid are the same then we're
                        # 024250.python.pslinux.line1599.comment dealing with a process PID.
                        return tgid == pid
                msg = f"'Tgid' line not found in {path}"
                raise ValueError(msg)
        except (OSError, ValueError):
            return pid in pids()


def ppid_map():
    """Obtain a {pid: ppid, ...} dict for all running processes in
    one shot. Used to speed up Process.children().
    """
    ret = {}
    procfs_path = get_procfs_path()
    for pid in pids():
        try:
            with open_binary(f"{procfs_path}/{pid}/stat") as f:
                data = f.read()
        except (FileNotFoundError, ProcessLookupError):
            pass
        except PermissionError as err:
            raise AccessDenied(pid) from err
        else:
            rpar = data.rfind(b')')
            dset = data[rpar + 2 :].split()
            ppid = int(dset[1])
            ret[pid] = ppid
    return ret


def wrap_exceptions(fun):
    """Decorator which translates bare OSError and OSError exceptions
    into NoSuchProcess and AccessDenied.
    """

    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        pid, name = self.pid, self._name
        try:
            return fun(self, *args, **kwargs)
        except PermissionError as err:
            raise AccessDenied(pid, name) from err
        except ProcessLookupError as err:
            self._raise_if_zombie()
            raise NoSuchProcess(pid, name) from err
        except FileNotFoundError as err:
            self._raise_if_zombie()
            # 024251.python.pslinux.line1646.comment /proc/PID directory may still exist, but the files within
            # 024252.python.pslinux.line1647.comment it may not, indicating the process is gone, see:
            # 024253.python.pslinux.line1648.comment https://github.com/giampaolo/psutil/issues/2418
            if not os.path.exists(f"{self._procfs_path}/{pid}/stat"):
                raise NoSuchProcess(pid, name) from err
            raise

    return wrapper


class Process:
    """Linux process implementation."""

    __slots__ = [
        "_cache",
        "_ctime",
        "_name",
        "_ppid",
        "_procfs_path",
        "pid",
    ]

    def __init__(self, pid):
        self.pid = pid
        self._name = None
        self._ppid = None
        self._ctime = None
        self._procfs_path = get_procfs_path()

    def _is_zombie(self):
        # 024254.python.pslinux.line1676.comment Note: most of the times Linux is able to return info about the
        # 024255.python.pslinux.line1677.comment process even if it's a zombie, and /proc/{pid} will exist.
        # 024256.python.pslinux.line1678.comment There are some exceptions though, like exe(), cmdline() and
        # 024257.python.pslinux.line1679.comment memory_maps(). In these cases /proc/{pid}/{file} exists but
        # 024258.python.pslinux.line1680.comment it's empty. Instead of returning a "null" value we'll raise an
        # 024259.python.pslinux.line1681.comment exception.
        try:
            data = bcat(f"{self._procfs_path}/{self.pid}/stat")
        except OSError:
            return False
        else:
            rpar = data.rfind(b')')
            status = data[rpar + 2 : rpar + 3]
            return status == b"Z"

    def _raise_if_zombie(self):
        if self._is_zombie():
            raise ZombieProcess(self.pid, self._name, self._ppid)

    def _raise_if_not_alive(self):
        """Raise NSP if the process disappeared on us."""
        # 024260.python.pslinux.line1697.comment For those C function who do not raise NSP, possibly returning
        # 024261.python.pslinux.line1698.comment incorrect or incomplete result.
        os.stat(f"{self._procfs_path}/{self.pid}")

    def _readlink(self, path, fallback=UNSET):
        # 024262.python.pslinux.line1702.comment * https://github.com/giampaolo/psutil/issues/503
        # 024263.python.pslinux.line1703.comment os.readlink('/proc/pid/exe') may raise ESRCH (ProcessLookupError)
        # 024264.python.pslinux.line1704.comment instead of ENOENT (FileNotFoundError) when it races.
        # 024265.python.pslinux.line1705.comment * ENOENT may occur also if the path actually exists if PID is
        # 024266.python.pslinux.line1706.comment a low PID (~0-20 range).
        # 024267.python.pslinux.line1707.comment * https://github.com/giampaolo/psutil/issues/2514
        try:
            return readlink(path)
        except (FileNotFoundError, ProcessLookupError):
            if os.path.lexists(f"{self._procfs_path}/{self.pid}"):
                self._raise_if_zombie()
                if fallback is not UNSET:
                    return fallback
            raise

    @wrap_exceptions
    @memoize_when_activated
    def _parse_stat_file(self):
        """Parse /proc/{pid}/stat file and return a dict with various
        process info.
        Using "man proc" as a reference: where "man proc" refers to
        position N always subtract 3 (e.g ppid position 4 in
        'man proc' == position 1 in here).
        The return value is cached in case oneshot() ctx manager is
        in use.
        """
        data = bcat(f"{self._procfs_path}/{self.pid}/stat")
        # 024268.python.pslinux.line1729.comment Process name is between parentheses. It can contain spaces and
        # 024269.python.pslinux.line1730.comment other parentheses. This is taken into account by looking for
        # 024270.python.pslinux.line1731.comment the first occurrence of "(" and the last occurrence of ")".
        rpar = data.rfind(b')')
        name = data[data.find(b'(') + 1 : rpar]
        fields = data[rpar + 2 :].split()

        ret = {}
        ret['name'] = name
        ret['status'] = fields[0]
        ret['ppid'] = fields[1]
        ret['ttynr'] = fields[4]
        ret['utime'] = fields[11]
        ret['stime'] = fields[12]
        ret['children_utime'] = fields[13]
        ret['children_stime'] = fields[14]
        ret['create_time'] = fields[19]
        ret['cpu_num'] = fields[36]
        try:
            ret['blkio_ticks'] = fields[39]  # aka 'delayacct_blkio_ticks'
        except IndexError:
            # 024272.python.pslinux.line1750.comment https://github.com/giampaolo/psutil/issues/2455
            debug("can't get blkio_ticks, set iowait to 0")
            ret['blkio_ticks'] = 0

        return ret

    @wrap_exceptions
    @memoize_when_activated
    def _read_status_file(self):
        """Read /proc/{pid}/stat file and return its content.
        The return value is cached in case oneshot() ctx manager is
        in use.
        """
        with open_binary(f"{self._procfs_path}/{self.pid}/status") as f:
            return f.read()

    @wrap_exceptions
    @memoize_when_activated
    def _read_smaps_file(self):
        with open_binary(f"{self._procfs_path}/{self.pid}/smaps") as f:
            return f.read().strip()

    def oneshot_enter(self):
        self._parse_stat_file.cache_activate(self)
        self._read_status_file.cache_activate(self)
        self._read_smaps_file.cache_activate(self)

    def oneshot_exit(self):
        self._parse_stat_file.cache_deactivate(self)
        self._read_status_file.cache_deactivate(self)
        self._read_smaps_file.cache_deactivate(self)

    @wrap_exceptions
    def name(self):
        # 024273.python.pslinux.line1784.comment XXX - gets changed later and probably needs refactoring
        return decode(self._parse_stat_file()['name'])

    @wrap_exceptions
    def exe(self):
        return self._readlink(
            f"{self._procfs_path}/{self.pid}/exe", fallback=""
        )

    @wrap_exceptions
    def cmdline(self):
        with open_text(f"{self._procfs_path}/{self.pid}/cmdline") as f:
            data = f.read()
        if not data:
            # 024274.python.pslinux.line1798.comment may happen in case of zombie process
            self._raise_if_zombie()
            return []
        # 024275.python.pslinux.line1801.comment 'man proc' states that args are separated by null bytes '\0'
        # 024276.python.pslinux.line1802.comment and last char is supposed to be a null byte. Nevertheless
        # 024277.python.pslinux.line1803.comment some processes may change their cmdline after being started
        # 024278.python.pslinux.line1804.comment (via setproctitle() or similar), they are usually not
        # 024279.python.pslinux.line1805.comment compliant with this rule and use spaces instead. Google
        # 024280.python.pslinux.line1806.comment Chrome process is an example. See:
        # 024281.python.pslinux.line1807.comment https://github.com/giampaolo/psutil/issues/1179
        sep = '\x00' if data.endswith('\x00') else ' '
        if data.endswith(sep):
            data = data[:-1]
        cmdline = data.split(sep)
        # 024282.python.pslinux.line1812.comment Sometimes last char is a null byte '\0' but the args are
        # 024283.python.pslinux.line1813.comment separated by spaces, see: https://github.com/giampaolo/psutil/
        # 024284.python.pslinux.line1814.comment issues/1179#issuecomment-552984549
        if sep == '\x00' and len(cmdline) == 1 and ' ' in data:
            cmdline = data.split(' ')
        return cmdline

    @wrap_exceptions
    def environ(self):
        with open_text(f"{self._procfs_path}/{self.pid}/environ") as f:
            data = f.read()
        return parse_environ_block(data)

    @wrap_exceptions
    def terminal(self):
        tty_nr = int(self._parse_stat_file()['ttynr'])
        tmap = _psposix.get_terminal_map()
        try:
            return tmap[tty_nr]
        except KeyError:
            return None

    # 024285.python.pslinux.line1834.comment May not be available on old kernels.
    if os.path.exists(f"/proc/{os.getpid()}/io"):

        @wrap_exceptions
        def io_counters(self):
            fname = f"{self._procfs_path}/{self.pid}/io"
            fields = {}
            with open_binary(fname) as f:
                for line in f:
                    # 024286.python.pslinux.line1843.comment https://github.com/giampaolo/psutil/issues/1004
                    line = line.strip()
                    if line:
                        try:
                            name, value = line.split(b': ')
                        except ValueError:
                            # 024287.python.pslinux.line1849.comment https://github.com/giampaolo/psutil/issues/1004
                            continue
                        else:
                            fields[name] = int(value)
            if not fields:
                msg = f"{fname} file was empty"
                raise RuntimeError(msg)
            try:
                return pio(
                    fields[b'syscr'],  # read syscalls
                    fields[b'syscw'],  # write syscalls
                    fields[b'read_bytes'],  # read bytes
                    fields[b'write_bytes'],  # write bytes
                    fields[b'rchar'],  # read chars
                    fields[b'wchar'],  # write chars
                )
            except KeyError as err:
                msg = (
                    f"{err.args[0]!r} field was not found in {fname}; found"
                    f" fields are {fields!r}"
                )
                raise ValueError(msg) from None

    @wrap_exceptions
    def cpu_times(self):
        values = self._parse_stat_file()
        utime = float(values['utime']) / CLOCK_TICKS
        stime = float(values['stime']) / CLOCK_TICKS
        children_utime = float(values['children_utime']) / CLOCK_TICKS
        children_stime = float(values['children_stime']) / CLOCK_TICKS
        iowait = float(values['blkio_ticks']) / CLOCK_TICKS
        return pcputimes(utime, stime, children_utime, children_stime, iowait)

    @wrap_exceptions
    def cpu_num(self):
        """What CPU the process is on."""
        return int(self._parse_stat_file()['cpu_num'])

    @wrap_exceptions
    def wait(self, timeout=None):
        return _psposix.wait_pid(self.pid, timeout, self._name)

    @wrap_exceptions
    def create_time(self, monotonic=False):
        # 024294.python.pslinux.line1893.comment The 'starttime' field in /proc/[pid]/stat is expressed in
        # 024295.python.pslinux.line1894.comment jiffies (clock ticks per second), a relative value which
        # 024296.python.pslinux.line1895.comment represents the number of clock ticks that have passed since
        # 024297.python.pslinux.line1896.comment the system booted until the process was created. It never
        # 024298.python.pslinux.line1897.comment changes and is unaffected by system clock updates.
        if self._ctime is None:
            self._ctime = (
                float(self._parse_stat_file()['create_time']) / CLOCK_TICKS
            )
        if monotonic:
            return self._ctime
        # 024299.python.pslinux.line1904.comment Add the boot time, returning time expressed in seconds since
        # 024300.python.pslinux.line1905.comment the epoch. This is subject to system clock updates.
        return self._ctime + boot_time()

    @wrap_exceptions
    def memory_info(self):
        # 024301.python.pslinux.line1910.comment ============================================================
        # 024302.python.pslinux.line1911.comment | FIELD  | DESCRIPTION                         | AKA  | TOP  |
        # 024303.python.pslinux.line1912.comment ============================================================
        # 024304.python.pslinux.line1913.comment | rss    | resident set size                   |      | RES  |
        # 024305.python.pslinux.line1914.comment | vms    | total program size                  | size | VIRT |
        # 024306.python.pslinux.line1915.comment | shared | shared pages (from shared mappings) |      | SHR  |
        # 024307.python.pslinux.line1916.comment | text   | text ('code')                       | trs  | CODE |
        # 024308.python.pslinux.line1917.comment | lib    | library (unused in Linux 2.6)       | lrs  |      |
        # 024309.python.pslinux.line1918.comment | data   | data + stack                        | drs  | DATA |
        # 024310.python.pslinux.line1919.comment | dirty  | dirty pages (unused in Linux 2.6)   | dt   |      |
        # 024311.python.pslinux.line1920.comment ============================================================
        with open_binary(f"{self._procfs_path}/{self.pid}/statm") as f:
            vms, rss, shared, text, lib, data, dirty = (
                int(x) * PAGESIZE for x in f.readline().split()[:7]
            )
        return pmem(rss, vms, shared, text, lib, data, dirty)

    if HAS_PROC_SMAPS_ROLLUP or HAS_PROC_SMAPS:

        def _parse_smaps_rollup(self):
            # 024312.python.pslinux.line1930.comment /proc/pid/smaps_rollup was added to Linux in 2017. Faster
            # 024313.python.pslinux.line1931.comment than /proc/pid/smaps. It reports higher PSS than */smaps
            # 024314.python.pslinux.line1932.comment (from 1k up to 200k higher; tested against all processes).
            # 024315.python.pslinux.line1933.comment IMPORTANT: /proc/pid/smaps_rollup is weird, because it
            # 024316.python.pslinux.line1934.comment raises ESRCH / ENOENT for many PIDs, even if they're alive
            # 024317.python.pslinux.line1935.comment (also as root). In that case we'll use /proc/pid/smaps as
            # 024318.python.pslinux.line1936.comment fallback, which is slower but has a +50% success rate
            # 024319.python.pslinux.line1937.comment compared to /proc/pid/smaps_rollup.
            uss = pss = swap = 0
            with open_binary(
                f"{self._procfs_path}/{self.pid}/smaps_rollup"
            ) as f:
                for line in f:
                    if line.startswith(b"Private_"):
                        # 024320.python.pslinux.line1944.comment Private_Clean, Private_Dirty, Private_Hugetlb
                        uss += int(line.split()[1]) * 1024
                    elif line.startswith(b"Pss:"):
                        pss = int(line.split()[1]) * 1024
                    elif line.startswith(b"Swap:"):
                        swap = int(line.split()[1]) * 1024
            return (uss, pss, swap)

        @wrap_exceptions
        def _parse_smaps(
            self,
            # 024321.python.pslinux.line1955.comment Gets Private_Clean, Private_Dirty, Private_Hugetlb.
            _private_re=re.compile(br"\nPrivate.*:\s+(\d+)"),
            _pss_re=re.compile(br"\nPss\:\s+(\d+)"),
            _swap_re=re.compile(br"\nSwap\:\s+(\d+)"),
        ):
            # 024322.python.pslinux.line1960.comment /proc/pid/smaps does not exist on kernels < 2.6.14 or if
            # 024323.python.pslinux.line1961.comment CONFIG_MMU kernel configuration option is not enabled.

            # 024324.python.pslinux.line1963.comment Note: using 3 regexes is faster than reading the file
            # 024325.python.pslinux.line1964.comment line by line.
            # 024326.python.pslinux.line1965.comment
            # 024327.python.pslinux.line1966.comment You might be tempted to calculate USS by subtracting
            # 024328.python.pslinux.line1967.comment the "shared" value from the "resident" value in
            # 024329.python.pslinux.line1968.comment /proc/<pid>/statm. But at least on Linux, statm's "shared"
            # 024330.python.pslinux.line1969.comment value actually counts pages backed by files, which has
            # 024331.python.pslinux.line1970.comment little to do with whether the pages are actually shared.
            # 024332.python.pslinux.line1971.comment /proc/self/smaps on the other hand appears to give us the
            # 024333.python.pslinux.line1972.comment correct information.
            smaps_data = self._read_smaps_file()
            # 024334.python.pslinux.line1974.comment Note: smaps file can be empty for certain processes.
            # 024335.python.pslinux.line1975.comment The code below will not crash though and will result to 0.
            uss = sum(map(int, _private_re.findall(smaps_data))) * 1024
            pss = sum(map(int, _pss_re.findall(smaps_data))) * 1024
            swap = sum(map(int, _swap_re.findall(smaps_data))) * 1024
            return (uss, pss, swap)

        @wrap_exceptions
        def memory_full_info(self):
            if HAS_PROC_SMAPS_ROLLUP:  # faster
                try:
                    uss, pss, swap = self._parse_smaps_rollup()
                except (ProcessLookupError, FileNotFoundError):
                    uss, pss, swap = self._parse_smaps()
            else:
                uss, pss, swap = self._parse_smaps()
            basic_mem = self.memory_info()
            return pfullmem(*basic_mem + (uss, pss, swap))

    else:
        memory_full_info = memory_info

    if HAS_PROC_SMAPS:

        @wrap_exceptions
        def memory_maps(self):
            """Return process's mapped memory regions as a list of named
            tuples. Fields are explained in 'man proc'; here is an updated
            (Apr 2012) version: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/Documentation/filesystems/proc.txt?id=b76437579d1344b612cf1851ae610c636cec7db0.

            /proc/{PID}/smaps does not exist on kernels < 2.6.14 or if
            CONFIG_MMU kernel configuration option is not enabled.
            """

            def get_blocks(lines, current_block):
                data = {}
                for line in lines:
                    fields = line.split(None, 5)
                    if not fields[0].endswith(b':'):
                        # 024337.python.pslinux.line2013.comment new block section
                        yield (current_block.pop(), data)
                        current_block.append(line)
                    else:
                        try:
                            data[fields[0]] = int(fields[1]) * 1024
                        except (ValueError, IndexError):
                            if fields[0].startswith(b'VmFlags:'):
                                # 024338.python.pslinux.line2021.comment see issue #369
                                continue
                            msg = f"don't know how to interpret line {line!r}"
                            raise ValueError(msg) from None
                yield (current_block.pop(), data)

            data = self._read_smaps_file()
            # 024339.python.pslinux.line2028.comment Note: smaps file can be empty for certain processes or for
            # 024340.python.pslinux.line2029.comment zombies.
            if not data:
                self._raise_if_zombie()
                return []
            lines = data.split(b'\n')
            ls = []
            first_line = lines.pop(0)
            current_block = [first_line]
            for header, data in get_blocks(lines, current_block):
                hfields = header.split(None, 5)
                try:
                    addr, perms, _offset, _dev, _inode, path = hfields
                except ValueError:
                    addr, perms, _offset, _dev, _inode, path = hfields + ['']
                if not path:
                    path = '[anon]'
                else:
                    path = decode(path)
                    path = path.strip()
                    if path.endswith(' (deleted)') and not path_exists_strict(
                        path
                    ):
                        path = path[:-10]
                item = (
                    decode(addr),
                    decode(perms),
                    path,
                    data.get(b'Rss:', 0),
                    data.get(b'Size:', 0),
                    data.get(b'Pss:', 0),
                    data.get(b'Shared_Clean:', 0),
                    data.get(b'Shared_Dirty:', 0),
                    data.get(b'Private_Clean:', 0),
                    data.get(b'Private_Dirty:', 0),
                    data.get(b'Referenced:', 0),
                    data.get(b'Anonymous:', 0),
                    data.get(b'Swap:', 0),
                )
                ls.append(item)
            return ls

    @wrap_exceptions
    def cwd(self):
        return self._readlink(
            f"{self._procfs_path}/{self.pid}/cwd", fallback=""
        )

    @wrap_exceptions
    def num_ctx_switches(
        self, _ctxsw_re=re.compile(br'ctxt_switches:\t(\d+)')
    ):
        data = self._read_status_file()
        ctxsw = _ctxsw_re.findall(data)
        if not ctxsw:
            msg = (
                "'voluntary_ctxt_switches' and"
                " 'nonvoluntary_ctxt_switches'lines were not found in"
                f" {self._procfs_path}/{self.pid}/status; the kernel is"
                " probably older than 2.6.23"
            )
            raise NotImplementedError(msg)
        return _common.pctxsw(int(ctxsw[0]), int(ctxsw[1]))

    @wrap_exceptions
    def num_threads(self, _num_threads_re=re.compile(br'Threads:\t(\d+)')):
        # 024341.python.pslinux.line2094.comment Using a re is faster than iterating over file line by line.
        data = self._read_status_file()
        return int(_num_threads_re.findall(data)[0])

    @wrap_exceptions
    def threads(self):
        thread_ids = os.listdir(f"{self._procfs_path}/{self.pid}/task")
        thread_ids.sort()
        retlist = []
        hit_enoent = False
        for thread_id in thread_ids:
            fname = f"{self._procfs_path}/{self.pid}/task/{thread_id}/stat"
            try:
                with open_binary(fname) as f:
                    st = f.read().strip()
            except (FileNotFoundError, ProcessLookupError):
                # 024342.python.pslinux.line2110.comment no such file or directory or no such process;
                # 024343.python.pslinux.line2111.comment it means thread disappeared on us
                hit_enoent = True
                continue
            # 024344.python.pslinux.line2114.comment ignore the first two values ("pid (exe)")
            st = st[st.find(b')') + 2 :]
            values = st.split(b' ')
            utime = float(values[11]) / CLOCK_TICKS
            stime = float(values[12]) / CLOCK_TICKS
            ntuple = _common.pthread(int(thread_id), utime, stime)
            retlist.append(ntuple)
        if hit_enoent:
            self._raise_if_not_alive()
        return retlist

    @wrap_exceptions
    def nice_get(self):
        # 024345.python.pslinux.line2127.comment with open_text(f"{self._procfs_path}/{self.pid}/stat") as f:
        # 024346.python.pslinux.line2128.comment data = f.read()
        # 024347.python.pslinux.line2129.comment return int(data.split()[18])

        # 024348.python.pslinux.line2131.comment Use C implementation
        return cext_posix.getpriority(self.pid)

    @wrap_exceptions
    def nice_set(self, value):
        return cext_posix.setpriority(self.pid, value)

    # 024349.python.pslinux.line2138.comment starting from CentOS 6.
    if HAS_CPU_AFFINITY:

        @wrap_exceptions
        def cpu_affinity_get(self):
            return cext.proc_cpu_affinity_get(self.pid)

        def _get_eligible_cpus(
            self, _re=re.compile(br"Cpus_allowed_list:\t(\d+)-(\d+)")
        ):
            # 024350.python.pslinux.line2148.comment See: https://github.com/giampaolo/psutil/issues/956
            data = self._read_status_file()
            match = _re.findall(data)
            if match:
                return list(range(int(match[0][0]), int(match[0][1]) + 1))
            else:
                return list(range(len(per_cpu_times())))

        @wrap_exceptions
        def cpu_affinity_set(self, cpus):
            try:
                cext.proc_cpu_affinity_set(self.pid, cpus)
            except (OSError, ValueError) as err:
                if isinstance(err, ValueError) or err.errno == errno.EINVAL:
                    eligible_cpus = self._get_eligible_cpus()
                    all_cpus = tuple(range(len(per_cpu_times())))
                    for cpu in cpus:
                        if cpu not in all_cpus:
                            msg = (
                                f"invalid CPU {cpu!r}; choose between"
                                f" {eligible_cpus!r}"
                            )
                            raise ValueError(msg) from None
                        if cpu not in eligible_cpus:
                            msg = (
                                f"CPU number {cpu} is not eligible; choose"
                                f" between {eligible_cpus}"
                            )
                            raise ValueError(msg) from err
                raise

    # 024351.python.pslinux.line2179.comment only starting from kernel 2.6.13
    if HAS_PROC_IO_PRIORITY:

        @wrap_exceptions
        def ionice_get(self):
            ioclass, value = cext.proc_ioprio_get(self.pid)
            ioclass = IOPriority(ioclass)
            return _common.pionice(ioclass, value)

        @wrap_exceptions
        def ionice_set(self, ioclass, value):
            if value is None:
                value = 0
            if value and ioclass in {
                IOPriority.IOPRIO_CLASS_IDLE,
                IOPriority.IOPRIO_CLASS_NONE,
            }:
                msg = f"{ioclass!r} ioclass accepts no value"
                raise ValueError(msg)
            if value < 0 or value > 7:
                msg = "value not in 0-7 range"
                raise ValueError(msg)
            return cext.proc_ioprio_set(self.pid, ioclass, value)

    if hasattr(resource, "prlimit"):

        @wrap_exceptions
        def rlimit(self, resource_, limits=None):
            # 024352.python.pslinux.line2207.comment If pid is 0 prlimit() applies to the calling process and
            # 024353.python.pslinux.line2208.comment we don't want that. We should never get here though as
            # 024354.python.pslinux.line2209.comment PID 0 is not supported on Linux.
            if self.pid == 0:
                msg = "can't use prlimit() against PID 0 process"
                raise ValueError(msg)
            try:
                if limits is None:
                    # 024355.python.pslinux.line2215.comment get
                    return resource.prlimit(self.pid, resource_)
                else:
                    # 024356.python.pslinux.line2218.comment set
                    if len(limits) != 2:
                        msg = (
                            "second argument must be a (soft, hard) "
                            f"tuple, got {limits!r}"
                        )
                        raise ValueError(msg)
                    resource.prlimit(self.pid, resource_, limits)
            except OSError as err:
                if err.errno == errno.ENOSYS:
                    # 024357.python.pslinux.line2228.comment I saw this happening on Travis:
                    # 024358.python.pslinux.line2229.comment https://travis-ci.org/giampaolo/psutil/jobs/51368273
                    self._raise_if_zombie()
                raise

    @wrap_exceptions
    def status(self):
        letter = self._parse_stat_file()['status']
        letter = letter.decode()
        # 024359.python.pslinux.line2237.comment XXX is '?' legit? (we're not supposed to return it anyway)
        return PROC_STATUSES.get(letter, '?')

    @wrap_exceptions
    def open_files(self):
        retlist = []
        files = os.listdir(f"{self._procfs_path}/{self.pid}/fd")
        hit_enoent = False
        for fd in files:
            file = f"{self._procfs_path}/{self.pid}/fd/{fd}"
            try:
                path = readlink(file)
            except (FileNotFoundError, ProcessLookupError):
                # 024360.python.pslinux.line2250.comment ENOENT == file which is gone in the meantime
                hit_enoent = True
                continue
            except OSError as err:
                if err.errno == errno.EINVAL:
                    # 024361.python.pslinux.line2255.comment not a link
                    continue
                if err.errno == errno.ENAMETOOLONG:
                    # 024362.python.pslinux.line2258.comment file name too long
                    debug(err)
                    continue
                raise
            else:
                # 024363.python.pslinux.line2263.comment If path is not an absolute there's no way to tell
                # 024364.python.pslinux.line2264.comment whether it's a regular file or not, so we skip it.
                # 024365.python.pslinux.line2265.comment A regular file is always supposed to be have an
                # 024366.python.pslinux.line2266.comment absolute path though.
                if path.startswith('/') and isfile_strict(path):
                    # 024367.python.pslinux.line2268.comment Get file position and flags.
                    file = f"{self._procfs_path}/{self.pid}/fdinfo/{fd}"
                    try:
                        with open_binary(file) as f:
                            pos = int(f.readline().split()[1])
                            flags = int(f.readline().split()[1], 8)
                    except (FileNotFoundError, ProcessLookupError):
                        # 024368.python.pslinux.line2275.comment fd gone in the meantime; process may
                        # 024369.python.pslinux.line2276.comment still be alive
                        hit_enoent = True
                    else:
                        mode = file_flags_to_mode(flags)
                        ntuple = popenfile(
                            path, int(fd), int(pos), mode, flags
                        )
                        retlist.append(ntuple)
        if hit_enoent:
            self._raise_if_not_alive()
        return retlist

    @wrap_exceptions
    def net_connections(self, kind='inet'):
        ret = _net_connections.retrieve(kind, self.pid)
        self._raise_if_not_alive()
        return ret

    @wrap_exceptions
    def num_fds(self):
        return len(os.listdir(f"{self._procfs_path}/{self.pid}/fd"))

    @wrap_exceptions
    def ppid(self):
        return int(self._parse_stat_file()['ppid'])

    @wrap_exceptions
    def uids(self, _uids_re=re.compile(br'Uid:\t(\d+)\t(\d+)\t(\d+)')):
        data = self._read_status_file()
        real, effective, saved = _uids_re.findall(data)[0]
        return _common.puids(int(real), int(effective), int(saved))

    @wrap_exceptions
    def gids(self, _gids_re=re.compile(br'Gid:\t(\d+)\t(\d+)\t(\d+)')):
        data = self._read_status_file()
        real, effective, saved = _gids_re.findall(data)[0]
        return _common.pgids(int(real), int(effective), int(saved))
