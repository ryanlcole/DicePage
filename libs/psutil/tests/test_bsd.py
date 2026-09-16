#!/usr/bin/env python3

# 024973.python.test_bsd.line3.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 024974.python.test_bsd.line4.comment Use of this source code is governed by a BSD-style license that can be
# 024975.python.test_bsd.line5.comment found in the LICENSE file.

# 024976.python.test_bsd.line7.comment TODO: (FreeBSD) add test for comparing connections with 'sockstat' cmd.


"""Tests specific to all BSD platforms."""

import datetime
import os
import re
import shutil
import time

import psutil
from psutil import BSD
from psutil import FREEBSD
from psutil import NETBSD
from psutil import OPENBSD
from psutil.tests import HAS_BATTERY
from psutil.tests import TOLERANCE_SYS_MEM
from psutil.tests import PsutilTestCase
from psutil.tests import pytest
from psutil.tests import retry_on_failure
from psutil.tests import sh
from psutil.tests import spawn_subproc
from psutil.tests import terminate

if BSD:
    from psutil._psutil_posix import getpagesize

    PAGESIZE = getpagesize()
    # 024977.python.test_bsd.line36.comment muse requires root privileges
    MUSE_AVAILABLE = os.getuid() == 0 and shutil.which("muse")
else:
    PAGESIZE = None
    MUSE_AVAILABLE = False


def sysctl(cmdline):
    """Expects a sysctl command with an argument and parse the result
    returning only the value of interest.
    """
    result = sh("sysctl " + cmdline)
    if FREEBSD:
        result = result[result.find(": ") + 2 :]
    elif OPENBSD or NETBSD:
        result = result[result.find("=") + 1 :]
    try:
        return int(result)
    except ValueError:
        return result


def muse(field):
    """Thin wrapper around 'muse' cmdline utility."""
    out = sh('muse')
    for line in out.split('\n'):
        if line.startswith(field):
            break
    else:
        raise ValueError("line not found")
    return int(line.split()[1])


# 024978.python.test_bsd.line69.comment =====================================================================
# 024979.python.test_bsd.line70.comment --- All BSD*
# 024980.python.test_bsd.line71.comment =====================================================================


@pytest.mark.skipif(not BSD, reason="BSD only")
class BSDTestCase(PsutilTestCase):
    """Generic tests common to all BSD variants."""

    @classmethod
    def setUpClass(cls):
        cls.pid = spawn_subproc().pid

    @classmethod
    def tearDownClass(cls):
        terminate(cls.pid)

    @pytest.mark.skipif(NETBSD, reason="-o lstart doesn't work on NETBSD")
    def test_process_create_time(self):
        output = sh(f"ps -o lstart -p {self.pid}")
        start_ps = output.replace('STARTED', '').strip()
        start_psutil = psutil.Process(self.pid).create_time()
        start_psutil = time.strftime(
            "%a %b %e %H:%M:%S %Y", time.localtime(start_psutil)
        )
        assert start_ps == start_psutil

    def test_disks(self):
        # 024981.python.test_bsd.line97.comment test psutil.disk_usage() and psutil.disk_partitions()
        # 024982.python.test_bsd.line98.comment against "df -a"
        def df(path):
            out = sh(f'df -k "{path}"').strip()
            lines = out.split('\n')
            lines.pop(0)
            line = lines.pop(0)
            dev, total, used, free = line.split()[:4]
            if dev == 'none':
                dev = ''
            total = int(total) * 1024
            used = int(used) * 1024
            free = int(free) * 1024
            return dev, total, used, free

        for part in psutil.disk_partitions(all=False):
            usage = psutil.disk_usage(part.mountpoint)
            dev, total, used, free = df(part.mountpoint)
            assert part.device == dev
            assert usage.total == total
            # 024983.python.test_bsd.line117.comment 10 MB tolerance
            if abs(usage.free - free) > 10 * 1024 * 1024:
                raise pytest.fail(f"psutil={usage.free}, df={free}")
            if abs(usage.used - used) > 10 * 1024 * 1024:
                raise pytest.fail(f"psutil={usage.used}, df={used}")

    @pytest.mark.skipif(
        not shutil.which("sysctl"), reason="sysctl cmd not available"
    )
    def test_cpu_count_logical(self):
        syst = sysctl("hw.ncpu")
        assert psutil.cpu_count(logical=True) == syst

    @pytest.mark.skipif(
        not shutil.which("sysctl"), reason="sysctl cmd not available"
    )
    @pytest.mark.skipif(
        NETBSD, reason="skipped on NETBSD"  # we check /proc/meminfo
    )
    def test_virtual_memory_total(self):
        num = sysctl('hw.physmem')
        assert num == psutil.virtual_memory().total

    @pytest.mark.skipif(
        not shutil.which("ifconfig"), reason="ifconfig cmd not available"
    )
    def test_net_if_stats(self):
        for name, stats in psutil.net_if_stats().items():
            try:
                out = sh(f"ifconfig {name}")
            except RuntimeError:
                pass
            else:
                assert stats.isup == ('RUNNING' in out)
                if "mtu" in out:
                    assert stats.mtu == int(re.findall(r'mtu (\d+)', out)[0])


