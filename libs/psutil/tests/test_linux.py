#!/usr/bin/env python3

# 025095.python.test_linux.line3.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 025096.python.test_linux.line4.comment Use of this source code is governed by a BSD-style license that can be
# 025097.python.test_linux.line5.comment found in the LICENSE file.

"""Linux specific tests."""


import collections
import contextlib
import errno
import io
import os
import platform
import re
import shutil
import socket
import struct
import textwrap
import time
import warnings
from unittest import mock

import psutil
from psutil import LINUX
from psutil.tests import AARCH64
from psutil.tests import GITHUB_ACTIONS
from psutil.tests import GLOBAL_TIMEOUT
from psutil.tests import HAS_BATTERY
from psutil.tests import HAS_CPU_FREQ
from psutil.tests import HAS_GETLOADAVG
from psutil.tests import HAS_RLIMIT
from psutil.tests import RISCV64
from psutil.tests import TOLERANCE_DISK_USAGE
from psutil.tests import TOLERANCE_SYS_MEM
from psutil.tests import PsutilTestCase
from psutil.tests import ThreadTask
from psutil.tests import call_until
from psutil.tests import pytest
from psutil.tests import reload_module
from psutil.tests import retry_on_failure
from psutil.tests import safe_rmpath
from psutil.tests import sh
from psutil.tests import skip_on_not_implemented

if LINUX:
    from psutil._pslinux import CLOCK_TICKS
    from psutil._pslinux import RootFsDeviceFinder
    from psutil._pslinux import calculate_avail_vmem
    from psutil._pslinux import open_binary


HERE = os.path.abspath(os.path.dirname(__file__))
SIOCGIFADDR = 0x8915
SIOCGIFHWADDR = 0x8927
SIOCGIFNETMASK = 0x891B
SIOCGIFBRDADDR = 0x8919
if LINUX:
    SECTOR_SIZE = 512
# 025098.python.test_linux.line61.comment =====================================================================
# 025099.python.test_linux.line62.comment --- utils
# 025100.python.test_linux.line63.comment =====================================================================


def get_ipv4_address(ifname):
    import fcntl

    ifname = bytes(ifname[:15], "ascii")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), SIOCGIFADDR, struct.pack('256s', ifname))[
                20:24
            ]
        )


def get_ipv4_netmask(ifname):
    import fcntl

    ifname = bytes(ifname[:15], "ascii")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(), SIOCGIFNETMASK, struct.pack('256s', ifname)
            )[20:24]
        )


def get_ipv4_broadcast(ifname):
    import fcntl

    ifname = bytes(ifname[:15], "ascii")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(), SIOCGIFBRDADDR, struct.pack('256s', ifname)
            )[20:24]
        )


def get_ipv6_addresses(ifname):
    with open("/proc/net/if_inet6") as f:
        all_fields = []
        for line in f:
            fields = line.split()
            if fields[-1] == ifname:
                all_fields.append(fields)

        if len(all_fields) == 0:
            raise ValueError(f"could not find interface {ifname!r}")

    for i in range(len(all_fields)):
        unformatted = all_fields[i][0]
        groups = [
            unformatted[j : j + 4] for j in range(0, len(unformatted), 4)
        ]
        formatted = ":".join(groups)
        packed = socket.inet_pton(socket.AF_INET6, formatted)
        all_fields[i] = socket.inet_ntop(socket.AF_INET6, packed)
    return all_fields


def get_mac_address(ifname):
    import fcntl

    ifname = bytes(ifname[:15], "ascii")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        info = fcntl.ioctl(
            s.fileno(), SIOCGIFHWADDR, struct.pack('256s', ifname)
        )
        return "".join([f"{char:02x}:" for char in info[18:24]])[:-1]


def free_swap():
    """Parse 'free' cmd and return swap memory's s total, used and free
    values.
    """
    out = sh(["free", "-b"], env={"LANG": "C.UTF-8"})
    lines = out.split('\n')
    for line in lines:
        if line.startswith('Swap'):
            _, total, used, free = line.split()
            nt = collections.namedtuple('free', 'total used free')
            return nt(int(total), int(used), int(free))
    raise ValueError(f"can't find 'Swap' in 'free' output:\n{out}")


def free_physmem():
    """Parse 'free' cmd and return physical memory's total, used
    and free values.
    """
    # 025101.python.test_linux.line153.comment Note: free can have 2 different formats, invalidating 'shared'
    # 025102.python.test_linux.line154.comment and 'cached' memory which may have different positions so we
    # 025103.python.test_linux.line155.comment do not return them.
    # 025104.python.test_linux.line156.comment https://github.com/giampaolo/psutil/issues/538#issuecomment-57059946
    out = sh(["free", "-b"], env={"LANG": "C.UTF-8"})
    lines = out.split('\n')
    for line in lines:
        if line.startswith('Mem'):
            total, used, free, shared = (int(x) for x in line.split()[1:5])
            nt = collections.namedtuple(
                'free', 'total used free shared output'
            )
            return nt(total, used, free, shared, out)
    raise ValueError(f"can't find 'Mem' in 'free' output:\n{out}")


def vmstat(stat):
    out = sh(["vmstat", "-s"], env={"LANG": "C.UTF-8"})
    for line in out.split("\n"):
        line = line.strip()
        if stat in line:
            return int(line.split(' ')[0])
    raise ValueError(f"can't find {stat!r} in 'vmstat' output")


def get_free_version_info():
    out = sh(["free", "-V"]).strip()
    if 'UNKNOWN' in out:
        raise pytest.skip("can't determine free version")
    return tuple(map(int, re.findall(r'\d+', out.split()[-1])))


@contextlib.contextmanager
def mock_open_content(pairs):
    """Mock open() builtin and forces it to return a certain content
    for a given path. `pairs` is a {"path": "content", ...} dict.
    """

    def open_mock(name, *args, **kwargs):
        if name in pairs:
            content = pairs[name]
            if isinstance(content, str):
                return io.StringIO(content)
            else:
                return io.BytesIO(content)
        else:
            return orig_open(name, *args, **kwargs)

    orig_open = open
    with mock.patch("builtins.open", create=True, side_effect=open_mock) as m:
        yield m


@contextlib.contextmanager
def mock_open_exception(for_path, exc):
    """Mock open() builtin and raises `exc` if the path being opened
    matches `for_path`.
    """

    def open_mock(name, *args, **kwargs):
        if name == for_path:
            raise exc
        return orig_open(name, *args, **kwargs)

    orig_open = open
    with mock.patch("builtins.open", create=True, side_effect=open_mock) as m:
        yield m