# 024985.python.test_bsd.line155.comment =====================================================================
# 024986.python.test_bsd.line156.comment --- FreeBSD
# 024987.python.test_bsd.line157.comment =====================================================================


@pytest.mark.skipif(not FREEBSD, reason="FREEBSD only")
class FreeBSDPsutilTestCase(PsutilTestCase):
    @classmethod
    def setUpClass(cls):
        cls.pid = spawn_subproc().pid

    @classmethod
    def tearDownClass(cls):
        terminate(cls.pid)

    @retry_on_failure()
    def test_memory_maps(self):
        out = sh(f"procstat -v {self.pid}")
        maps = psutil.Process(self.pid).memory_maps(grouped=False)
        lines = out.split('\n')[1:]
        while lines:
            line = lines.pop()
            fields = line.split()
            _, start, stop, _perms, res = fields[:5]
            map = maps.pop()
            assert f"{start}-{stop}" == map.addr
            assert int(res) == map.rss
            if not map.path.startswith('['):
                assert fields[10] == map.path

    def test_exe(self):
        out = sh(f"procstat -b {self.pid}")
        assert psutil.Process(self.pid).exe() == out.split('\n')[1].split()[-1]

    def test_cmdline(self):
        out = sh(f"procstat -c {self.pid}")
        assert ' '.join(psutil.Process(self.pid).cmdline()) == ' '.join(
            out.split('\n')[1].split()[2:]
        )

    def test_uids_gids(self):
        out = sh(f"procstat -s {self.pid}")
        euid, ruid, suid, egid, rgid, sgid = out.split('\n')[1].split()[2:8]
        p = psutil.Process(self.pid)
        uids = p.uids()
        gids = p.gids()
        assert uids.real == int(ruid)
        assert uids.effective == int(euid)
        assert uids.saved == int(suid)
        assert gids.real == int(rgid)
        assert gids.effective == int(egid)
        assert gids.saved == int(sgid)

    @retry_on_failure()
    def test_ctx_switches(self):
        tested = []
        out = sh(f"procstat -r {self.pid}")
        p = psutil.Process(self.pid)
        for line in out.split('\n'):
            line = line.lower().strip()
            if ' voluntary context' in line:
                pstat_value = int(line.split()[-1])
                psutil_value = p.num_ctx_switches().voluntary
                assert pstat_value == psutil_value
                tested.append(None)
            elif ' involuntary context' in line:
                pstat_value = int(line.split()[-1])
                psutil_value = p.num_ctx_switches().involuntary
                assert pstat_value == psutil_value
                tested.append(None)
        if len(tested) != 2:
            raise RuntimeError("couldn't find lines match in procstat out")

    @retry_on_failure()
    def test_cpu_times(self):
        tested = []
        out = sh(f"procstat -r {self.pid}")
        p = psutil.Process(self.pid)
        for line in out.split('\n'):
            line = line.lower().strip()
            if 'user time' in line:
                pstat_value = float('0.' + line.split()[-1].split('.')[-1])
                psutil_value = p.cpu_times().user
                assert pstat_value == psutil_value
                tested.append(None)
            elif 'system time' in line:
                pstat_value = float('0.' + line.split()[-1].split('.')[-1])
                psutil_value = p.cpu_times().system
                assert pstat_value == psutil_value
                tested.append(None)
        if len(tested) != 2:
            raise RuntimeError("couldn't find lines match in procstat out")


@pytest.mark.skipif(not FREEBSD, reason="FREEBSD only")
class FreeBSDSystemTestCase(PsutilTestCase):
    @staticmethod
    def parse_swapinfo():
        # 024988.python.test_bsd.line253.comment the last line is always the total
        output = sh("swapinfo -k").splitlines()[-1]
        parts = re.split(r'\s+', output)

        if not parts:
            raise ValueError(f"Can't parse swapinfo: {output}")

        # 024989.python.test_bsd.line260.comment the size is in 1k units, so multiply by 1024
        total, used, free = (int(p) * 1024 for p in parts[1:4])
        return total, used, free

    def test_cpu_frequency_against_sysctl(self):
        # 024990.python.test_bsd.line265.comment Currently only cpu 0 is frequency is supported in FreeBSD
        # 024991.python.test_bsd.line266.comment All other cores use the same frequency.
        sensor = "dev.cpu.0.freq"
        try:
            sysctl_result = int(sysctl(sensor))
        except RuntimeError:
            raise pytest.skip("frequencies not supported by kernel")
        assert psutil.cpu_freq().current == sysctl_result

        sensor = "dev.cpu.0.freq_levels"
        sysctl_result = sysctl(sensor)
        # 024992.python.test_bsd.line276.comment sysctl returns a string of the format:
        # 024993.python.test_bsd.line277.comment <freq_level_1>/<voltage_level_1> <freq_level_2>/<voltage_level_2>...
        # 024994.python.test_bsd.line278.comment Ordered highest available to lowest available.
        max_freq = int(sysctl_result.split()[0].split("/")[0])
        min_freq = int(sysctl_result.split()[-1].split("/")[0])
        assert psutil.cpu_freq().max == max_freq
        assert psutil.cpu_freq().min == min_freq

    # 024995.python.test_bsd.line284.comment --- virtual_memory(); tests against sysctl

    @retry_on_failure()
    def test_vmem_active(self):
        syst = sysctl("vm.stats.vm.v_active_count") * PAGESIZE
        assert abs(psutil.virtual_memory().active - syst) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_vmem_inactive(self):
        syst = sysctl("vm.stats.vm.v_inactive_count") * PAGESIZE
        assert abs(psutil.virtual_memory().inactive - syst) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_vmem_wired(self):
        syst = sysctl("vm.stats.vm.v_wire_count") * PAGESIZE
        assert abs(psutil.virtual_memory().wired - syst) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_vmem_cached(self):
        syst = sysctl("vm.stats.vm.v_cache_count") * PAGESIZE
        assert abs(psutil.virtual_memory().cached - syst) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_vmem_free(self):
        syst = sysctl("vm.stats.vm.v_free_count") * PAGESIZE
        assert abs(psutil.virtual_memory().free - syst) < TOLERANCE_SYS_MEM

    @retry_on_failure()
    def test_vmem_buffers(self):
        syst = sysctl("vfs.bufspace")
        assert abs(psutil.virtual_memory().buffers - syst) < TOLERANCE_SYS_MEM

    # 024996.python.test_bsd.line316.comment --- virtual_memory(); tests against muse

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    def test_muse_vmem_total(self):
        num = muse('Total')
        assert psutil.virtual_memory().total == num

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_active(self):
        num = muse('Active')
        assert abs(psutil.virtual_memory().active - num) < TOLERANCE_SYS_MEM

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_inactive(self):
        num = muse('Inactive')
        assert abs(psutil.virtual_memory().inactive - num) < TOLERANCE_SYS_MEM

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_wired(self):
        num = muse('Wired')
        assert abs(psutil.virtual_memory().wired - num) < TOLERANCE_SYS_MEM

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_cached(self):
        num = muse('Cache')
        assert abs(psutil.virtual_memory().cached - num) < TOLERANCE_SYS_MEM

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_free(self):
        num = muse('Free')
        assert abs(psutil.virtual_memory().free - num) < TOLERANCE_SYS_MEM

    @pytest.mark.skipif(not MUSE_AVAILABLE, reason="muse not installed")
    @retry_on_failure()
    def test_muse_vmem_buffers(self):
        num = muse('Buffer')
        assert abs(psutil.virtual_memory().buffers - num) < TOLERANCE_SYS_MEM

    def test_cpu_stats_ctx_switches(self):
        assert (
            abs(
                psutil.cpu_stats().ctx_switches
                - sysctl('vm.stats.sys.v_swtch')
            )
            < 1000
        )

    def test_cpu_stats_interrupts(self):
        assert (
            abs(psutil.cpu_stats().interrupts - sysctl('vm.stats.sys.v_intr'))
            < 1000
        )

    def test_cpu_stats_soft_interrupts(self):
        assert (
            abs(
                psutil.cpu_stats().soft_interrupts
                - sysctl('vm.stats.sys.v_soft')
            )
            < 1000
        )

    @retry_on_failure()
    def test_cpu_stats_syscalls(self):
        # 024997.python.test_bsd.line385.comment pretty high tolerance but it looks like it's OK.
        assert (
            abs(psutil.cpu_stats().syscalls - sysctl('vm.stats.sys.v_syscall'))
            < 200000
        )

    # 024998.python.test_bsd.line391.comment --- swap memory

    def test_swapmem_free(self):
        _total, _used, free = self.parse_swapinfo()
        assert abs(psutil.swap_memory().free - free) < TOLERANCE_SYS_MEM

    def test_swapmem_used(self):
        _total, used, _free = self.parse_swapinfo()
        assert abs(psutil.swap_memory().used - used) < TOLERANCE_SYS_MEM

    def test_swapmem_total(self):
        total, _used, _free = self.parse_swapinfo()
        assert abs(psutil.swap_memory().total - total) < TOLERANCE_SYS_MEM

    # 024999.python.test_bsd.line405.comment --- others

    def test_boot_time(self):
        s = sysctl('sysctl kern.boottime')
        s = s[s.find(" sec = ") + 7 :]
        s = s[: s.find(',')]
        btime = int(s)
        assert btime == psutil.boot_time()

    # 025000.python.test_bsd.line414.comment --- sensors_battery

    @pytest.mark.skipif(not HAS_BATTERY, reason="no battery")
    def test_sensors_battery(self):
        def secs2hours(secs):
            m, _s = divmod(secs, 60)
            h, m = divmod(m, 60)
            return f"{int(h)}:{int(m):02}"

        out = sh("acpiconf -i 0")
        fields = {x.split('\t')[0]: x.split('\t')[-1] for x in out.split("\n")}
        metrics = psutil.sensors_battery()
        percent = int(fields['Remaining capacity:'].replace('%', ''))
        remaining_time = fields['Remaining time:']
        assert metrics.percent == percent
        if remaining_time == 'unknown':
            assert metrics.secsleft == psutil.POWER_TIME_UNLIMITED
        else:
            assert secs2hours(metrics.secsleft) == remaining_time

    @pytest.mark.skipif(not HAS_BATTERY, reason="no battery")
    def test_sensors_battery_against_sysctl(self):
        assert psutil.sensors_battery().percent == sysctl(
            "hw.acpi.battery.life"
        )
        assert psutil.sensors_battery().power_plugged == (
            sysctl("hw.acpi.acline") == 1
        )
        secsleft = psutil.sensors_battery().secsleft
        if secsleft < 0:
            assert sysctl("hw.acpi.battery.time") == -1
        else:
            assert secsleft == sysctl("hw.acpi.battery.time") * 60

    @pytest.mark.skipif(HAS_BATTERY, reason="has battery")
    def test_sensors_battery_no_battery(self):
        # 025001.python.test_bsd.line450.comment If no battery is present one of these calls is supposed
        # 025002.python.test_bsd.line451.comment to fail, see:
        # 025003.python.test_bsd.line452.comment https://github.com/giampaolo/psutil/issues/1074
        with pytest.raises(RuntimeError):
            sysctl("hw.acpi.battery.life")
            sysctl("hw.acpi.battery.time")
            sysctl("hw.acpi.acline")
        assert psutil.sensors_battery() is None

    # 025004.python.test_bsd.line459.comment --- sensors_temperatures

    def test_sensors_temperatures_against_sysctl(self):
        num_cpus = psutil.cpu_count(True)
        for cpu in range(num_cpus):
            sensor = f"dev.cpu.{cpu}.temperature"
            # 025005.python.test_bsd.line465.comment sysctl returns a string in the format 46.0C
            try:
                sysctl_result = int(float(sysctl(sensor)[:-1]))
            except RuntimeError:
                raise pytest.skip("temperatures not supported by kernel")
            assert (
                abs(
                    psutil.sensors_temperatures()["coretemp"][cpu].current
                    - sysctl_result
                )
                < 10
            )

            sensor = f"dev.cpu.{cpu}.coretemp.tjmax"
            sysctl_result = int(float(sysctl(sensor)[:-1]))
            assert (
                psutil.sensors_temperatures()["coretemp"][cpu].high
                == sysctl_result
            )