# 025105.python.test_linux.line222.comment =====================================================================
# 025106.python.test_linux.line223.comment --- system virtual memory
# 025107.python.test_linux.line224.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemVirtualMemoryAgainstFree(PsutilTestCase):
    def test_total(self):
        cli_value = free_physmem().total
        psutil_value = psutil.virtual_memory().total
        assert cli_value == psutil_value

    @retry_on_failure()
    def test_used(self):
        # 025108.python.test_linux.line236.comment Older versions of procps used slab memory to calculate used memory.
        # 025109.python.test_linux.line237.comment This got changed in:
        # 025110.python.test_linux.line238.comment https://gitlab.com/procps-ng/procps/commit/
        # 025111.python.test_linux.line239.comment 05d751c4f076a2f0118b914c5e51cfbb4762ad8e
        # 025112.python.test_linux.line240.comment Newer versions of procps are using yet another way to compute used
        # 025113.python.test_linux.line241.comment memory.
        # 025114.python.test_linux.line242.comment https://gitlab.com/procps-ng/procps/commit/
        # 025115.python.test_linux.line243.comment 2184e90d2e7cdb582f9a5b706b47015e56707e4d
        if get_free_version_info() < (4, 0, 0):
            raise pytest.skip("free version too old")
        cli_value = free_physmem().used
        psutil_value = psutil.virtual_memory().used
        assert abs(cli_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_free(self):
        cli_value = free_physmem().free
        psutil_value = psutil.virtual_memory().free
        assert abs(cli_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_shared(self):
        free = free_physmem()
        free_value = free.shared
        if free_value == 0:
            raise pytest.skip("free does not support 'shared' column")
        psutil_value = psutil.virtual_memory().shared
        assert (
            abs(free_value - psutil_value) < TOLERANCE_SYS_MEM
        ), f"{free_value} {psutil_value} \n{free.output}"

    @retry_on_failure()
    def test_available(self):
        # 025116.python.test_linux.line269.comment "free" output format has changed at some point:
        # 025117.python.test_linux.line270.comment https://github.com/giampaolo/psutil/issues/538#issuecomment-147192098
        out = sh(["free", "-b"])
        lines = out.split('\n')
        if 'available' not in lines[0]:
            raise pytest.skip("free does not support 'available' column")
        free_value = int(lines[1].split()[-1])
        psutil_value = psutil.virtual_memory().available
        assert abs(free_value - psutil_value) < TOLERANCE_SYS_MEM


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemVirtualMemoryAgainstVmstat(PsutilTestCase):
    def test_total(self):
        vmstat_value = vmstat('total memory') * 1024
        psutil_value = psutil.virtual_memory().total
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_used(self):
        # 025118.python.test_linux.line289.comment Older versions of procps used slab memory to calculate used memory.
        # 025119.python.test_linux.line290.comment This got changed in:
        # 025120.python.test_linux.line291.comment https://gitlab.com/procps-ng/procps/commit/
        # 025121.python.test_linux.line292.comment 05d751c4f076a2f0118b914c5e51cfbb4762ad8e
        # 025122.python.test_linux.line293.comment Newer versions of procps are using yet another way to compute used
        # 025123.python.test_linux.line294.comment memory.
        # 025124.python.test_linux.line295.comment https://gitlab.com/procps-ng/procps/commit/
        # 025125.python.test_linux.line296.comment 2184e90d2e7cdb582f9a5b706b47015e56707e4d
        if get_free_version_info() < (4, 0, 0):
            raise pytest.skip("free version too old")
        vmstat_value = vmstat('used memory') * 1024
        psutil_value = psutil.virtual_memory().used
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_free(self):
        vmstat_value = vmstat('free memory') * 1024
        psutil_value = psutil.virtual_memory().free
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_buffers(self):
        vmstat_value = vmstat('buffer memory') * 1024
        psutil_value = psutil.virtual_memory().buffers
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_active(self):
        vmstat_value = vmstat('active memory') * 1024
        psutil_value = psutil.virtual_memory().active
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_inactive(self):
        vmstat_value = vmstat('inactive memory') * 1024
        psutil_value = psutil.virtual_memory().inactive
        assert abs(vmstat_value - psutil_value) < TOLERANCE_SYS_MEM


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemVirtualMemoryMocks(PsutilTestCase):
    def test_warnings_on_misses(self):
        # 025126.python.test_linux.line331.comment Emulate a case where /proc/meminfo provides few info.
        # 025127.python.test_linux.line332.comment psutil is supposed to set the missing fields to 0 and
        # 025128.python.test_linux.line333.comment raise a warning.
        content = textwrap.dedent("""\
            Active(anon):    6145416 kB
            Active(file):    2950064 kB
            Inactive(anon):   574764 kB
            Inactive(file):  1567648 kB
            MemAvailable:         -1 kB
            MemFree:         2057400 kB
            MemTotal:       16325648 kB
            SReclaimable:     346648 kB
            """).encode()
        with mock_open_content({'/proc/meminfo': content}) as m:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                ret = psutil.virtual_memory()
                assert m.called
                assert len(ws) == 1
                w = ws[0]
                assert "memory stats couldn't be determined" in str(w.message)
                assert "cached" in str(w.message)
                assert "shared" in str(w.message)
                assert "active" in str(w.message)
                assert "inactive" in str(w.message)
                assert "buffers" in str(w.message)
                assert "available" in str(w.message)
                assert ret.cached == 0
                assert ret.active == 0
                assert ret.inactive == 0
                assert ret.shared == 0
                assert ret.buffers == 0
                assert ret.available == 0
                assert ret.slab == 0

    @retry_on_failure()
    def test_avail_old_percent(self):
        # 025129.python.test_linux.line368.comment Make sure that our calculation of avail mem for old kernels
        # 025130.python.test_linux.line369.comment is off by max 15%.
        mems = {}
        with open_binary('/proc/meminfo') as f:
            for line in f:
                fields = line.split()
                mems[fields[0]] = int(fields[1]) * 1024

        a = calculate_avail_vmem(mems)
        if b'MemAvailable:' in mems:
            b = mems[b'MemAvailable:']
            diff_percent = abs(a - b) / a * 100
            assert diff_percent < 15

    def test_avail_old_comes_from_kernel(self):
        # 025131.python.test_linux.line383.comment Make sure "MemAvailable:" coluimn is used instead of relying
        # 025132.python.test_linux.line384.comment on our internal algorithm to calculate avail mem.
        content = textwrap.dedent("""\
            Active:          9444728 kB
            Active(anon):    6145416 kB
            Active(file):    2950064 kB
            Buffers:          287952 kB
            Cached:          4818144 kB
            Inactive(file):  1578132 kB
            Inactive(anon):   574764 kB
            Inactive(file):  1567648 kB
            MemAvailable:    6574984 kB
            MemFree:         2057400 kB
            MemTotal:       16325648 kB
            Shmem:            577588 kB
            SReclaimable:     346648 kB
            """).encode()
        with mock_open_content({'/proc/meminfo': content}) as m:
            with warnings.catch_warnings(record=True) as ws:
                ret = psutil.virtual_memory()
            assert m.called
            assert ret.available == 6574984 * 1024
            w = ws[0]
            assert "inactive memory stats couldn't be determined" in str(
                w.message
            )

    def test_avail_old_missing_fields(self):
        # 025133.python.test_linux.line411.comment Remove Active(file), Inactive(file) and SReclaimable
        # 025134.python.test_linux.line412.comment from /proc/meminfo and make sure the fallback is used
        # 025135.python.test_linux.line413.comment (free + cached),
        content = textwrap.dedent("""\
            Active:          9444728 kB
            Active(anon):    6145416 kB
            Buffers:          287952 kB
            Cached:          4818144 kB
            Inactive(file):  1578132 kB
            Inactive(anon):   574764 kB
            MemFree:         2057400 kB
            MemTotal:       16325648 kB
            Shmem:            577588 kB
            """).encode()
        with mock_open_content({"/proc/meminfo": content}) as m:
            with warnings.catch_warnings(record=True) as ws:
                ret = psutil.virtual_memory()
            assert m.called
            assert ret.available == 2057400 * 1024 + 4818144 * 1024
            w = ws[0]
            assert "inactive memory stats couldn't be determined" in str(
                w.message
            )

    def test_avail_old_missing_zoneinfo(self):
        # 025136.python.test_linux.line436.comment Remove /proc/zoneinfo file. Make sure fallback is used
        # 025137.python.test_linux.line437.comment (free + cached).
        content = textwrap.dedent("""\
            Active:          9444728 kB
            Active(anon):    6145416 kB
            Active(file):    2950064 kB
            Buffers:          287952 kB
            Cached:          4818144 kB
            Inactive(file):  1578132 kB
            Inactive(anon):   574764 kB
            Inactive(file):  1567648 kB
            MemFree:         2057400 kB
            MemTotal:       16325648 kB
            Shmem:            577588 kB
            SReclaimable:     346648 kB
            """).encode()
        with mock_open_content({"/proc/meminfo": content}):
            with mock_open_exception("/proc/zoneinfo", FileNotFoundError):
                with warnings.catch_warnings(record=True) as ws:
                    ret = psutil.virtual_memory()
                    assert ret.available == 2057400 * 1024 + 4818144 * 1024
                    w = ws[0]
                    assert (
                        "inactive memory stats couldn't be determined"
                        in str(w.message)
                    )

    def test_virtual_memory_mocked(self):
        # 025138.python.test_linux.line464.comment Emulate /proc/meminfo because neither vmstat nor free return slab.
        content = textwrap.dedent("""\
            MemTotal:              100 kB
            MemFree:               2 kB
            MemAvailable:          3 kB
            Buffers:               4 kB
            Cached:                5 kB
            SwapCached:            6 kB
            Active:                7 kB
            Inactive:              8 kB
            Active(anon):          9 kB
            Inactive(anon):        10 kB
            Active(file):          11 kB
            Inactive(file):        12 kB
            Unevictable:           13 kB
            Mlocked:               14 kB
            SwapTotal:             15 kB
            SwapFree:              16 kB
            Dirty:                 17 kB
            Writeback:             18 kB
            AnonPages:             19 kB
            Mapped:                20 kB
            Shmem:                 21 kB
            Slab:                  22 kB
            SReclaimable:          23 kB
            SUnreclaim:            24 kB
            KernelStack:           25 kB
            PageTables:            26 kB
            NFS_Unstable:          27 kB
            Bounce:                28 kB
            WritebackTmp:          29 kB
            CommitLimit:           30 kB
            Committed_AS:          31 kB
            VmallocTotal:          32 kB
            VmallocUsed:           33 kB
            VmallocChunk:          34 kB
            HardwareCorrupted:     35 kB
            AnonHugePages:         36 kB
            ShmemHugePages:        37 kB
            ShmemPmdMapped:        38 kB
            CmaTotal:              39 kB
            CmaFree:               40 kB
            HugePages_Total:       41 kB
            HugePages_Free:        42 kB
            HugePages_Rsvd:        43 kB
            HugePages_Surp:        44 kB
            Hugepagesize:          45 kB
            DirectMap46k:          46 kB
            DirectMap47M:          47 kB
            DirectMap48G:          48 kB
            """).encode()
        with mock_open_content({"/proc/meminfo": content}) as m:
            mem = psutil.virtual_memory()
            assert m.called
            assert mem.total == 100 * 1024
            assert mem.free == 2 * 1024
            assert mem.buffers == 4 * 1024
            # 025139.python.test_linux.line521.comment cached mem also includes reclaimable memory
            assert mem.cached == (5 + 23) * 1024
            assert mem.shared == 21 * 1024
            assert mem.active == 7 * 1024
            assert mem.inactive == 8 * 1024
            assert mem.slab == 22 * 1024
            assert mem.available == 3 * 1024


# 025140.python.test_linux.line530.comment =====================================================================
# 025141.python.test_linux.line531.comment --- system swap memory
# 025142.python.test_linux.line532.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemSwapMemory(PsutilTestCase):
    @staticmethod
    def meminfo_has_swap_info():
        """Return True if /proc/meminfo provides swap metrics."""
        with open("/proc/meminfo") as f:
            data = f.read()
        return 'SwapTotal:' in data and 'SwapFree:' in data

    def test_total(self):
        free_value = free_swap().total
        psutil_value = psutil.swap_memory().total
        assert abs(free_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_used(self):
        free_value = free_swap().used
        psutil_value = psutil.swap_memory().used
        assert abs(free_value - psutil_value) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_free(self):
        free_value = free_swap().free
        psutil_value = psutil.swap_memory().free
        assert abs(free_value - psutil_value) < TOLERANCE_SYS_MEM

    def test_missing_sin_sout(self):
        with mock.patch('psutil._common.open', create=True) as m:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                ret = psutil.swap_memory()
                assert m.called
                assert len(ws) == 1
                w = ws[0]
                assert (
                    "'sin' and 'sout' swap memory stats couldn't be determined"
                    in str(w.message)
                )
                assert ret.sin == 0
                assert ret.sout == 0

    def test_no_vmstat_mocked(self):
        # 025143.python.test_linux.line577.comment see https://github.com/giampaolo/psutil/issues/722
        with mock_open_exception("/proc/vmstat", FileNotFoundError) as m:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                ret = psutil.swap_memory()
                assert m.called
                assert len(ws) == 1
                w = ws[0]
                assert (
                    "'sin' and 'sout' swap memory stats couldn't "
                    "be determined and were set to 0"
                    in str(w.message)
                )
                assert ret.sin == 0
                assert ret.sout == 0

    def test_meminfo_against_sysinfo(self):
        # 025144.python.test_linux.line594.comment Make sure the content of /proc/meminfo about swap memory
        # 025145.python.test_linux.line595.comment matches sysinfo() syscall, see:
        # 025146.python.test_linux.line596.comment https://github.com/giampaolo/psutil/issues/1015
        if not self.meminfo_has_swap_info():
            raise pytest.skip("/proc/meminfo has no swap metrics")
        with mock.patch('psutil._pslinux.cext.linux_sysinfo') as m:
            swap = psutil.swap_memory()
        assert not m.called
        import psutil._psutil_linux as cext

        _, _, _, _, total, free, unit_multiplier = cext.linux_sysinfo()
        total *= unit_multiplier
        free *= unit_multiplier
        assert swap.total == total
        assert abs(swap.free - free) < TOLERANCE_SYS_MEM

    def test_emulate_meminfo_has_no_metrics(self):
        # 025147.python.test_linux.line611.comment Emulate a case where /proc/meminfo provides no swap metrics
        # 025148.python.test_linux.line612.comment in which case sysinfo() syscall is supposed to be used
        # 025149.python.test_linux.line613.comment as a fallback.
        with mock_open_content({"/proc/meminfo": b""}) as m:
            psutil.swap_memory()
            assert m.called


# 025150.python.test_linux.line619.comment =====================================================================
# 025151.python.test_linux.line620.comment --- system CPU
# 025152.python.test_linux.line621.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemCPUTimes(PsutilTestCase):
    def test_fields(self):
        fields = psutil.cpu_times()._fields
        kernel_ver = re.findall(r'\d+\.\d+\.\d+', os.uname()[2])[0]
        kernel_ver_info = tuple(map(int, kernel_ver.split('.')))
        if kernel_ver_info >= (2, 6, 11):
            assert 'steal' in fields
        else:
            assert 'steal' not in fields
        if kernel_ver_info >= (2, 6, 24):
            assert 'guest' in fields
        else:
            assert 'guest' not in fields
        if kernel_ver_info >= (3, 2, 0):
            assert 'guest_nice' in fields
        else:
            assert 'guest_nice' not in fields


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemCPUCountLogical(PsutilTestCase):
    @pytest.mark.skipif(
        not os.path.exists("/sys/devices/system/cpu/online"),
        reason="/sys/devices/system/cpu/online does not exist",
    )
    def test_against_sysdev_cpu_online(self):
        with open("/sys/devices/system/cpu/online") as f:
            value = f.read().strip()
        if "-" in str(value):
            value = int(value.split('-')[1]) + 1
            assert psutil.cpu_count() == value

    @pytest.mark.skipif(
        not os.path.exists("/sys/devices/system/cpu"),
        reason="/sys/devices/system/cpu does not exist",
    )
    def test_against_sysdev_cpu_num(self):
        ls = os.listdir("/sys/devices/system/cpu")
        count = len([x for x in ls if re.search(r"cpu\d+$", x) is not None])
        assert psutil.cpu_count() == count

    @pytest.mark.skipif(
        not shutil.which("nproc"), reason="nproc utility not available"
    )
    def test_against_nproc(self):
        num = int(sh("nproc --all"))
        assert psutil.cpu_count(logical=True) == num

    @pytest.mark.skipif(
        not shutil.which("lscpu"), reason="lscpu utility not available"
    )
    def test_against_lscpu(self):
        out = sh("lscpu -p")
        num = len([x for x in out.split('\n') if not x.startswith('#')])
        assert psutil.cpu_count(logical=True) == num

    def test_emulate_fallbacks(self):
        import psutil._pslinux

        original = psutil._pslinux.cpu_count_logical()
        # 025153.python.test_linux.line685.comment Here we want to mock os.sysconf("SC_NPROCESSORS_ONLN") in
        # 025154.python.test_linux.line686.comment order to cause the parsing of /proc/cpuinfo and /proc/stat.
        with mock.patch(
            'psutil._pslinux.os.sysconf', side_effect=ValueError
        ) as m:
            assert psutil._pslinux.cpu_count_logical() == original
            assert m.called

            # 025155.python.test_linux.line693.comment Let's have open() return empty data and make sure None is
            # 025156.python.test_linux.line694.comment returned ('cause we mimic os.cpu_count()).
            with mock.patch('psutil._common.open', create=True) as m:
                assert psutil._pslinux.cpu_count_logical() is None
                assert m.call_count == 2
                # 025157.python.test_linux.line698.comment /proc/stat should be the last one
                assert m.call_args[0][0] == '/proc/stat'

            # 025158.python.test_linux.line701.comment Let's push this a bit further and make sure /proc/cpuinfo
            # 025159.python.test_linux.line702.comment parsing works as expected.
            with open('/proc/cpuinfo', 'rb') as f:
                cpuinfo_data = f.read()
            fake_file = io.BytesIO(cpuinfo_data)
            with mock.patch(
                'psutil._common.open', return_value=fake_file, create=True
            ) as m:
                assert psutil._pslinux.cpu_count_logical() == original

            # 025160.python.test_linux.line711.comment Finally, let's make /proc/cpuinfo return meaningless data;
            # 025161.python.test_linux.line712.comment this way we'll fall back on relying on /proc/stat
            with mock_open_content({"/proc/cpuinfo": b""}) as m:
                assert psutil._pslinux.cpu_count_logical() == original
                assert m.called


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemCPUCountCores(PsutilTestCase):
    @pytest.mark.skipif(
        not shutil.which("lscpu"), reason="lscpu utility not available"
    )
    def test_against_lscpu(self):
        out = sh("lscpu -p")
        core_ids = set()
        for line in out.split('\n'):
            if not line.startswith('#'):
                fields = line.split(',')
                core_ids.add(fields[1])
        assert psutil.cpu_count(logical=False) == len(core_ids)

    @pytest.mark.skipif(
        platform.machine() not in {"x86_64", "i686"}, reason="x86_64/i686 only"
    )
    def test_method_2(self):
        meth_1 = psutil._pslinux.cpu_count_cores()
        with mock.patch('glob.glob', return_value=[]) as m:
            meth_2 = psutil._pslinux.cpu_count_cores()
            assert m.called
        if meth_1 is not None:
            assert meth_1 == meth_2

    def test_emulate_none(self):
        with mock.patch('glob.glob', return_value=[]) as m1:
            with mock.patch('psutil._common.open', create=True) as m2:
                assert psutil._pslinux.cpu_count_cores() is None
        assert m1.called
        assert m2.called


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemCPUFrequency(PsutilTestCase):
    @pytest.mark.skipif(not HAS_CPU_FREQ, reason="not supported")
    @pytest.mark.skipif(
        AARCH64, reason="aarch64 does not always expose frequency"
    )
    def test_emulate_use_second_file(self):
        # 025162.python.test_linux.line758.comment https://github.com/giampaolo/psutil/issues/981
        def path_exists_mock(path):
            if path.startswith("/sys/devices/system/cpu/cpufreq/policy"):
                return False
            else:
                return orig_exists(path)

        orig_exists = os.path.exists
        with mock.patch(
            "os.path.exists", side_effect=path_exists_mock, create=True
        ):
            assert psutil.cpu_freq()

    @pytest.mark.skipif(not HAS_CPU_FREQ, reason="not supported")
    @pytest.mark.skipif(
        AARCH64 or RISCV64,
        reason=f"{platform.machine()} does not report mhz in /proc/cpuinfo",
    )
    def test_emulate_use_cpuinfo(self):
        # 025163.python.test_linux.line777.comment Emulate a case where /sys/devices/system/cpu/cpufreq* does not
        # 025164.python.test_linux.line778.comment exist and /proc/cpuinfo is used instead.
        def path_exists_mock(path):
            if path.startswith('/sys/devices/system/cpu/'):
                return False
            else:
                return os_path_exists(path)

        os_path_exists = os.path.exists
        try:
            with mock.patch("os.path.exists", side_effect=path_exists_mock):
                reload_module(psutil._pslinux)
                ret = psutil.cpu_freq()
                assert ret, ret
                assert ret.max == 0.0
                assert ret.min == 0.0
                for freq in psutil.cpu_freq(percpu=True):
                    assert freq.max == 0.0
                    assert freq.min == 0.0
        finally:
            reload_module(psutil._pslinux)
            reload_module(psutil)

    @pytest.mark.skipif(not HAS_CPU_FREQ, reason="not supported")
    def test_emulate_data(self):
        def open_mock(name, *args, **kwargs):
            if name.endswith('/scaling_cur_freq') and name.startswith(
                "/sys/devices/system/cpu/cpufreq/policy"
            ):
                return io.BytesIO(b"500000")
            elif name.endswith('/scaling_min_freq') and name.startswith(
                "/sys/devices/system/cpu/cpufreq/policy"
            ):
                return io.BytesIO(b"600000")
            elif name.endswith('/scaling_max_freq') and name.startswith(
                "/sys/devices/system/cpu/cpufreq/policy"
            ):
                return io.BytesIO(b"700000")
            elif name == '/proc/cpuinfo':
                return io.BytesIO(b"cpu MHz     : 500")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            with mock.patch('os.path.exists', return_value=True):
                freq = psutil.cpu_freq()
                assert freq.current == 500.0
                # 025165.python.test_linux.line825.comment when /proc/cpuinfo is used min and max frequencies are not
                # 025166.python.test_linux.line826.comment available and are set to 0.
                if freq.min != 0.0:
                    assert freq.min == 600.0
                if freq.max != 0.0:
                    assert freq.max == 700.0

    @pytest.mark.skipif(not HAS_CPU_FREQ, reason="not supported")
    def test_emulate_multi_cpu(self):
        def open_mock(name, *args, **kwargs):
            n = name
            if n.endswith('/scaling_cur_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy0"
            ):
                return io.BytesIO(b"100000")
            elif n.endswith('/scaling_min_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy0"
            ):
                return io.BytesIO(b"200000")
            elif n.endswith('/scaling_max_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy0"
            ):
                return io.BytesIO(b"300000")
            elif n.endswith('/scaling_cur_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy1"
            ):
                return io.BytesIO(b"400000")
            elif n.endswith('/scaling_min_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy1"
            ):
                return io.BytesIO(b"500000")
            elif n.endswith('/scaling_max_freq') and n.startswith(
                "/sys/devices/system/cpu/cpufreq/policy1"
            ):
                return io.BytesIO(b"600000")
            elif name == '/proc/cpuinfo':
                return io.BytesIO(b"cpu MHz     : 100\ncpu MHz     : 400")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch(
                    'psutil._pslinux.cpu_count_logical', return_value=2
                ):
                    freq = psutil.cpu_freq(percpu=True)
                    assert freq[0].current == 100.0
                    if freq[0].min != 0.0:
                        assert freq[0].min == 200.0
                    if freq[0].max != 0.0:
                        assert freq[0].max == 300.0
                    assert freq[1].current == 400.0
                    if freq[1].min != 0.0:
                        assert freq[1].min == 500.0
                    if freq[1].max != 0.0:
                        assert freq[1].max == 600.0

    @pytest.mark.skipif(not HAS_CPU_FREQ, reason="not supported")
    def test_emulate_no_scaling_cur_freq_file(self):
        # 025167.python.test_linux.line885.comment See: https://github.com/giampaolo/psutil/issues/1071
        def open_mock(name, *args, **kwargs):
            if name.endswith('/scaling_cur_freq'):
                raise FileNotFoundError
            if name.endswith('/cpuinfo_cur_freq'):
                return io.BytesIO(b"200000")
            elif name == '/proc/cpuinfo':
                return io.BytesIO(b"cpu MHz     : 200")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch(
                    'psutil._pslinux.cpu_count_logical', return_value=1
                ):
                    freq = psutil.cpu_freq()
                    assert freq.current == 200


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemCPUStats(PsutilTestCase):

    # 025168.python.test_linux.line909.comment XXX: fails too often.
    # 025169.python.test_linux.line910.comment def test_ctx_switches(self):
    # 025170.python.test_linux.line911.comment vmstat_value = vmstat("context switches")
    # 025171.python.test_linux.line912.comment psutil_value = psutil.cpu_stats().ctx_switches
    # 025172.python.test_linux.line913.comment assert abs(vmstat_value - psutil_value) < 500

    def test_interrupts(self):
        vmstat_value = vmstat("interrupts")
        psutil_value = psutil.cpu_stats().interrupts
        assert abs(vmstat_value - psutil_value) < 500


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestLoadAvg(PsutilTestCase):
    @pytest.mark.skipif(not HAS_GETLOADAVG, reason="not supported")
    def test_getloadavg(self):
        psutil_value = psutil.getloadavg()
        with open("/proc/loadavg") as f:
            proc_value = f.read().split()

        assert abs(float(proc_value[0]) - psutil_value[0]) < 1
        assert abs(float(proc_value[1]) - psutil_value[1]) < 1
        assert abs(float(proc_value[2]) - psutil_value[2]) < 1


# 025173.python.test_linux.line934.comment =====================================================================
# 025174.python.test_linux.line935.comment --- system network
# 025175.python.test_linux.line936.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemNetIfAddrs(PsutilTestCase):
    def test_ips(self):
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    assert addr.address == get_mac_address(name)
                elif addr.family == socket.AF_INET:
                    assert addr.address == get_ipv4_address(name)
                    assert addr.netmask == get_ipv4_netmask(name)
                    if addr.broadcast is not None:
                        assert addr.broadcast == get_ipv4_broadcast(name)
                    else:
                        assert get_ipv4_broadcast(name) == '0.0.0.0'
                elif addr.family == socket.AF_INET6:
                    # 025176.python.test_linux.line954.comment IPv6 addresses can have a percent symbol at the end.
                    # 025177.python.test_linux.line955.comment E.g. these 2 are equivalent:
                    # 025178.python.test_linux.line956.comment "fe80::1ff:fe23:4567:890a"
                    # 025179.python.test_linux.line957.comment "fe80::1ff:fe23:4567:890a%eth0"
                    # 025180.python.test_linux.line958.comment That is the "zone id" portion, which usually is the name
                    # 025181.python.test_linux.line959.comment of the network interface.
                    address = addr.address.split('%')[0]
                    assert address in get_ipv6_addresses(name)

    # 025182.python.test_linux.line963.comment XXX - not reliable when having virtual NICs installed by Docker.
    # 025183.python.test_linux.line964.comment @pytest.mark.skipif(not shutil.which("ip"),
    # 025184.python.test_linux.line965.comment reason="'ip' utility not available")
    # 025185.python.test_linux.line966.comment def test_net_if_names(self):
    # 025186.python.test_linux.line967.comment out = sh("ip addr").strip()
    # 025187.python.test_linux.line968.comment nics = [x for x in psutil.net_if_addrs().keys() if ':' not in x]
    # 025188.python.test_linux.line969.comment found = 0
    # 025189.python.test_linux.line970.comment for line in out.split('\n'):
    # 025190.python.test_linux.line971.comment line = line.strip()
    # 025191.python.test_linux.line972.comment if re.search(r"^\d+:", line):
    # 025192.python.test_linux.line973.comment found += 1
    # 025193.python.test_linux.line974.comment name = line.split(':')[1].strip()
    # 025194.python.test_linux.line975.comment assert name in nics
    # 025195.python.test_linux.line976.comment assert len(nics) == found


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemNetIfStats(PsutilTestCase):
    @pytest.mark.skipif(
        not shutil.which("ifconfig"), reason="ifconfig utility not available"
    )
    def test_against_ifconfig(self):
        for name, stats in psutil.net_if_stats().items():
            try:
                out = sh(f"ifconfig {name}")
            except RuntimeError:
                pass
            else:
                assert stats.isup == ('RUNNING' in out), out
                assert stats.mtu == int(
                    re.findall(r'(?i)MTU[: ](\d+)', out)[0]
                )

    def test_mtu(self):
        for name, stats in psutil.net_if_stats().items():
            with open(f"/sys/class/net/{name}/mtu") as f:
                assert stats.mtu == int(f.read().strip())

    @pytest.mark.skipif(
        not shutil.which("ifconfig"), reason="ifconfig utility not available"
    )
    def test_flags(self):
        # 025196.python.test_linux.line1005.comment first line looks like this:
        # 025197.python.test_linux.line1006.comment "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500"
        matches_found = 0
        for name, stats in psutil.net_if_stats().items():
            try:
                out = sh(f"ifconfig {name}")
            except RuntimeError:
                pass
            else:
                match = re.search(r"flags=(\d+)?<(.*?)>", out)
                if match and len(match.groups()) >= 2:
                    matches_found += 1
                    ifconfig_flags = set(match.group(2).lower().split(","))
                    psutil_flags = set(stats.flags.split(","))
                    assert ifconfig_flags == psutil_flags
                else:
                    # 025198.python.test_linux.line1021.comment ifconfig has a different output on CentOS 6
                    # 025199.python.test_linux.line1022.comment let's try that
                    match = re.search(r"(.*)  MTU:(\d+)  Metric:(\d+)", out)
                    if match and len(match.groups()) >= 3:
                        matches_found += 1
                        ifconfig_flags = set(match.group(1).lower().split())
                        psutil_flags = set(stats.flags.split(","))
                        assert ifconfig_flags == psutil_flags

        if not matches_found:
            raise pytest.fail("no matches were found")


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemNetIOCounters(PsutilTestCase):
    @pytest.mark.skipif(
        not shutil.which("ifconfig"), reason="ifconfig utility not available"
    )
    @retry_on_failure()
    def test_against_ifconfig(self):
        def ifconfig(nic):
            ret = {}
            out = sh(f"ifconfig {nic}")
            ret['packets_recv'] = int(
                re.findall(r'RX packets[: ](\d+)', out)[0]
            )
            ret['packets_sent'] = int(
                re.findall(r'TX packets[: ](\d+)', out)[0]
            )
            ret['errin'] = int(re.findall(r'errors[: ](\d+)', out)[0])
            ret['errout'] = int(re.findall(r'errors[: ](\d+)', out)[1])
            ret['dropin'] = int(re.findall(r'dropped[: ](\d+)', out)[0])
            ret['dropout'] = int(re.findall(r'dropped[: ](\d+)', out)[1])
            ret['bytes_recv'] = int(
                re.findall(r'RX (?:packets \d+ +)?bytes[: ](\d+)', out)[0]
            )
            ret['bytes_sent'] = int(
                re.findall(r'TX (?:packets \d+ +)?bytes[: ](\d+)', out)[0]
            )
            return ret

        nio = psutil.net_io_counters(pernic=True, nowrap=False)
        for name, stats in nio.items():
            try:
                ifconfig_ret = ifconfig(name)
            except RuntimeError:
                continue
            assert (
                abs(stats.bytes_recv - ifconfig_ret['bytes_recv']) < 1024 * 10
            )
            assert (
                abs(stats.bytes_sent - ifconfig_ret['bytes_sent']) < 1024 * 10
            )
            assert (
                abs(stats.packets_recv - ifconfig_ret['packets_recv']) < 1024
            )
            assert (
                abs(stats.packets_sent - ifconfig_ret['packets_sent']) < 1024
            )
            assert abs(stats.errin - ifconfig_ret['errin']) < 10
            assert abs(stats.errout - ifconfig_ret['errout']) < 10
            assert abs(stats.dropin - ifconfig_ret['dropin']) < 10
            assert abs(stats.dropout - ifconfig_ret['dropout']) < 10


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemNetConnections(PsutilTestCase):
    @mock.patch('psutil._pslinux.socket.inet_ntop', side_effect=ValueError)
    @mock.patch('psutil._pslinux.supports_ipv6', return_value=False)
    def test_emulate_ipv6_unsupported(self, supports_ipv6, inet_ntop):
        # 025200.python.test_linux.line1091.comment see: https://github.com/giampaolo/psutil/issues/623
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            try:
                s.bind(("::1", 0))
            except OSError:
                pass
            psutil.net_connections(kind='inet6')

    def test_emulate_unix(self):
        content = textwrap.dedent("""\
            0: 00000003 000 000 0001 03 462170 @/tmp/dbus-Qw2hMPIU3n
            0: 00000003 000 000 0001 03 35010 @/tmp/dbus-tB2X8h69BQ
            0: 00000003 000 000 0001 03 34424 @/tmp/dbus-cHy80Y8O
            000000000000000000000000000000000000000000000000000000
            """)
        with mock_open_content({"/proc/net/unix": content}) as m:
            psutil.net_connections(kind='unix')
            assert m.called


# 025201.python.test_linux.line1111.comment =====================================================================
# 025202.python.test_linux.line1112.comment --- system disks
# 025203.python.test_linux.line1113.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemDiskPartitions(PsutilTestCase):
    @pytest.mark.skipif(
        not hasattr(os, 'statvfs'), reason="os.statvfs() not available"
    )
    @skip_on_not_implemented()
    def test_against_df(self):
        # 025204.python.test_linux.line1123.comment test psutil.disk_usage() and psutil.disk_partitions()
        # 025205.python.test_linux.line1124.comment against "df -a"
        def df(path):
            out = sh(f'df -P -B 1 "{path}"').strip()
            lines = out.split('\n')
            lines.pop(0)
            line = lines.pop(0)
            dev, total, used, free = line.split()[:4]
            if dev == 'none':
                dev = ''
            total, used, free = int(total), int(used), int(free)
            return dev, total, used, free

        for part in psutil.disk_partitions(all=False):
            usage = psutil.disk_usage(part.mountpoint)
            _, total, used, free = df(part.mountpoint)
            assert usage.total == total
            assert abs(usage.free - free) < TOLERANCE_DISK_USAGE
            assert abs(usage.used - used) < TOLERANCE_DISK_USAGE

    def test_zfs_fs(self):
        # 025206.python.test_linux.line1144.comment Test that ZFS partitions are returned.
        with open("/proc/filesystems") as f:
            data = f.read()
        if 'zfs' in data:
            for part in psutil.disk_partitions():
                if part.fstype == 'zfs':
                    return

        # 025207.python.test_linux.line1152.comment No ZFS partitions on this system. Let's fake one.
        fake_file = io.StringIO("nodev\tzfs\n")
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m1:
            with mock.patch(
                'psutil._pslinux.cext.disk_partitions',
                return_value=[('/dev/sdb3', '/', 'zfs', 'rw')],
            ) as m2:
                ret = psutil.disk_partitions()
                assert m1.called
                assert m2.called
                assert ret
                assert ret[0].fstype == 'zfs'

    def test_emulate_realpath_fail(self):
        # 025208.python.test_linux.line1168.comment See: https://github.com/giampaolo/psutil/issues/1307
        try:
            with mock.patch(
                'os.path.realpath', return_value='/non/existent'
            ) as m:
                with pytest.raises(FileNotFoundError):
                    psutil.disk_partitions()
                assert m.called
        finally:
            psutil.PROCFS_PATH = "/proc"


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSystemDiskIoCounters(PsutilTestCase):
    def test_emulate_kernel_2_4(self):
        # 025209.python.test_linux.line1183.comment Tests /proc/diskstats parsing format for 2.4 kernels, see:
        # 025210.python.test_linux.line1184.comment https://github.com/giampaolo/psutil/issues/767
        content = "   3     0   1 hda 2 3 4 5 6 7 8 9 10 11 12"
        with mock_open_content({'/proc/diskstats': content}):
            with mock.patch(
                'psutil._pslinux.is_storage_device', return_value=True
            ):
                ret = psutil.disk_io_counters(nowrap=False)
                assert ret.read_count == 1
                assert ret.read_merged_count == 2
                assert ret.read_bytes == 3 * SECTOR_SIZE
                assert ret.read_time == 4
                assert ret.write_count == 5
                assert ret.write_merged_count == 6
                assert ret.write_bytes == 7 * SECTOR_SIZE
                assert ret.write_time == 8
                assert ret.busy_time == 10

    def test_emulate_kernel_2_6_full(self):
        # 025211.python.test_linux.line1202.comment Tests /proc/diskstats parsing format for 2.6 kernels,
        # 025212.python.test_linux.line1203.comment lines reporting all metrics:
        # 025213.python.test_linux.line1204.comment https://github.com/giampaolo/psutil/issues/767
        content = "   3    0   hda 1 2 3 4 5 6 7 8 9 10 11"
        with mock_open_content({"/proc/diskstats": content}):
            with mock.patch(
                'psutil._pslinux.is_storage_device', return_value=True
            ):
                ret = psutil.disk_io_counters(nowrap=False)
                assert ret.read_count == 1
                assert ret.read_merged_count == 2
                assert ret.read_bytes == 3 * SECTOR_SIZE
                assert ret.read_time == 4
                assert ret.write_count == 5
                assert ret.write_merged_count == 6
                assert ret.write_bytes == 7 * SECTOR_SIZE
                assert ret.write_time == 8
                assert ret.busy_time == 10

    def test_emulate_kernel_2_6_limited(self):
        # 025214.python.test_linux.line1222.comment Tests /proc/diskstats parsing format for 2.6 kernels,
        # 025215.python.test_linux.line1223.comment where one line of /proc/partitions return a limited
        # 025216.python.test_linux.line1224.comment amount of metrics when it bumps into a partition
        # 025217.python.test_linux.line1225.comment (instead of a disk). See:
        # 025218.python.test_linux.line1226.comment https://github.com/giampaolo/psutil/issues/767
        with mock_open_content({"/proc/diskstats": "   3    1   hda 1 2 3 4"}):
            with mock.patch(
                'psutil._pslinux.is_storage_device', return_value=True
            ):
                ret = psutil.disk_io_counters(nowrap=False)
                assert ret.read_count == 1
                assert ret.read_bytes == 2 * SECTOR_SIZE
                assert ret.write_count == 3
                assert ret.write_bytes == 4 * SECTOR_SIZE

                assert ret.read_merged_count == 0
                assert ret.read_time == 0
                assert ret.write_merged_count == 0
                assert ret.write_time == 0
                assert ret.busy_time == 0

    def test_emulate_include_partitions(self):
        # 025219.python.test_linux.line1244.comment Make sure that when perdisk=True disk partitions are returned,
        # 025220.python.test_linux.line1245.comment see:
        # 025221.python.test_linux.line1246.comment https://github.com/giampaolo/psutil/pull/1313#issuecomment-408626842
        content = textwrap.dedent("""\
            3    0   nvme0n1 1 2 3 4 5 6 7 8 9 10 11
            3    0   nvme0n1p1 1 2 3 4 5 6 7 8 9 10 11
            """)
        with mock_open_content({"/proc/diskstats": content}):
            with mock.patch(
                'psutil._pslinux.is_storage_device', return_value=False
            ):
                ret = psutil.disk_io_counters(perdisk=True, nowrap=False)
                assert len(ret) == 2
                assert ret['nvme0n1'].read_count == 1
                assert ret['nvme0n1p1'].read_count == 1
                assert ret['nvme0n1'].write_count == 5
                assert ret['nvme0n1p1'].write_count == 5

    def test_emulate_exclude_partitions(self):
        # 025222.python.test_linux.line1263.comment Make sure that when perdisk=False partitions (e.g. 'sda1',
        # 025223.python.test_linux.line1264.comment 'nvme0n1p1') are skipped and not included in the total count.
        # 025224.python.test_linux.line1265.comment https://github.com/giampaolo/psutil/pull/1313#issuecomment-408626842
        content = textwrap.dedent("""\
            3    0   nvme0n1 1 2 3 4 5 6 7 8 9 10 11
            3    0   nvme0n1p1 1 2 3 4 5 6 7 8 9 10 11
            """)
        with mock_open_content({"/proc/diskstats": content}):
            with mock.patch(
                'psutil._pslinux.is_storage_device', return_value=False
            ):
                ret = psutil.disk_io_counters(perdisk=False, nowrap=False)
                assert ret is None

        def is_storage_device(name):
            return name == 'nvme0n1'

        content = textwrap.dedent("""\
            3    0   nvme0n1 1 2 3 4 5 6 7 8 9 10 11
            3    0   nvme0n1p1 1 2 3 4 5 6 7 8 9 10 11
            """)
        with mock_open_content({"/proc/diskstats": content}):
            with mock.patch(
                'psutil._pslinux.is_storage_device',
                create=True,
                side_effect=is_storage_device,
            ):
                ret = psutil.disk_io_counters(perdisk=False, nowrap=False)
                assert ret.read_count == 1
                assert ret.write_count == 5

    def test_emulate_use_sysfs(self):
        def exists(path):
            return path == '/proc/diskstats'

        wprocfs = psutil.disk_io_counters(perdisk=True)
        with mock.patch(
            'psutil._pslinux.os.path.exists', create=True, side_effect=exists
        ):
            wsysfs = psutil.disk_io_counters(perdisk=True)
        assert len(wprocfs) == len(wsysfs)

    def test_emulate_not_impl(self):
        def exists(path):
            return False

        with mock.patch(
            'psutil._pslinux.os.path.exists', create=True, side_effect=exists
        ):
            with pytest.raises(NotImplementedError):
                psutil.disk_io_counters()


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestRootFsDeviceFinder(PsutilTestCase):
    def setUp(self):
        dev = os.stat("/").st_dev
        self.major = os.major(dev)
        self.minor = os.minor(dev)

    def test_call_methods(self):
        finder = RootFsDeviceFinder()
        if os.path.exists("/proc/partitions"):
            finder.ask_proc_partitions()
        else:
            with pytest.raises(FileNotFoundError):
                finder.ask_proc_partitions()
        if os.path.exists(f"/sys/dev/block/{self.major}:{self.minor}/uevent"):
            finder.ask_sys_dev_block()
        else:
            with pytest.raises(FileNotFoundError):
                finder.ask_sys_dev_block()
        finder.ask_sys_class_block()

    @pytest.mark.skipif(GITHUB_ACTIONS, reason="unsupported on GITHUB_ACTIONS")
    def test_comparisons(self):
        finder = RootFsDeviceFinder()
        assert finder.find() is not None

        a = b = c = None
        if os.path.exists("/proc/partitions"):
            a = finder.ask_proc_partitions()
        if os.path.exists(f"/sys/dev/block/{self.major}:{self.minor}/uevent"):
            b = finder.ask_sys_class_block()
        c = finder.ask_sys_dev_block()

        base = a or b or c
        if base and a:
            assert base == a
        if base and b:
            assert base == b
        if base and c:
            assert base == c

    @pytest.mark.skipif(
        not shutil.which("findmnt"), reason="findmnt utility not available"
    )
    @pytest.mark.skipif(GITHUB_ACTIONS, reason="unsupported on GITHUB_ACTIONS")
    def test_against_findmnt(self):
        psutil_value = RootFsDeviceFinder().find()
        findmnt_value = sh("findmnt -o SOURCE -rn /")
        assert psutil_value == findmnt_value

    def test_disk_partitions_mocked(self):
        with mock.patch(
            'psutil._pslinux.cext.disk_partitions',
            return_value=[('/dev/root', '/', 'ext4', 'rw')],
        ) as m:
            part = psutil.disk_partitions()[0]
            assert m.called
            if not GITHUB_ACTIONS:
                assert part.device != "/dev/root"
                assert part.device == RootFsDeviceFinder().find()
            else:
                assert part.device == "/dev/root"


# 025225.python.test_linux.line1380.comment =====================================================================
# 025226.python.test_linux.line1381.comment --- misc
# 025227.python.test_linux.line1382.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestMisc(PsutilTestCase):
    def test_boot_time(self):
        vmstat_value = vmstat('boot time')
        psutil_value = psutil.boot_time()
        assert int(vmstat_value) == int(psutil_value)

    def test_no_procfs_on_import(self):
        my_procfs = self.get_testfn()
        os.mkdir(my_procfs)

        with open(os.path.join(my_procfs, 'stat'), 'w') as f:
            f.write('cpu   0 0 0 0 0 0 0 0 0 0\n')
            f.write('cpu0  0 0 0 0 0 0 0 0 0 0\n')
            f.write('cpu1  0 0 0 0 0 0 0 0 0 0\n')

        try:
            orig_open = open

            def open_mock(name, *args, **kwargs):
                if name.startswith('/proc'):
                    raise FileNotFoundError
                return orig_open(name, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=open_mock):
                reload_module(psutil)

                with pytest.raises(OSError):
                    psutil.cpu_times()
                with pytest.raises(OSError):
                    psutil.cpu_times(percpu=True)
                with pytest.raises(OSError):
                    psutil.cpu_percent()
                with pytest.raises(OSError):
                    psutil.cpu_percent(percpu=True)
                with pytest.raises(OSError):
                    psutil.cpu_times_percent()
                with pytest.raises(OSError):
                    psutil.cpu_times_percent(percpu=True)

                psutil.PROCFS_PATH = my_procfs

                assert psutil.cpu_percent() == 0
                assert sum(psutil.cpu_times_percent()) == 0

                # 025228.python.test_linux.line1430.comment since we don't know the number of CPUs at import time,
                # 025229.python.test_linux.line1431.comment we awkwardly say there are none until the second call
                per_cpu_percent = psutil.cpu_percent(percpu=True)
                assert sum(per_cpu_percent) == 0

                # 025230.python.test_linux.line1435.comment ditto awkward length
                per_cpu_times_percent = psutil.cpu_times_percent(percpu=True)
                assert sum(map(sum, per_cpu_times_percent)) == 0

                # 025231.python.test_linux.line1439.comment much user, very busy
                with open(os.path.join(my_procfs, 'stat'), 'w') as f:
                    f.write('cpu   1 0 0 0 0 0 0 0 0 0\n')
                    f.write('cpu0  1 0 0 0 0 0 0 0 0 0\n')
                    f.write('cpu1  1 0 0 0 0 0 0 0 0 0\n')

                assert psutil.cpu_percent() != 0
                assert sum(psutil.cpu_percent(percpu=True)) != 0
                assert sum(psutil.cpu_times_percent()) != 0
                assert (
                    sum(map(sum, psutil.cpu_times_percent(percpu=True))) != 0
                )
        finally:
            shutil.rmtree(my_procfs)
            reload_module(psutil)

        assert psutil.PROCFS_PATH == '/proc'

    def test_cpu_steal_decrease(self):
        # 025232.python.test_linux.line1458.comment Test cumulative cpu stats decrease. We should ignore this.
        # 025233.python.test_linux.line1459.comment See issue #1210.
        content = textwrap.dedent("""\
            cpu   0 0 0 0 0 0 0 1 0 0
            cpu0  0 0 0 0 0 0 0 1 0 0
            cpu1  0 0 0 0 0 0 0 1 0 0
            """).encode()
        with mock_open_content({"/proc/stat": content}) as m:
            # 025234.python.test_linux.line1466.comment first call to "percent" functions should read the new stat file
            # 025235.python.test_linux.line1467.comment and compare to the "real" file read at import time - so the
            # 025236.python.test_linux.line1468.comment values are meaningless
            psutil.cpu_percent()
            assert m.called
            psutil.cpu_percent(percpu=True)
            psutil.cpu_times_percent()
            psutil.cpu_times_percent(percpu=True)

        content = textwrap.dedent("""\
            cpu   1 0 0 0 0 0 0 0 0 0
            cpu0  1 0 0 0 0 0 0 0 0 0
            cpu1  1 0 0 0 0 0 0 0 0 0
            """).encode()
        with mock_open_content({"/proc/stat": content}):
            # 025237.python.test_linux.line1481.comment Increase "user" while steal goes "backwards" to zero.
            cpu_percent = psutil.cpu_percent()
            assert m.called
            cpu_percent_percpu = psutil.cpu_percent(percpu=True)
            cpu_times_percent = psutil.cpu_times_percent()
            cpu_times_percent_percpu = psutil.cpu_times_percent(percpu=True)
            assert cpu_percent != 0
            assert sum(cpu_percent_percpu) != 0
            assert sum(cpu_times_percent) != 0
            assert sum(cpu_times_percent) != 100.0
            assert sum(map(sum, cpu_times_percent_percpu)) != 0
            assert sum(map(sum, cpu_times_percent_percpu)) != 100.0
            assert cpu_times_percent.steal == 0
            assert cpu_times_percent.user != 0

    def test_boot_time_mocked(self):
        with mock.patch('psutil._common.open', create=True) as m:
            with pytest.raises(RuntimeError):
                psutil._pslinux.boot_time()
            assert m.called

    def test_users(self):
        # 025238.python.test_linux.line1503.comment Make sure the C extension converts ':0' and ':0.0' to
        # 025239.python.test_linux.line1504.comment 'localhost'.
        for user in psutil.users():
            assert user.host not in {":0", ":0.0"}

    def test_procfs_path(self):
        tdir = self.get_testfn()
        os.mkdir(tdir)
        try:
            psutil.PROCFS_PATH = tdir
            with pytest.raises(OSError):
                psutil.virtual_memory()
            with pytest.raises(OSError):
                psutil.cpu_times()
            with pytest.raises(OSError):
                psutil.cpu_times(percpu=True)
            with pytest.raises(OSError):
                psutil.boot_time()
            with pytest.raises(OSError):
                psutil.net_connections()
            with pytest.raises(OSError):
                psutil.net_io_counters()
            with pytest.raises(OSError):
                psutil.net_if_stats()
            with pytest.raises(OSError):
                psutil.disk_partitions()
            with pytest.raises(psutil.NoSuchProcess):
                psutil.Process()
        finally:
            psutil.PROCFS_PATH = "/proc"

    @retry_on_failure()
    @pytest.mark.xdist_group(name="serial")
    def test_issue_687(self):
        # 025240.python.test_linux.line1537.comment In case of thread ID:
        # 025241.python.test_linux.line1538.comment - pid_exists() is supposed to return False
        # 025242.python.test_linux.line1539.comment - Process(tid) is supposed to work
        # 025243.python.test_linux.line1540.comment - pids() should not return the TID
        # 025244.python.test_linux.line1541.comment See: https://github.com/giampaolo/psutil/issues/687

        p = psutil.Process()
        nthreads = len(p.threads())
        with ThreadTask():
            threads = p.threads()
            assert len(threads) == nthreads + 1
            tid = sorted(threads, key=lambda x: x.id)[1].id
            assert p.pid != tid
            pt = psutil.Process(tid)
            pt.as_dict()
            assert tid not in psutil.pids()

    def test_pid_exists_no_proc_status(self):
        # 025245.python.test_linux.line1555.comment Internally pid_exists relies on /proc/{pid}/status.
        # 025246.python.test_linux.line1556.comment Emulate a case where this file is empty in which case
        # 025247.python.test_linux.line1557.comment psutil is supposed to fall back on using pids().
        with mock_open_content({"/proc/%s/status": ""}) as m:
            assert psutil.pid_exists(os.getpid())
            assert m.called


# 025248.python.test_linux.line1563.comment =====================================================================
# 025249.python.test_linux.line1564.comment --- sensors
# 025250.python.test_linux.line1565.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
@pytest.mark.skipif(not HAS_BATTERY, reason="no battery")
class TestSensorsBattery(PsutilTestCase):
    @pytest.mark.skipif(
        not shutil.which("acpi"), reason="acpi utility not available"
    )
    def test_percent(self):
        out = sh("acpi -b")
        acpi_value = int(out.split(",")[1].strip().replace('%', ''))
        psutil_value = psutil.sensors_battery().percent
        assert abs(acpi_value - psutil_value) < 1

    def test_emulate_power_plugged(self):
        # 025251.python.test_linux.line1581.comment Pretend the AC power cable is connected.
        def open_mock(name, *args, **kwargs):
            if name.endswith(('AC0/online', 'AC/online')):
                return io.BytesIO(b"1")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock) as m:
            assert psutil.sensors_battery().power_plugged is True
            assert (
                psutil.sensors_battery().secsleft
                == psutil.POWER_TIME_UNLIMITED
            )
            assert m.called

    def test_emulate_power_plugged_2(self):
        # 025252.python.test_linux.line1598.comment Same as above but pretend /AC0/online does not exist in which
        # 025253.python.test_linux.line1599.comment case code relies on /status file.
        def open_mock(name, *args, **kwargs):
            if name.endswith(('AC0/online', 'AC/online')):
                raise FileNotFoundError
            if name.endswith("/status"):
                return io.StringIO("charging")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock) as m:
            assert psutil.sensors_battery().power_plugged is True
            assert m.called

    def test_emulate_power_not_plugged(self):
        # 025254.python.test_linux.line1614.comment Pretend the AC power cable is not connected.
        def open_mock(name, *args, **kwargs):
            if name.endswith(('AC0/online', 'AC/online')):
                return io.BytesIO(b"0")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock) as m:
            assert psutil.sensors_battery().power_plugged is False
            assert m.called

    def test_emulate_power_not_plugged_2(self):
        # 025255.python.test_linux.line1627.comment Same as above but pretend /AC0/online does not exist in which
        # 025256.python.test_linux.line1628.comment case code relies on /status file.
        def open_mock(name, *args, **kwargs):
            if name.endswith(('AC0/online', 'AC/online')):
                raise FileNotFoundError
            if name.endswith("/status"):
                return io.StringIO("discharging")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock) as m:
            assert psutil.sensors_battery().power_plugged is False
            assert m.called

    def test_emulate_power_undetermined(self):
        # 025257.python.test_linux.line1643.comment Pretend we can't know whether the AC power cable not
        # 025258.python.test_linux.line1644.comment connected (assert fallback to False).
        def open_mock(name, *args, **kwargs):
            if name.startswith((
                '/sys/class/power_supply/AC0/online',
                '/sys/class/power_supply/AC/online',
            )):
                raise FileNotFoundError
            if name.startswith("/sys/class/power_supply/BAT0/status"):
                return io.BytesIO(b"???")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock) as m:
            assert psutil.sensors_battery().power_plugged is None
            assert m.called

    def test_emulate_energy_full_0(self):
        # 025259.python.test_linux.line1662.comment Emulate a case where energy_full files returns 0.
        with mock_open_content(
            {"/sys/class/power_supply/BAT0/energy_full": b"0"}
        ) as m:
            assert psutil.sensors_battery().percent == 0
            assert m.called

    def test_emulate_energy_full_not_avail(self):
        # 025260.python.test_linux.line1670.comment Emulate a case where energy_full file does not exist.
        # 025261.python.test_linux.line1671.comment Expected fallback on /capacity.
        with mock_open_exception(
            "/sys/class/power_supply/BAT0/energy_full",
            FileNotFoundError,
        ):
            with mock_open_exception(
                "/sys/class/power_supply/BAT0/charge_full",
                FileNotFoundError,
            ):
                with mock_open_content(
                    {"/sys/class/power_supply/BAT0/capacity": b"88"}
                ):
                    assert psutil.sensors_battery().percent == 88

    def test_emulate_no_power(self):
        # 025262.python.test_linux.line1686.comment Emulate a case where /AC0/online file nor /BAT0/status exist.
        with mock_open_exception(
            "/sys/class/power_supply/AC/online", FileNotFoundError
        ):
            with mock_open_exception(
                "/sys/class/power_supply/AC0/online", FileNotFoundError
            ):
                with mock_open_exception(
                    "/sys/class/power_supply/BAT0/status",
                    FileNotFoundError,
                ):
                    assert psutil.sensors_battery().power_plugged is None


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSensorsBatteryEmulated(PsutilTestCase):
    def test_it(self):
        def open_mock(name, *args, **kwargs):
            if name.endswith("/energy_now"):
                return io.StringIO("60000000")
            elif name.endswith("/power_now"):
                return io.StringIO("0")
            elif name.endswith("/energy_full"):
                return io.StringIO("60000001")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch('os.listdir', return_value=["BAT0"]) as mlistdir:
            with mock.patch("builtins.open", side_effect=open_mock) as mopen:
                assert psutil.sensors_battery() is not None
        assert mlistdir.called
        assert mopen.called


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSensorsTemperatures(PsutilTestCase):
    def test_emulate_class_hwmon(self):
        def open_mock(name, *args, **kwargs):
            if name.endswith('/name'):
                return io.StringIO("name")
            elif name.endswith('/temp1_label'):
                return io.StringIO("label")
            elif name.endswith('/temp1_input'):
                return io.BytesIO(b"30000")
            elif name.endswith('/temp1_max'):
                return io.BytesIO(b"40000")
            elif name.endswith('/temp1_crit'):
                return io.BytesIO(b"50000")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            # 025263.python.test_linux.line1740.comment Test case with /sys/class/hwmon
            with mock.patch(
                'glob.glob', return_value=['/sys/class/hwmon/hwmon0/temp1']
            ):
                temp = psutil.sensors_temperatures()['name'][0]
                assert temp.label == 'label'
                assert temp.current == 30.0
                assert temp.high == 40.0
                assert temp.critical == 50.0

    def test_emulate_class_thermal(self):
        def open_mock(name, *args, **kwargs):
            if name.endswith('0_temp'):
                return io.BytesIO(b"50000")
            elif name.endswith('temp'):
                return io.BytesIO(b"30000")
            elif name.endswith('0_type'):
                return io.StringIO("critical")
            elif name.endswith('type'):
                return io.StringIO("name")
            else:
                return orig_open(name, *args, **kwargs)

        def glob_mock(path):
            if path in {
                '/sys/class/hwmon/hwmon*/temp*_*',
                '/sys/class/hwmon/hwmon*/device/temp*_*',
            }:
                return []
            elif path == '/sys/class/thermal/thermal_zone*':
                return ['/sys/class/thermal/thermal_zone0']
            elif path == '/sys/class/thermal/thermal_zone0/trip_point*':
                return [
                    '/sys/class/thermal/thermal_zone1/trip_point_0_type',
                    '/sys/class/thermal/thermal_zone1/trip_point_0_temp',
                ]
            return []

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            with mock.patch('glob.glob', create=True, side_effect=glob_mock):
                temp = psutil.sensors_temperatures()['name'][0]
                assert temp.label == ''
                assert temp.current == 30.0
                assert temp.high == 50.0
                assert temp.critical == 50.0


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestSensorsFans(PsutilTestCase):
    def test_emulate_data(self):
        def open_mock(name, *args, **kwargs):
            if name.endswith('/name'):
                return io.StringIO("name")
            elif name.endswith('/fan1_label'):
                return io.StringIO("label")
            elif name.endswith('/fan1_input'):
                return io.StringIO("2000")
            else:
                return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock):
            with mock.patch(
                'glob.glob', return_value=['/sys/class/hwmon/hwmon2/fan1']
            ):
                fan = psutil.sensors_fans()['name'][0]
                assert fan.label == 'label'
                assert fan.current == 2000