# 025006.python.test_bsd.line486.comment =====================================================================
# 025007.python.test_bsd.line487.comment --- OpenBSD
# 025008.python.test_bsd.line488.comment =====================================================================


@pytest.mark.skipif(not OPENBSD, reason="OPENBSD only")
class OpenBSDTestCase(PsutilTestCase):
    def test_boot_time(self):
        s = sysctl('kern.boottime')
        sys_bt = datetime.datetime.strptime(s, "%a %b %d %H:%M:%S %Y")
        psutil_bt = datetime.datetime.fromtimestamp(psutil.boot_time())
        assert sys_bt == psutil_bt


# 025009.python.test_bsd.line500.comment =====================================================================
# 025010.python.test_bsd.line501.comment --- NetBSD
# 025011.python.test_bsd.line502.comment =====================================================================


@pytest.mark.skipif(not NETBSD, reason="NETBSD only")
class NetBSDTestCase(PsutilTestCase):
    @staticmethod
    def parse_meminfo(look_for):
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith(look_for):
                    return int(line.split()[1]) * 1024
        raise ValueError(f"can't find {look_for}")

    # 025012.python.test_bsd.line515.comment --- virtual mem

    def test_vmem_total(self):
        assert psutil.virtual_memory().total == self.parse_meminfo("MemTotal:")

    def test_vmem_free(self):
        assert (
            abs(psutil.virtual_memory().free - self.parse_meminfo("MemFree:"))
            < TOLERANCE_SYS_MEM
        )

    def test_vmem_buffers(self):
        assert (
            abs(
                psutil.virtual_memory().buffers
                - self.parse_meminfo("Buffers:")
            )
            < TOLERANCE_SYS_MEM
        )

    def test_vmem_shared(self):
        assert (
            abs(
                psutil.virtual_memory().shared
                - self.parse_meminfo("MemShared:")
            )
            < TOLERANCE_SYS_MEM
        )

    def test_vmem_cached(self):
        assert (
            abs(psutil.virtual_memory().cached - self.parse_meminfo("Cached:"))
            < TOLERANCE_SYS_MEM
        )

    # 025013.python.test_bsd.line550.comment --- swap mem

    def test_swapmem_total(self):
        assert (
            abs(psutil.swap_memory().total - self.parse_meminfo("SwapTotal:"))
            < TOLERANCE_SYS_MEM
        )

    def test_swapmem_free(self):
        assert (
            abs(psutil.swap_memory().free - self.parse_meminfo("SwapFree:"))
            < TOLERANCE_SYS_MEM
        )

    def test_swapmem_used(self):
        smem = psutil.swap_memory()
        assert smem.used == smem.total - smem.free

    # 025014.python.test_bsd.line568.comment --- others

    def test_cpu_stats_interrupts(self):
        with open('/proc/stat', 'rb') as f:
            for line in f:
                if line.startswith(b'intr'):
                    interrupts = int(line.split()[1])
                    break
            else:
                raise ValueError("couldn't find line")
        assert abs(psutil.cpu_stats().interrupts - interrupts) < 1000

    def test_cpu_stats_ctx_switches(self):
        with open('/proc/stat', 'rb') as f:
            for line in f:
                if line.startswith(b'ctxt'):
                    ctx_switches = int(line.split()[1])
                    break
            else:
                raise ValueError("couldn't find line")
        assert abs(psutil.cpu_stats().ctx_switches - ctx_switches) < 1000