# 025264.python.test_linux.line1811.comment =====================================================================
# 025265.python.test_linux.line1812.comment --- test process
# 025266.python.test_linux.line1813.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestProcess(PsutilTestCase):
    @retry_on_failure()
    def test_parse_smaps_vs_memory_maps(self):
        sproc = self.spawn_subproc()
        uss, pss, swap = psutil._pslinux.Process(sproc.pid)._parse_smaps()
        maps = psutil.Process(sproc.pid).memory_maps(grouped=False)
        assert (
            abs(uss - sum(x.private_dirty + x.private_clean for x in maps))
            < 4096
        )
        assert abs(pss - sum(x.pss for x in maps)) < 4096
        assert abs(swap - sum(x.swap for x in maps)) < 4096

    def test_parse_smaps_mocked(self):
        # 025267.python.test_linux.line1831.comment See: https://github.com/giampaolo/psutil/issues/1222
        content = textwrap.dedent("""\
            fffff0 r-xp 00000000 00:00 0                  [vsyscall]
            Size:                  1 kB
            Rss:                   2 kB
            Pss:                   3 kB
            Shared_Clean:          4 kB
            Shared_Dirty:          5 kB
            Private_Clean:         6 kB
            Private_Dirty:         7 kB
            Referenced:            8 kB
            Anonymous:             9 kB
            LazyFree:              10 kB
            AnonHugePages:         11 kB
            ShmemPmdMapped:        12 kB
            Shared_Hugetlb:        13 kB
            Private_Hugetlb:       14 kB
            Swap:                  15 kB
            SwapPss:               16 kB
            KernelPageSize:        17 kB
            MMUPageSize:           18 kB
            Locked:                19 kB
            VmFlags: rd ex
            """).encode()
        with mock_open_content({f"/proc/{os.getpid()}/smaps": content}) as m:
            p = psutil._pslinux.Process(os.getpid())
            uss, pss, swap = p._parse_smaps()
            assert m.called
            assert uss == (6 + 7 + 14) * 1024
            assert pss == 3 * 1024
            assert swap == 15 * 1024

    def test_open_files_mode(self):
        def get_test_file(fname):
            p = psutil.Process()
            giveup_at = time.time() + GLOBAL_TIMEOUT
            while True:
                for file in p.open_files():
                    if file.path == os.path.abspath(fname):
                        return file
                    elif time.time() > giveup_at:
                        break
            raise RuntimeError("timeout looking for test file")

        testfn = self.get_testfn()
        with open(testfn, "w"):
            assert get_test_file(testfn).mode == "w"
        with open(testfn):
            assert get_test_file(testfn).mode == "r"
        with open(testfn, "a"):
            assert get_test_file(testfn).mode == "a"
        with open(testfn, "r+"):
            assert get_test_file(testfn).mode == "r+"
        with open(testfn, "w+"):
            assert get_test_file(testfn).mode == "r+"
        with open(testfn, "a+"):
            assert get_test_file(testfn).mode == "a+"

        safe_rmpath(testfn)
        with open(testfn, "x"):
            assert get_test_file(testfn).mode == "w"
        safe_rmpath(testfn)
        with open(testfn, "x+"):
            assert get_test_file(testfn).mode == "r+"

    def test_open_files_file_gone(self):
        # 025268.python.test_linux.line1897.comment simulates a file which gets deleted during open_files()
        # 025269.python.test_linux.line1898.comment execution
        p = psutil.Process()
        files = p.open_files()
        with open(self.get_testfn(), 'w'):
            # 025270.python.test_linux.line1902.comment give the kernel some time to see the new file
            call_until(lambda: len(p.open_files()) != len(files))
            with mock.patch(
                'psutil._pslinux.os.readlink',
                side_effect=FileNotFoundError,
            ) as m:
                assert p.open_files() == []
                assert m.called
            # 025271.python.test_linux.line1910.comment also simulate the case where os.readlink() returns EINVAL
            # 025272.python.test_linux.line1911.comment in which case psutil is supposed to 'continue'
            with mock.patch(
                'psutil._pslinux.os.readlink',
                side_effect=OSError(errno.EINVAL, ""),
            ) as m:
                assert p.open_files() == []
                assert m.called

    def test_open_files_fd_gone(self):
        # 025273.python.test_linux.line1920.comment Simulate a case where /proc/{pid}/fdinfo/{fd} disappears
        # 025274.python.test_linux.line1921.comment while iterating through fds.
        # 025275.python.test_linux.line1922.comment https://travis-ci.org/giampaolo/psutil/jobs/225694530
        p = psutil.Process()
        files = p.open_files()
        with open(self.get_testfn(), 'w'):
            # 025276.python.test_linux.line1926.comment give the kernel some time to see the new file
            call_until(lambda: len(p.open_files()) != len(files))
            with mock.patch(
                "builtins.open", side_effect=FileNotFoundError
            ) as m:
                assert p.open_files() == []
                assert m.called

    def test_open_files_enametoolong(self):
        # 025277.python.test_linux.line1935.comment Simulate a case where /proc/{pid}/fd/{fd} symlink
        # 025278.python.test_linux.line1936.comment points to a file with full path longer than PATH_MAX, see:
        # 025279.python.test_linux.line1937.comment https://github.com/giampaolo/psutil/issues/1940
        p = psutil.Process()
        files = p.open_files()
        with open(self.get_testfn(), 'w'):
            # 025280.python.test_linux.line1941.comment give the kernel some time to see the new file
            call_until(lambda: len(p.open_files()) != len(files))
            patch_point = 'psutil._pslinux.os.readlink'
            with mock.patch(
                patch_point, side_effect=OSError(errno.ENAMETOOLONG, "")
            ) as m:
                with mock.patch("psutil._pslinux.debug"):
                    assert p.open_files() == []
                    assert m.called

    # 025281.python.test_linux.line1951.comment --- mocked tests

    def test_terminal_mocked(self):
        with mock.patch(
            'psutil._pslinux._psposix.get_terminal_map', return_value={}
        ) as m:
            assert psutil._pslinux.Process(os.getpid()).terminal() is None
            assert m.called

    def test_cmdline_mocked(self):
        # 025282.python.test_linux.line1961.comment see: https://github.com/giampaolo/psutil/issues/639
        p = psutil.Process()
        fake_file = io.StringIO('foo\x00bar\x00')
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m:
            assert p.cmdline() == ['foo', 'bar']
            assert m.called
        fake_file = io.StringIO('foo\x00bar\x00\x00')
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m:
            assert p.cmdline() == ['foo', 'bar', '']
            assert m.called

    def test_cmdline_spaces_mocked(self):
        # 025283.python.test_linux.line1977.comment see: https://github.com/giampaolo/psutil/issues/1179
        p = psutil.Process()
        fake_file = io.StringIO('foo bar ')
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m:
            assert p.cmdline() == ['foo', 'bar']
            assert m.called
        fake_file = io.StringIO('foo bar  ')
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m:
            assert p.cmdline() == ['foo', 'bar', '']
            assert m.called

    def test_cmdline_mixed_separators(self):
        # 025284.python.test_linux.line1993.comment https://github.com/giampaolo/psutil/issues/
        # 025285.python.test_linux.line1994.comment 1179#issuecomment-552984549
        p = psutil.Process()
        fake_file = io.StringIO('foo\x20bar\x00')
        with mock.patch(
            'psutil._common.open', return_value=fake_file, create=True
        ) as m:
            assert p.cmdline() == ['foo', 'bar']
            assert m.called

    def test_readlink_path_deleted_mocked(self):
        with mock.patch(
            'psutil._pslinux.os.readlink', return_value='/home/foo (deleted)'
        ):
            assert psutil.Process().exe() == "/home/foo"
            assert psutil.Process().cwd() == "/home/foo"

    def test_threads_mocked(self):
        # 025286.python.test_linux.line2011.comment Test the case where os.listdir() returns a file (thread)
        # 025287.python.test_linux.line2012.comment which no longer exists by the time we open() it (race
        # 025288.python.test_linux.line2013.comment condition). threads() is supposed to ignore that instead
        # 025289.python.test_linux.line2014.comment of raising NSP.
        def open_mock_1(name, *args, **kwargs):
            if name.startswith(f"/proc/{os.getpid()}/task"):
                raise FileNotFoundError
            return orig_open(name, *args, **kwargs)

        orig_open = open
        with mock.patch("builtins.open", side_effect=open_mock_1) as m:
            ret = psutil.Process().threads()
            assert m.called
            assert ret == []

        # 025290.python.test_linux.line2026.comment ...but if it bumps into something != ENOENT we want an
        # 025291.python.test_linux.line2027.comment exception.
        def open_mock_2(name, *args, **kwargs):
            if name.startswith(f"/proc/{os.getpid()}/task"):
                raise PermissionError
            return orig_open(name, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=open_mock_2):
            with pytest.raises(psutil.AccessDenied):
                psutil.Process().threads()

    def test_exe_mocked(self):
        with mock.patch(
            'psutil._pslinux.readlink', side_effect=FileNotFoundError
        ) as m:
            # 025292.python.test_linux.line2041.comment de-activate guessing from cmdline()
            with mock.patch(
                'psutil._pslinux.Process.cmdline', return_value=[]
            ):
                ret = psutil.Process().exe()
                assert m.called
                assert ret == ""

    def test_cwd_mocked(self):
        # 025293.python.test_linux.line2050.comment https://github.com/giampaolo/psutil/issues/2514
        with mock.patch(
            'psutil._pslinux.readlink', side_effect=FileNotFoundError
        ) as m:
            ret = psutil.Process().cwd()
            assert m.called
            assert ret == ""

    def test_issue_1014(self):
        # 025294.python.test_linux.line2059.comment Emulates a case where smaps file does not exist. In this case
        # 025295.python.test_linux.line2060.comment wrap_exception decorator should not raise NoSuchProcess.
        with mock_open_exception(
            f"/proc/{os.getpid()}/smaps", FileNotFoundError
        ) as m:
            p = psutil.Process()
            with pytest.raises(FileNotFoundError):
                p.memory_maps()
            assert m.called

    def test_issue_2418(self):
        p = psutil.Process()
        with mock_open_exception(
            f"/proc/{os.getpid()}/statm", FileNotFoundError
        ):
            with mock.patch("os.path.exists", return_value=False):
                with pytest.raises(psutil.NoSuchProcess):
                    p.memory_info()

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit_zombie(self):
        # 025296.python.test_linux.line2080.comment Emulate a case where rlimit() raises ENOSYS, which may
        # 025297.python.test_linux.line2081.comment happen in case of zombie process:
        # 025298.python.test_linux.line2082.comment https://travis-ci.org/giampaolo/psutil/jobs/51368273
        with mock.patch(
            "resource.prlimit", side_effect=OSError(errno.ENOSYS, "")
        ) as m1:
            with mock.patch(
                "psutil._pslinux.Process._is_zombie", return_value=True
            ) as m2:
                p = psutil.Process()
                p.name()
                with pytest.raises(psutil.ZombieProcess) as cm:
                    p.rlimit(psutil.RLIMIT_NOFILE)
        assert m1.called
        assert m2.called
        assert cm.value.pid == p.pid
        assert cm.value.name == p.name()

    def test_stat_file_parsing(self):
        args = [
            "0",  # pid
            "(cat)",  # name
            "Z",  # status
            "1",  # ppid
            "0",  # pgrp
            "0",  # session
            "0",  # tty
            "0",  # tpgid
            "0",  # flags
            "0",  # minflt
            "0",  # cminflt
            "0",  # majflt
            "0",  # cmajflt
            "2",  # utime
            "3",  # stime
            "4",  # cutime
            "5",  # cstime
            "0",  # priority
            "0",  # nice
            "0",  # num_threads
            "0",  # itrealvalue
            "6",  # starttime
            "0",  # vsize
            "0",  # rss
            "0",  # rsslim
            "0",  # startcode
            "0",  # endcode
            "0",  # startstack
            "0",  # kstkesp
            "0",  # kstkeip
            "0",  # signal
            "0",  # blocked
            "0",  # sigignore
            "0",  # sigcatch
            "0",  # wchan
            "0",  # nswap
            "0",  # cnswap
            "0",  # exit_signal
            "6",  # processor
            "0",  # rt priority
            "0",  # policy
            "7",  # delayacct_blkio_ticks
        ]
        content = " ".join(args).encode()
        with mock_open_content({f"/proc/{os.getpid()}/stat": content}):
            p = psutil.Process()
            assert p.name() == 'cat'
            assert p.status() == psutil.STATUS_ZOMBIE
            assert p.ppid() == 1
            assert p.create_time() == 6 / CLOCK_TICKS + psutil.boot_time()
            cpu = p.cpu_times()
            assert cpu.user == 2 / CLOCK_TICKS
            assert cpu.system == 3 / CLOCK_TICKS
            assert cpu.children_user == 4 / CLOCK_TICKS
            assert cpu.children_system == 5 / CLOCK_TICKS
            assert cpu.iowait == 7 / CLOCK_TICKS
            assert p.cpu_num() == 6

    def test_status_file_parsing(self):
        content = textwrap.dedent("""\
            Uid:\t1000\t1001\t1002\t1003
            Gid:\t1004\t1005\t1006\t1007
            Threads:\t66
            Cpus_allowed:\tf
            Cpus_allowed_list:\t0-7
            voluntary_ctxt_switches:\t12
            nonvoluntary_ctxt_switches:\t13""").encode()
        with mock_open_content({f"/proc/{os.getpid()}/status": content}):
            p = psutil.Process()
            assert p.num_ctx_switches().voluntary == 12
            assert p.num_ctx_switches().involuntary == 13
            assert p.num_threads() == 66
            uids = p.uids()
            assert uids.real == 1000
            assert uids.effective == 1001
            assert uids.saved == 1002
            gids = p.gids()
            assert gids.real == 1004
            assert gids.effective == 1005
            assert gids.saved == 1006
            assert p._proc._get_eligible_cpus() == list(range(8))

    def test_net_connections_enametoolong(self):
        # 025341.python.test_linux.line2183.comment Simulate a case where /proc/{pid}/fd/{fd} symlink points to
        # 025342.python.test_linux.line2184.comment a file with full path longer than PATH_MAX, see:
        # 025343.python.test_linux.line2185.comment https://github.com/giampaolo/psutil/issues/1940
        with mock.patch(
            'psutil._pslinux.os.readlink',
            side_effect=OSError(errno.ENAMETOOLONG, ""),
        ) as m:
            p = psutil.Process()
            with mock.patch("psutil._pslinux.debug"):
                assert p.net_connections() == []
                assert m.called

    def test_create_time_monotonic(self):
        p = psutil.Process()
        assert p._proc.create_time() != p._proc.create_time(monotonic=True)
        assert p._get_ident()[1] == p._proc.create_time(monotonic=True)


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestProcessAgainstStatus(PsutilTestCase):
    """/proc/pid/stat and /proc/pid/status have many values in common.
    Whenever possible, psutil uses /proc/pid/stat (it's faster).
    For all those cases we check that the value found in
    /proc/pid/stat (by psutil) matches the one found in
    /proc/pid/status.
    """

    @classmethod
    def setUpClass(cls):
        cls.proc = psutil.Process()

    def read_status_file(self, linestart):
        with psutil._psplatform.open_text(
            f"/proc/{self.proc.pid}/status"
        ) as f:
            for line in f:
                line = line.strip()
                if line.startswith(linestart):
                    value = line.partition('\t')[2]
                    try:
                        return int(value)
                    except ValueError:
                        return value
            raise ValueError(f"can't find {linestart!r}")

    def test_name(self):
        value = self.read_status_file("Name:")
        assert self.proc.name() == value

    def test_status(self):
        value = self.read_status_file("State:")
        value = value[value.find('(') + 1 : value.rfind(')')]
        value = value.replace(' ', '-')
        assert self.proc.status() == value

    def test_ppid(self):
        value = self.read_status_file("PPid:")
        assert self.proc.ppid() == value

    def test_num_threads(self):
        value = self.read_status_file("Threads:")
        assert self.proc.num_threads() == value

    def test_uids(self):
        value = self.read_status_file("Uid:")
        value = tuple(map(int, value.split()[1:4]))
        assert self.proc.uids() == value

    def test_gids(self):
        value = self.read_status_file("Gid:")
        value = tuple(map(int, value.split()[1:4]))
        assert self.proc.gids() == value

    @retry_on_failure()
    def test_num_ctx_switches(self):
        value = self.read_status_file("voluntary_ctxt_switches:")
        assert self.proc.num_ctx_switches().voluntary == value
        value = self.read_status_file("nonvoluntary_ctxt_switches:")
        assert self.proc.num_ctx_switches().involuntary == value

    def test_cpu_affinity(self):
        value = self.read_status_file("Cpus_allowed_list:")
        if '-' in str(value):
            min_, max_ = map(int, value.split('-'))
            assert self.proc.cpu_affinity() == list(range(min_, max_ + 1))

    def test_cpu_affinity_eligible_cpus(self):
        value = self.read_status_file("Cpus_allowed_list:")
        with mock.patch("psutil._pslinux.per_cpu_times") as m:
            self.proc._proc._get_eligible_cpus()
        if '-' in str(value):
            assert not m.called
        else:
            assert m.called


# 025344.python.test_linux.line2279.comment =====================================================================
# 025345.python.test_linux.line2280.comment --- test utils
# 025346.python.test_linux.line2281.comment =====================================================================


@pytest.mark.skipif(not LINUX, reason="LINUX only")
class TestUtils(PsutilTestCase):
    def test_readlink(self):
        with mock.patch("os.readlink", return_value="foo (deleted)") as m:
            assert psutil._psplatform.readlink("bar") == "foo"
            assert m.called
