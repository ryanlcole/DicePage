#!/usr/bin/env python3

# 025533.python.test_process.line3.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 025534.python.test_process.line4.comment Use of this source code is governed by a BSD-style license that can be
# 025535.python.test_process.line5.comment found in the LICENSE file.

"""Tests for psutil.Process class."""

import collections
import contextlib
import errno
import getpass
import io
import itertools
import os
import signal
import socket
import stat
import string
import subprocess
import sys
import textwrap
import time
from unittest import mock

import psutil
from psutil import AIX
from psutil import BSD
from psutil import LINUX
from psutil import MACOS
from psutil import NETBSD
from psutil import OPENBSD
from psutil import OSX
from psutil import POSIX
from psutil import WINDOWS
from psutil._common import open_text
from psutil.tests import CI_TESTING
from psutil.tests import GITHUB_ACTIONS
from psutil.tests import GLOBAL_TIMEOUT
from psutil.tests import HAS_CPU_AFFINITY
from psutil.tests import HAS_ENVIRON
from psutil.tests import HAS_IONICE
from psutil.tests import HAS_MEMORY_MAPS
from psutil.tests import HAS_PROC_CPU_NUM
from psutil.tests import HAS_PROC_IO_COUNTERS
from psutil.tests import HAS_RLIMIT
from psutil.tests import HAS_THREADS
from psutil.tests import MACOS_11PLUS
from psutil.tests import PYPY
from psutil.tests import PYTHON_EXE
from psutil.tests import PYTHON_EXE_ENV
from psutil.tests import PsutilTestCase
from psutil.tests import ThreadTask
from psutil.tests import call_until
from psutil.tests import copyload_shared_lib
from psutil.tests import create_c_exe
from psutil.tests import create_py_exe
from psutil.tests import process_namespace
from psutil.tests import pytest
from psutil.tests import reap_children
from psutil.tests import retry_on_failure
from psutil.tests import sh
from psutil.tests import skip_on_access_denied
from psutil.tests import skip_on_not_implemented
from psutil.tests import wait_for_pid

# 025536.python.test_process.line67.comment ===================================================================
# 025537.python.test_process.line68.comment --- psutil.Process class tests
# 025538.python.test_process.line69.comment ===================================================================


class TestProcess(PsutilTestCase):
    """Tests for psutil.Process class."""

    def test_pid(self):
        p = psutil.Process()
        assert p.pid == os.getpid()
        with pytest.raises(AttributeError):
            p.pid = 33

    def test_kill(self):
        p = self.spawn_psproc()
        p.kill()
        code = p.wait()
        if WINDOWS:
            assert code == signal.SIGTERM
        else:
            assert code == -signal.SIGKILL
        self.assert_proc_gone(p)

    def test_terminate(self):
        p = self.spawn_psproc()
        p.terminate()
        code = p.wait()
        if WINDOWS:
            assert code == signal.SIGTERM
        else:
            assert code == -signal.SIGTERM
        self.assert_proc_gone(p)

    def test_send_signal(self):
        sig = signal.SIGKILL if POSIX else signal.SIGTERM
        p = self.spawn_psproc()
        p.send_signal(sig)
        code = p.wait()
        if WINDOWS:
            assert code == sig
        else:
            assert code == -sig
        self.assert_proc_gone(p)

    @pytest.mark.skipif(not POSIX, reason="not POSIX")
    def test_send_signal_mocked(self):
        sig = signal.SIGTERM
        p = self.spawn_psproc()
        with mock.patch('psutil.os.kill', side_effect=ProcessLookupError):
            with pytest.raises(psutil.NoSuchProcess):
                p.send_signal(sig)

        p = self.spawn_psproc()
        with mock.patch('psutil.os.kill', side_effect=PermissionError):
            with pytest.raises(psutil.AccessDenied):
                p.send_signal(sig)

    def test_wait_exited(self):
        # 025539.python.test_process.line126.comment Test waitpid() + WIFEXITED -> WEXITSTATUS.
        # 025540.python.test_process.line127.comment normal return, same as exit(0)
        cmd = [PYTHON_EXE, "-c", "pass"]
        p = self.spawn_psproc(cmd)
        code = p.wait()
        assert code == 0
        self.assert_proc_gone(p)
        # 025541.python.test_process.line133.comment exit(1), implicit in case of error
        cmd = [PYTHON_EXE, "-c", "1 / 0"]
        p = self.spawn_psproc(cmd, stderr=subprocess.PIPE)
        code = p.wait()
        assert code == 1
        self.assert_proc_gone(p)
        # 025542.python.test_process.line139.comment via sys.exit()
        cmd = [PYTHON_EXE, "-c", "import sys; sys.exit(5);"]
        p = self.spawn_psproc(cmd)
        code = p.wait()
        assert code == 5
        self.assert_proc_gone(p)
        # 025543.python.test_process.line145.comment via os._exit()
        cmd = [PYTHON_EXE, "-c", "import os; os._exit(5);"]
        p = self.spawn_psproc(cmd)
        code = p.wait()
        assert code == 5
        self.assert_proc_gone(p)

    @pytest.mark.skipif(NETBSD, reason="fails on NETBSD")
    def test_wait_stopped(self):
        p = self.spawn_psproc()
        if POSIX:
            # 025544.python.test_process.line156.comment Test waitpid() + WIFSTOPPED and WIFCONTINUED.
            # 025545.python.test_process.line157.comment Note: if a process is stopped it ignores SIGTERM.
            p.send_signal(signal.SIGSTOP)
            with pytest.raises(psutil.TimeoutExpired):
                p.wait(timeout=0.001)
            p.send_signal(signal.SIGCONT)
            with pytest.raises(psutil.TimeoutExpired):
                p.wait(timeout=0.001)
            p.send_signal(signal.SIGTERM)
            assert p.wait() == -signal.SIGTERM
            assert p.wait() == -signal.SIGTERM
        else:
            p.suspend()
            with pytest.raises(psutil.TimeoutExpired):
                p.wait(timeout=0.001)
            p.resume()
            with pytest.raises(psutil.TimeoutExpired):
                p.wait(timeout=0.001)
            p.terminate()
            assert p.wait() == signal.SIGTERM
            assert p.wait() == signal.SIGTERM

    def test_wait_non_children(self):
        # 025546.python.test_process.line179.comment Test wait() against a process which is not our direct
        # 025547.python.test_process.line180.comment child.
        child, grandchild = self.spawn_children_pair()
        with pytest.raises(psutil.TimeoutExpired):
            child.wait(0.01)
        with pytest.raises(psutil.TimeoutExpired):
            grandchild.wait(0.01)
        # 025548.python.test_process.line186.comment We also terminate the direct child otherwise the
        # 025549.python.test_process.line187.comment grandchild will hang until the parent is gone.
        child.terminate()
        grandchild.terminate()
        child_ret = child.wait()
        grandchild_ret = grandchild.wait()
        if POSIX:
            assert child_ret == -signal.SIGTERM
            # 025550.python.test_process.line194.comment For processes which are not our children we're supposed
            # 025551.python.test_process.line195.comment to get None.
            assert grandchild_ret is None
        else:
            assert child_ret == signal.SIGTERM
            assert child_ret == signal.SIGTERM

    def test_wait_timeout(self):
        p = self.spawn_psproc()
        p.name()
        with pytest.raises(psutil.TimeoutExpired):
            p.wait(0.01)
        with pytest.raises(psutil.TimeoutExpired):
            p.wait(0)
        with pytest.raises(ValueError):
            p.wait(-1)

    def test_wait_timeout_nonblocking(self):
        p = self.spawn_psproc()
        with pytest.raises(psutil.TimeoutExpired):
            p.wait(0)
        p.kill()
        stop_at = time.time() + GLOBAL_TIMEOUT
        while time.time() < stop_at:
            try:
                code = p.wait(0)
                break
            except psutil.TimeoutExpired:
                pass
        else:
            raise pytest.fail('timeout')
        if POSIX:
            assert code == -signal.SIGKILL
        else:
            assert code == signal.SIGTERM
        self.assert_proc_gone(p)

    def test_cpu_percent(self):
        p = psutil.Process()
        p.cpu_percent(interval=0.001)
        p.cpu_percent(interval=0.001)
        for _ in range(100):
            percent = p.cpu_percent(interval=None)
            assert isinstance(percent, float)
            assert percent >= 0.0
        with pytest.raises(ValueError):
            p.cpu_percent(interval=-1)

    def test_cpu_percent_numcpus_none(self):
        # 025552.python.test_process.line243.comment See: https://github.com/giampaolo/psutil/issues/1087
        with mock.patch('psutil.cpu_count', return_value=None) as m:
            psutil.Process().cpu_percent()
            assert m.called

    def test_cpu_times(self):
        times = psutil.Process().cpu_times()
        assert times.user >= 0.0, times
        assert times.system >= 0.0, times
        assert times.children_user >= 0.0, times
        assert times.children_system >= 0.0, times
        if LINUX:
            assert times.iowait >= 0.0, times
        # 025553.python.test_process.line256.comment make sure returned values can be pretty printed with strftime
        for name in times._fields:
            time.strftime("%H:%M:%S", time.localtime(getattr(times, name)))

    def test_cpu_times_2(self):
        def waste_cpu():
            stop_at = os.times().user + 0.2
            while os.times().user < stop_at:
                for x in range(100000):
                    x **= 2

        waste_cpu()
        a = psutil.Process().cpu_times()
        b = os.times()
        assert abs(a.user - b.user) < 0.1
        assert abs(a.system - b.system) < 0.1

    @pytest.mark.skipif(not HAS_PROC_CPU_NUM, reason="not supported")
    def test_cpu_num(self):
        p = psutil.Process()
        num = p.cpu_num()
        assert num >= 0
        if psutil.cpu_count() == 1:
            assert num == 0
        assert p.cpu_num() in range(psutil.cpu_count())

    def test_create_time(self):
        p = self.spawn_psproc()
        now = time.time()
        # 025554.python.test_process.line285.comment Fail if the difference with current time is > 2s.
        assert abs(p.create_time() - now) < 2
        # 025555.python.test_process.line287.comment make sure returned value can be pretty printed with strftime
        time.strftime("%Y %m %d %H:%M:%S", time.localtime(p.create_time()))

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_terminal(self):
        terminal = psutil.Process().terminal()
        if terminal is not None:
            try:
                tty = os.path.realpath(sh('tty'))
            except RuntimeError:
                # 025556.python.test_process.line297.comment Note: happens if pytest is run without the `-s` opt.
                raise pytest.skip("can't rely on `tty` CLI")
            else:
                assert terminal == tty

    @pytest.mark.skipif(not HAS_PROC_IO_COUNTERS, reason="not supported")
    @skip_on_not_implemented(only_if=LINUX)
    def test_io_counters(self):
        p = psutil.Process()
        # 025557.python.test_process.line306.comment test reads
        io1 = p.io_counters()
        with open(PYTHON_EXE, 'rb') as f:
            f.read()
        io2 = p.io_counters()
        if not BSD and not AIX:
            assert io2.read_count > io1.read_count
            assert io2.write_count == io1.write_count
            if LINUX:
                assert io2.read_chars > io1.read_chars
                assert io2.write_chars == io1.write_chars
        else:
            assert io2.read_bytes >= io1.read_bytes
            assert io2.write_bytes >= io1.write_bytes

        # 025558.python.test_process.line321.comment test writes
        io1 = p.io_counters()
        with open(self.get_testfn(), 'wb') as f:
            f.write(bytes("x" * 1000000, 'ascii'))
        io2 = p.io_counters()
        assert io2.write_count >= io1.write_count
        assert io2.write_bytes >= io1.write_bytes
        assert io2.read_count >= io1.read_count
        assert io2.read_bytes >= io1.read_bytes
        if LINUX:
            assert io2.write_chars > io1.write_chars
            assert io2.read_chars >= io1.read_chars

        # 025559.python.test_process.line334.comment sanity check
        for i in range(len(io2)):
            if BSD and i >= 2:
                # 025560.python.test_process.line337.comment On BSD read_bytes and write_bytes are always set to -1.
                continue
            assert io2[i] >= 0
            assert io2[i] >= 0

    @pytest.mark.skipif(not HAS_IONICE, reason="not supported")
    @pytest.mark.skipif(not LINUX, reason="linux only")
    def test_ionice_linux(self):
        def cleanup(init):
            ioclass, value = init
            if ioclass == psutil.IOPRIO_CLASS_NONE:
                value = 0
            p.ionice(ioclass, value)

        p = psutil.Process()
        if not CI_TESTING:
            assert p.ionice()[0] == psutil.IOPRIO_CLASS_NONE
        assert psutil.IOPRIO_CLASS_NONE == 0
        assert psutil.IOPRIO_CLASS_RT == 1  # high
        assert psutil.IOPRIO_CLASS_BE == 2  # normal
        assert psutil.IOPRIO_CLASS_IDLE == 3  # low
        init = p.ionice()
        self.addCleanup(cleanup, init)

        # 025564.python.test_process.line361.comment low
        p.ionice(psutil.IOPRIO_CLASS_IDLE)
        assert tuple(p.ionice()) == (psutil.IOPRIO_CLASS_IDLE, 0)
        with pytest.raises(ValueError):  # accepts no value
            p.ionice(psutil.IOPRIO_CLASS_IDLE, value=7)
        # 025566.python.test_process.line366.comment normal
        p.ionice(psutil.IOPRIO_CLASS_BE)
        assert tuple(p.ionice()) == (psutil.IOPRIO_CLASS_BE, 0)
        p.ionice(psutil.IOPRIO_CLASS_BE, value=7)
        assert tuple(p.ionice()) == (psutil.IOPRIO_CLASS_BE, 7)
        with pytest.raises(ValueError):
            p.ionice(psutil.IOPRIO_CLASS_BE, value=8)
        try:
            p.ionice(psutil.IOPRIO_CLASS_RT, value=7)
        except psutil.AccessDenied:
            pass
        # 025567.python.test_process.line377.comment errs
        with pytest.raises(ValueError, match="ioclass accepts no value"):
            p.ionice(psutil.IOPRIO_CLASS_NONE, 1)
        with pytest.raises(ValueError, match="ioclass accepts no value"):
            p.ionice(psutil.IOPRIO_CLASS_IDLE, 1)
        with pytest.raises(
            ValueError, match="'ioclass' argument must be specified"
        ):
            p.ionice(value=1)

    @pytest.mark.skipif(not HAS_IONICE, reason="not supported")
    @pytest.mark.skipif(
        not WINDOWS, reason="not supported on this win version"
    )
    def test_ionice_win(self):
        p = psutil.Process()
        if not CI_TESTING:
            assert p.ionice() == psutil.IOPRIO_NORMAL
        init = p.ionice()
        self.addCleanup(p.ionice, init)

        # 025568.python.test_process.line398.comment base
        p.ionice(psutil.IOPRIO_VERYLOW)
        assert p.ionice() == psutil.IOPRIO_VERYLOW
        p.ionice(psutil.IOPRIO_LOW)
        assert p.ionice() == psutil.IOPRIO_LOW
        try:
            p.ionice(psutil.IOPRIO_HIGH)
        except psutil.AccessDenied:
            pass
        else:
            assert p.ionice() == psutil.IOPRIO_HIGH
        # 025569.python.test_process.line409.comment errs
        with pytest.raises(
            TypeError, match="value argument not accepted on Windows"
        ):
            p.ionice(psutil.IOPRIO_NORMAL, value=1)
        with pytest.raises(ValueError, match="is not a valid priority"):
            p.ionice(psutil.IOPRIO_HIGH + 1)

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit_get(self):
        import resource

        p = psutil.Process(os.getpid())
        names = [x for x in dir(psutil) if x.startswith('RLIMIT')]
        assert names, names
        for name in names:
            value = getattr(psutil, name)
            assert value >= 0
            if name in dir(resource):
                assert value == getattr(resource, name)
                # 025570.python.test_process.line429.comment XXX - On PyPy RLIMIT_INFINITY returned by
                # 025571.python.test_process.line430.comment resource.getrlimit() is reported as a very big long
                # 025572.python.test_process.line431.comment number instead of -1. It looks like a bug with PyPy.
                if PYPY:
                    continue
                assert p.rlimit(value) == resource.getrlimit(value)
            else:
                ret = p.rlimit(value)
                assert len(ret) == 2
                assert ret[0] >= -1
                assert ret[1] >= -1

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit_set(self):
        p = self.spawn_psproc()
        p.rlimit(psutil.RLIMIT_NOFILE, (5, 5))
        assert p.rlimit(psutil.RLIMIT_NOFILE) == (5, 5)
        # 025573.python.test_process.line446.comment If pid is 0 prlimit() applies to the calling process and
        # 025574.python.test_process.line447.comment we don't want that.
        if LINUX:
            with pytest.raises(ValueError, match="can't use prlimit"):
                psutil._psplatform.Process(0).rlimit(0)
        with pytest.raises(ValueError):
            p.rlimit(psutil.RLIMIT_NOFILE, (5, 5, 5))

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit(self):
        p = psutil.Process()
        testfn = self.get_testfn()
        soft, hard = p.rlimit(psutil.RLIMIT_FSIZE)
        try:
            p.rlimit(psutil.RLIMIT_FSIZE, (1024, hard))
            with open(testfn, "wb") as f:
                f.write(b"X" * 1024)
            # 025575.python.test_process.line463.comment write() or flush() doesn't always cause the exception
            # 025576.python.test_process.line464.comment but close() will.
            with pytest.raises(OSError) as exc:
                with open(testfn, "wb") as f:
                    f.write(b"X" * 1025)
            assert exc.value.errno == errno.EFBIG
        finally:
            p.rlimit(psutil.RLIMIT_FSIZE, (soft, hard))
            assert p.rlimit(psutil.RLIMIT_FSIZE) == (soft, hard)

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit_infinity(self):
        # 025577.python.test_process.line475.comment First set a limit, then re-set it by specifying INFINITY
        # 025578.python.test_process.line476.comment and assume we overridden the previous limit.
        p = psutil.Process()
        soft, hard = p.rlimit(psutil.RLIMIT_FSIZE)
        try:
            p.rlimit(psutil.RLIMIT_FSIZE, (1024, hard))
            p.rlimit(psutil.RLIMIT_FSIZE, (psutil.RLIM_INFINITY, hard))
            with open(self.get_testfn(), "wb") as f:
                f.write(b"X" * 2048)
        finally:
            p.rlimit(psutil.RLIMIT_FSIZE, (soft, hard))
            assert p.rlimit(psutil.RLIMIT_FSIZE) == (soft, hard)

    @pytest.mark.skipif(not HAS_RLIMIT, reason="not supported")
    def test_rlimit_infinity_value(self):
        # 025579.python.test_process.line490.comment RLIMIT_FSIZE should be RLIM_INFINITY, which will be a really
        # 025580.python.test_process.line491.comment big number on a platform with large file support.  On these
        # 025581.python.test_process.line492.comment platforms we need to test that the get/setrlimit functions
        # 025582.python.test_process.line493.comment properly convert the number to a C long long and that the
        # 025583.python.test_process.line494.comment conversion doesn't raise an error.
        p = psutil.Process()
        soft, hard = p.rlimit(psutil.RLIMIT_FSIZE)
        assert hard == psutil.RLIM_INFINITY
        p.rlimit(psutil.RLIMIT_FSIZE, (soft, hard))

    @pytest.mark.xdist_group(name="serial")
    def test_num_threads(self):
        # 025584.python.test_process.line502.comment on certain platforms such as Linux we might test for exact
        # 025585.python.test_process.line503.comment thread number, since we always have with 1 thread per process,
        # 025586.python.test_process.line504.comment but this does not apply across all platforms (MACOS, Windows)
        p = psutil.Process()
        if OPENBSD:
            try:
                step1 = p.num_threads()
            except psutil.AccessDenied:
                raise pytest.skip("on OpenBSD this requires root access")
        else:
            step1 = p.num_threads()

        with ThreadTask():
            step2 = p.num_threads()
            assert step2 == step1 + 1

    @pytest.mark.skipif(not WINDOWS, reason="WINDOWS only")
    def test_num_handles(self):
        # 025587.python.test_process.line520.comment a better test is done later into test/_windows.py
        p = psutil.Process()
        assert p.num_handles() > 0

    @pytest.mark.skipif(not HAS_THREADS, reason="not supported")
    def test_threads(self):
        p = psutil.Process()
        if OPENBSD:
            try:
                step1 = p.threads()
            except psutil.AccessDenied:
                raise pytest.skip("on OpenBSD this requires root access")
        else:
            step1 = p.threads()

        with ThreadTask():
            step2 = p.threads()
            assert len(step2) == len(step1) + 1
            athread = step2[0]
            # 025588.python.test_process.line539.comment test named tuple
            assert athread.id == athread[0]
            assert athread.user_time == athread[1]
            assert athread.system_time == athread[2]

    @retry_on_failure()
    @skip_on_access_denied(only_if=MACOS)
    @pytest.mark.skipif(not HAS_THREADS, reason="not supported")
    def test_threads_2(self):
        p = self.spawn_psproc()
        if OPENBSD:
            try:
                p.threads()
            except psutil.AccessDenied:
                raise pytest.skip("on OpenBSD this requires root access")
        assert (
            abs(p.cpu_times().user - sum(x.user_time for x in p.threads()))
            < 0.1
        )
        assert (
            abs(p.cpu_times().system - sum(x.system_time for x in p.threads()))
            < 0.1
        )

    @retry_on_failure()
    def test_memory_info(self):
        p = psutil.Process()

        # 025589.python.test_process.line567.comment step 1 - get a base value to compare our results
        rss1, vms1 = p.memory_info()[:2]
        percent1 = p.memory_percent()
        assert rss1 > 0
        assert vms1 > 0

        # 025590.python.test_process.line573.comment step 2 - allocate some memory
        memarr = [None] * 1500000

        rss2, vms2 = p.memory_info()[:2]
        percent2 = p.memory_percent()

        # 025591.python.test_process.line579.comment step 3 - make sure that the memory usage bumped up
        assert rss2 > rss1
        assert vms2 >= vms1  # vms might be equal
        assert percent2 > percent1
        del memarr

        if WINDOWS:
            mem = p.memory_info()
            assert mem.rss == mem.wset
            assert mem.vms == mem.pagefile

        mem = p.memory_info()
        for name in mem._fields:
            assert getattr(mem, name) >= 0

    def test_memory_full_info(self):
        p = psutil.Process()
        total = psutil.virtual_memory().total
        mem = p.memory_full_info()
        for name in mem._fields:
            value = getattr(mem, name)
            assert value >= 0
            if (name == "vms" and OSX) or LINUX:
                continue
            assert value <= total
        if LINUX or WINDOWS or MACOS:
            assert mem.uss >= 0
        if LINUX:
            assert mem.pss >= 0
            assert mem.swap >= 0

    @pytest.mark.skipif(not HAS_MEMORY_MAPS, reason="not supported")
    def test_memory_maps(self):
        p = psutil.Process()
        maps = p.memory_maps()
        assert len(maps) == len(set(maps))
        ext_maps = p.memory_maps(grouped=False)

        for nt in maps:
            if nt.path.startswith('['):
                continue
            if BSD and nt.path == "pvclock":
                continue
            assert os.path.isabs(nt.path), nt.path

            if POSIX:
                try:
                    assert os.path.exists(nt.path) or os.path.islink(
                        nt.path
                    ), nt.path
                except AssertionError:
                    if not LINUX:
                        raise
                    # 025593.python.test_process.line632.comment https://github.com/giampaolo/psutil/issues/759
                    with open_text('/proc/self/smaps') as f:
                        data = f.read()
                    if f"{nt.path} (deleted)" not in data:
                        raise
            elif '64' not in os.path.basename(nt.path):
                # 025594.python.test_process.line638.comment XXX - On Windows we have this strange behavior with
                # 025595.python.test_process.line639.comment 64 bit dlls: they are visible via explorer but cannot
                # 025596.python.test_process.line640.comment be accessed via os.stat() (wtf?).
                try:
                    st = os.stat(nt.path)
                except FileNotFoundError:
                    pass
                else:
                    assert stat.S_ISREG(st.st_mode), nt.path

        for nt in ext_maps:
            for fname in nt._fields:
                value = getattr(nt, fname)
                if fname == 'path':
                    continue
                if fname in {'addr', 'perms'}:
                    assert value, value
                else:
                    assert isinstance(value, int)
                    assert value >= 0, value

    @pytest.mark.skipif(not HAS_MEMORY_MAPS, reason="not supported")
    def test_memory_maps_lists_lib(self):
        # 025597.python.test_process.line661.comment Make sure a newly loaded shared lib is listed.
        p = psutil.Process()
        with copyload_shared_lib() as path:

            def normpath(p):
                return os.path.realpath(os.path.normcase(p))

            libpaths = [normpath(x.path) for x in p.memory_maps()]
            assert normpath(path) in libpaths

    def test_memory_percent(self):
        p = psutil.Process()
        p.memory_percent()
        with pytest.raises(ValueError):
            p.memory_percent(memtype="?!?")
        if LINUX or MACOS or WINDOWS:
            p.memory_percent(memtype='uss')

    def test_is_running(self):
        p = self.spawn_psproc()
        assert p.is_running()
        assert p.is_running()
        p.kill()
        p.wait()
        assert not p.is_running()
        assert not p.is_running()

    def test_exe(self):
        p = self.spawn_psproc()
        exe = p.exe()
        try:
            assert exe == PYTHON_EXE
        except AssertionError:
            if WINDOWS and len(exe) == len(PYTHON_EXE):
                # 025598.python.test_process.line695.comment on Windows we don't care about case sensitivity
                normcase = os.path.normcase
                assert normcase(exe) == normcase(PYTHON_EXE)
            else:
                # 025599.python.test_process.line699.comment certain platforms such as BSD are more accurate returning:
                # 025600.python.test_process.line700.comment "/usr/local/bin/python3.7"
                # 025601.python.test_process.line701.comment ...instead of:
                # 025602.python.test_process.line702.comment "/usr/local/bin/python"
                # 025603.python.test_process.line703.comment We do not want to consider this difference in accuracy
                # 025604.python.test_process.line704.comment an error.
                ver = f"{sys.version_info[0]}.{sys.version_info[1]}"
                try:
                    assert exe.replace(ver, '') == PYTHON_EXE.replace(ver, '')
                except AssertionError:
                    # 025605.python.test_process.line709.comment Typically MACOS. Really not sure what to do here.
                    pass

        out = sh([exe, "-c", "import os; print('hey')"])
        assert out == 'hey'

    def test_cmdline(self):
        cmdline = [
            PYTHON_EXE,
            "-c",
            "import time; [time.sleep(0.1) for x in range(100)]",
        ]
        p = self.spawn_psproc(cmdline)

        if NETBSD and p.cmdline() == []:
            # 025606.python.test_process.line724.comment https://github.com/giampaolo/psutil/issues/2250
            raise pytest.skip("OPENBSD: returned EBUSY")

        # 025607.python.test_process.line727.comment XXX - most of the times the underlying sysctl() call on Net
        # 025608.python.test_process.line728.comment and Open BSD returns a truncated string.
        # 025609.python.test_process.line729.comment Also /proc/pid/cmdline behaves the same so it looks
        # 025610.python.test_process.line730.comment like this is a kernel bug.
        # 025611.python.test_process.line731.comment XXX - AIX truncates long arguments in /proc/pid/cmdline
        if NETBSD or OPENBSD or AIX:
            assert p.cmdline()[0] == PYTHON_EXE
        else:
            if MACOS and CI_TESTING:
                pyexe = p.cmdline()[0]
                if pyexe != PYTHON_EXE:
                    assert ' '.join(p.cmdline()[1:]) == ' '.join(cmdline[1:])
                    return
            assert ' '.join(p.cmdline()) == ' '.join(cmdline)

    def test_long_cmdline(self):
        cmdline = [PYTHON_EXE]
        cmdline.extend(["-v"] * 50)
        cmdline.extend(
            ["-c", "import time; [time.sleep(0.1) for x in range(100)]"]
        )
        p = self.spawn_psproc(cmdline)

        # 025612.python.test_process.line750.comment XXX - flaky test: exclude the python exe which, for some
        # 025613.python.test_process.line751.comment reason, and only sometimes, on OSX appears different.
        cmdline = cmdline[1:]

        if OPENBSD:
            # 025614.python.test_process.line755.comment XXX: for some reason the test process may turn into a
            # 025615.python.test_process.line756.comment zombie (don't know why).
            try:
                assert p.cmdline()[1:] == cmdline
            except psutil.ZombieProcess:
                raise pytest.skip("OPENBSD: process turned into zombie")
        else:
            ret = p.cmdline()[1:]
            if NETBSD and ret == []:
                # 025616.python.test_process.line764.comment https://github.com/giampaolo/psutil/issues/2250
                raise pytest.skip("OPENBSD: returned EBUSY")
            assert ret == cmdline

    def test_name(self):
        p = self.spawn_psproc()
        name = p.name().lower()
        pyexe = os.path.basename(os.path.realpath(sys.executable)).lower()
        assert pyexe.startswith(name), (pyexe, name)

    @retry_on_failure()
    def test_long_name(self):
        pyexe = create_py_exe(self.get_testfn(suffix=string.digits * 2))
        cmdline = [
            pyexe,
            "-c",
            "import time; [time.sleep(0.1) for x in range(100)]",
        ]
        p = self.spawn_psproc(cmdline)
        if OPENBSD:
            # 025617.python.test_process.line784.comment XXX: for some reason the test process may turn into a
            # 025618.python.test_process.line785.comment zombie (don't know why). Because the name() is long, all
            # 025619.python.test_process.line786.comment UNIX kernels truncate it to 15 chars, so internally psutil
            # 025620.python.test_process.line787.comment tries to guess the full name() from the cmdline(). But the
            # 025621.python.test_process.line788.comment cmdline() of a zombie on OpenBSD fails (internally), so we
            # 025622.python.test_process.line789.comment just compare the first 15 chars. Full explanation:
            # 025623.python.test_process.line790.comment https://github.com/giampaolo/psutil/issues/2239
            try:
                assert p.name() == os.path.basename(pyexe)
            except AssertionError:
                if p.status() == psutil.STATUS_ZOMBIE:
                    assert os.path.basename(pyexe).startswith(p.name())
                else:
                    raise
        else:
            assert p.name() == os.path.basename(pyexe)

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_uids(self):
        p = psutil.Process()
        real, effective, _saved = p.uids()
        # 025624.python.test_process.line805.comment os.getuid() refers to "real" uid
        assert real == os.getuid()
        # 025625.python.test_process.line807.comment os.geteuid() refers to "effective" uid
        assert effective == os.geteuid()
        # 025626.python.test_process.line809.comment No such thing as os.getsuid() ("saved" uid), but we have
        # 025627.python.test_process.line810.comment os.getresuid() which returns all of them.
        if hasattr(os, "getresuid"):
            assert os.getresuid() == p.uids()

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_gids(self):
        p = psutil.Process()
        real, effective, _saved = p.gids()
        # 025628.python.test_process.line818.comment os.getuid() refers to "real" uid
        assert real == os.getgid()
        # 025629.python.test_process.line820.comment os.geteuid() refers to "effective" uid
        assert effective == os.getegid()
        # 025630.python.test_process.line822.comment No such thing as os.getsgid() ("saved" gid), but we have
        # 025631.python.test_process.line823.comment os.getresgid() which returns all of them.
        if hasattr(os, "getresuid"):
            assert os.getresgid() == p.gids()

    def test_nice(self):
        def cleanup(init):
            try:
                p.nice(init)
            except psutil.AccessDenied:
                pass

        p = psutil.Process()
        with pytest.raises(TypeError):
            p.nice("str")
        init = p.nice()
        self.addCleanup(cleanup, init)

        if WINDOWS:
            highest_prio = None
            for prio in [
                psutil.IDLE_PRIORITY_CLASS,
                psutil.BELOW_NORMAL_PRIORITY_CLASS,
                psutil.NORMAL_PRIORITY_CLASS,
                psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                psutil.HIGH_PRIORITY_CLASS,
                psutil.REALTIME_PRIORITY_CLASS,
            ]:
                with self.subTest(prio=prio):
                    try:
                        p.nice(prio)
                    except psutil.AccessDenied:
                        pass
                    else:
                        new_prio = p.nice()
                        # 025632.python.test_process.line857.comment The OS may limit our maximum priority,
                        # 025633.python.test_process.line858.comment even if the function succeeds. For higher
                        # 025634.python.test_process.line859.comment priorities, we match either the expected
                        # 025635.python.test_process.line860.comment value or the highest so far.
                        if prio in {
                            psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                            psutil.HIGH_PRIORITY_CLASS,
                            psutil.REALTIME_PRIORITY_CLASS,
                        }:
                            if new_prio == prio or highest_prio is None:
                                highest_prio = prio
                                assert new_prio == highest_prio
                        else:
                            assert new_prio == prio
        else:
            try:
                if hasattr(os, "getpriority"):
                    assert (
                        os.getpriority(os.PRIO_PROCESS, os.getpid())
                        == p.nice()
                    )
                p.nice(1)
                assert p.nice() == 1
                if hasattr(os, "getpriority"):
                    assert (
                        os.getpriority(os.PRIO_PROCESS, os.getpid())
                        == p.nice()
                    )
                # 025636.python.test_process.line885.comment XXX - going back to previous nice value raises
                # 025637.python.test_process.line886.comment AccessDenied on MACOS
                if not MACOS:
                    p.nice(0)
                    assert p.nice() == 0
            except psutil.AccessDenied:
                pass

    def test_status(self):
        p = psutil.Process()
        assert p.status() == psutil.STATUS_RUNNING

    def test_username(self):
        p = self.spawn_psproc()
        username = p.username()
        if WINDOWS:
            domain, username = username.split('\\')
            getpass_user = getpass.getuser()
            if getpass_user.endswith('$'):
                # 025638.python.test_process.line904.comment When running as a service account (most likely to be
                # 025639.python.test_process.line905.comment NetworkService), these user name calculations don't produce
                # 025640.python.test_process.line906.comment the same result, causing the test to fail.
                raise pytest.skip('running as service account')
            assert username == getpass_user
            if 'USERDOMAIN' in os.environ:
                assert domain == os.environ['USERDOMAIN']
        else:
            assert username == getpass.getuser()

    def test_cwd(self):
        p = self.spawn_psproc()
        assert p.cwd() == os.getcwd()

    def test_cwd_2(self):
        cmd = [
            PYTHON_EXE,
            "-c",
            (
                "import os, time; os.chdir('..'); [time.sleep(0.1) for x in"
                " range(100)]"
            ),
        ]
        p = self.spawn_psproc(cmd)
        call_until(lambda: p.cwd() == os.path.dirname(os.getcwd()))

    @pytest.mark.skipif(not HAS_CPU_AFFINITY, reason="not supported")
    def test_cpu_affinity(self):
        p = psutil.Process()
        initial = p.cpu_affinity()
        assert initial, initial
        self.addCleanup(p.cpu_affinity, initial)

        if hasattr(os, "sched_getaffinity"):
            assert initial == list(os.sched_getaffinity(p.pid))
        assert len(initial) == len(set(initial))

        all_cpus = list(range(len(psutil.cpu_percent(percpu=True))))
        for n in all_cpus:
            p.cpu_affinity([n])
            assert p.cpu_affinity() == [n]
            if hasattr(os, "sched_getaffinity"):
                assert p.cpu_affinity() == list(os.sched_getaffinity(p.pid))
            # 025641.python.test_process.line947.comment also test num_cpu()
            if hasattr(p, "num_cpu"):
                assert p.cpu_affinity()[0] == p.num_cpu()

        # 025642.python.test_process.line951.comment [] is an alias for "all eligible CPUs"; on Linux this may
        # 025643.python.test_process.line952.comment not be equal to all available CPUs, see:
        # 025644.python.test_process.line953.comment https://github.com/giampaolo/psutil/issues/956
        p.cpu_affinity([])
        if LINUX:
            assert p.cpu_affinity() == p._proc._get_eligible_cpus()
        else:
            assert p.cpu_affinity() == all_cpus
        if hasattr(os, "sched_getaffinity"):
            assert p.cpu_affinity() == list(os.sched_getaffinity(p.pid))

        with pytest.raises(TypeError):
            p.cpu_affinity(1)
        p.cpu_affinity(initial)
        # 025645.python.test_process.line965.comment it should work with all iterables, not only lists
        p.cpu_affinity(set(all_cpus))
        p.cpu_affinity(tuple(all_cpus))

    @pytest.mark.skipif(not HAS_CPU_AFFINITY, reason="not supported")
    def test_cpu_affinity_errs(self):
        p = self.spawn_psproc()
        invalid_cpu = [len(psutil.cpu_times(percpu=True)) + 10]
        with pytest.raises(ValueError):
            p.cpu_affinity(invalid_cpu)
        with pytest.raises(ValueError):
            p.cpu_affinity(range(10000, 11000))
        with pytest.raises((TypeError, ValueError)):
            p.cpu_affinity([0, "1"])
        with pytest.raises(ValueError):
            p.cpu_affinity([0, -1])

    @pytest.mark.skipif(not HAS_CPU_AFFINITY, reason="not supported")
    def test_cpu_affinity_all_combinations(self):
        p = psutil.Process()
        initial = p.cpu_affinity()
        assert initial, initial
        self.addCleanup(p.cpu_affinity, initial)

        # 025646.python.test_process.line989.comment All possible CPU set combinations.
        if len(initial) > 12:
            initial = initial[:12]  # ...otherwise it will take forever
        combos = []
        for i in range(len(initial) + 1):
            combos.extend(
                list(subset)
                for subset in itertools.combinations(initial, i)
                if subset
            )

        for combo in combos:
            p.cpu_affinity(combo)
            assert sorted(p.cpu_affinity()) == sorted(combo)

    # 025648.python.test_process.line1004.comment TODO: #595
    @pytest.mark.skipif(BSD, reason="broken on BSD")
    def test_open_files(self):
        p = psutil.Process()
        testfn = self.get_testfn()
        files = p.open_files()
        assert testfn not in files
        with open(testfn, 'wb') as f:
            f.write(b'x' * 1024)
            f.flush()
            # 025649.python.test_process.line1014.comment give the kernel some time to see the new file
            call_until(lambda: len(p.open_files()) != len(files))
            files = p.open_files()
            filenames = [os.path.normcase(x.path) for x in files]
            assert os.path.normcase(testfn) in filenames
            if LINUX:
                for file in files:
                    if file.path == testfn:
                        assert file.position == 1024
        for file in files:
            assert os.path.isfile(file.path), file

        # 025650.python.test_process.line1026.comment another process
        cmdline = (
            f"import time; f = open(r'{testfn}', 'r'); [time.sleep(0.1) for x"
            " in range(100)];"
        )
        p = self.spawn_psproc([PYTHON_EXE, "-c", cmdline])

        for x in range(100):
            filenames = [os.path.normcase(x.path) for x in p.open_files()]
            if testfn in filenames:
                break
            time.sleep(0.01)
        else:
            assert os.path.normcase(testfn) in filenames
        for file in filenames:
            assert os.path.isfile(file), file

    # 025651.python.test_process.line1043.comment TODO: #595
    @pytest.mark.skipif(BSD, reason="broken on BSD")
    def test_open_files_2(self):
        # 025652.python.test_process.line1046.comment test fd and path fields
        p = psutil.Process()
        normcase = os.path.normcase
        testfn = self.get_testfn()
        with open(testfn, 'w') as fileobj:
            for file in p.open_files():
                if (
                    normcase(file.path) == normcase(fileobj.name)
                    or file.fd == fileobj.fileno()
                ):
                    break
            else:
                raise pytest.fail(f"no file found; files={p.open_files()!r}")
            assert normcase(file.path) == normcase(fileobj.name)
            if WINDOWS:
                assert file.fd == -1
            else:
                assert file.fd == fileobj.fileno()
            # 025653.python.test_process.line1064.comment test positions
            ntuple = p.open_files()[0]
            assert ntuple[0] == ntuple.path
            assert ntuple[1] == ntuple.fd
            # 025654.python.test_process.line1068.comment test file is gone
            assert fileobj.name not in p.open_files()

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    @pytest.mark.xdist_group(name="serial")
    def test_num_fds(self):
        p = psutil.Process()
        testfn = self.get_testfn()
        start = p.num_fds()
        with open(testfn, 'w'):
            assert p.num_fds() == start + 1
            with socket.socket():
                assert p.num_fds() == start + 2
        assert p.num_fds() == start

    @skip_on_not_implemented(only_if=LINUX)
    @pytest.mark.skipif(
        OPENBSD or NETBSD, reason="not reliable on OPENBSD & NETBSD"
    )
    def test_num_ctx_switches(self):
        p = psutil.Process()
        before = sum(p.num_ctx_switches())
        for _ in range(2):
            time.sleep(0.05)  # this shall ensure a context switch happens
            after = sum(p.num_ctx_switches())
            if after > before:
                return
        raise pytest.fail("num ctx switches still the same after 2 iterations")

    def test_ppid(self):
        p = psutil.Process()
        if hasattr(os, 'getppid'):
            assert p.ppid() == os.getppid()
        p = self.spawn_psproc()
        assert p.ppid() == os.getpid()

    def test_parent(self):
        p = self.spawn_psproc()
        assert p.parent().pid == os.getpid()

        lowest_pid = psutil.pids()[0]
        assert psutil.Process(lowest_pid).parent() is None

    def test_parent_mocked_ctime(self):
        # 025656.python.test_process.line1112.comment Make sure we get a fresh copy of the ctime before processing
        # 025657.python.test_process.line1113.comment parent().We make the assumption that the parent pid MUST have
        # 025658.python.test_process.line1114.comment a creation time < than the child. If system clock is updated
        # 025659.python.test_process.line1115.comment this assumption was broken.
        # 025660.python.test_process.line1116.comment https://github.com/giampaolo/psutil/issues/2542
        p = self.spawn_psproc()
        p.create_time()  # trigger cache
        assert p._create_time
        p._create_time = 1
        assert p.parent().pid == os.getpid()

    def test_parent_multi(self):
        parent = psutil.Process()
        child, grandchild = self.spawn_children_pair()
        assert grandchild.parent() == child
        assert child.parent() == parent

    @retry_on_failure()
    def test_parents(self):
        parent = psutil.Process()
        assert parent.parents()
        child, grandchild = self.spawn_children_pair()
        assert child.parents()[0] == parent
        assert grandchild.parents()[0] == child
        assert grandchild.parents()[1] == parent

    def test_children(self):
        parent = psutil.Process()
        assert not parent.children()
        assert not parent.children(recursive=True)
        # 025662.python.test_process.line1142.comment On Windows we set the flag to 0 in order to cancel out the
        # 025663.python.test_process.line1143.comment CREATE_NO_WINDOW flag (enabled by default) which creates
        # 025664.python.test_process.line1144.comment an extra "conhost.exe" child.
        child = self.spawn_psproc(creationflags=0)
        children1 = parent.children()
        children2 = parent.children(recursive=True)
        for children in (children1, children2):
            assert len(children) == 1
            assert children[0].pid == child.pid
            assert children[0].ppid() == parent.pid

    def test_children_mocked_ctime(self):
        # 025665.python.test_process.line1154.comment Make sure we get a fresh copy of the ctime before processing
        # 025666.python.test_process.line1155.comment children(). We make the assumption that process children MUST
        # 025667.python.test_process.line1156.comment have a creation time > than the parent. If system clock is
        # 025668.python.test_process.line1157.comment updated this assumption was broken.
        # 025669.python.test_process.line1158.comment https://github.com/giampaolo/psutil/issues/2542
        parent = psutil.Process()
        parent.create_time()  # trigger cache
        assert parent._create_time
        parent._create_time += 100000

        assert not parent.children()
        assert not parent.children(recursive=True)
        # 025671.python.test_process.line1166.comment On Windows we set the flag to 0 in order to cancel out the
        # 025672.python.test_process.line1167.comment CREATE_NO_WINDOW flag (enabled by default) which creates
        # 025673.python.test_process.line1168.comment an extra "conhost.exe" child.
        child = self.spawn_psproc(creationflags=0)
        children1 = parent.children()
        children2 = parent.children(recursive=True)
        for children in (children1, children2):
            assert len(children) == 1
            assert children[0].pid == child.pid
            assert children[0].ppid() == parent.pid

    def test_children_recursive(self):
        # 025674.python.test_process.line1178.comment Test children() against two sub processes, p1 and p2, where
        # 025675.python.test_process.line1179.comment p1 (our child) spawned p2 (our grandchild).
        parent = psutil.Process()
        child, grandchild = self.spawn_children_pair()
        assert parent.children() == [child]
        assert parent.children(recursive=True) == [child, grandchild]
        # 025676.python.test_process.line1184.comment If the intermediate process is gone there's no way for
        # 025677.python.test_process.line1185.comment children() to recursively find it.
        child.terminate()
        child.wait()
        assert not parent.children(recursive=True)

    def test_children_duplicates(self):
        # 025678.python.test_process.line1191.comment find the process which has the highest number of children
        table = collections.defaultdict(int)
        for p in psutil.process_iter():
            try:
                table[p.ppid()] += 1
            except psutil.Error:
                pass
        # 025679.python.test_process.line1198.comment this is the one, now let's make sure there are no duplicates
        pid = max(table.items(), key=lambda x: x[1])[0]
        if LINUX and pid == 0:
            raise pytest.skip("PID 0")
        p = psutil.Process(pid)
        try:
            c = p.children(recursive=True)
        except psutil.AccessDenied:  # windows
            pass
        else:
            assert len(c) == len(set(c))

    def test_parents_and_children(self):
        parent = psutil.Process()
        child, grandchild = self.spawn_children_pair()
        # 025681.python.test_process.line1213.comment forward
        children = parent.children(recursive=True)
        assert len(children) == 2
        assert children[0] == child
        assert children[1] == grandchild
        # 025682.python.test_process.line1218.comment backward
        parents = grandchild.parents()
        assert parents[0] == child
        assert parents[1] == parent

    def test_suspend_resume(self):
        p = self.spawn_psproc()
        p.suspend()
        for _ in range(100):
            if p.status() == psutil.STATUS_STOPPED:
                break
            time.sleep(0.01)
        p.resume()
        assert p.status() != psutil.STATUS_STOPPED

    def test_invalid_pid(self):
        with pytest.raises(TypeError):
            psutil.Process("1")
        with pytest.raises(ValueError):
            psutil.Process(-1)

    def test_as_dict(self):
        p = psutil.Process()
        d = p.as_dict(attrs=['exe', 'name'])
        assert sorted(d.keys()) == ['exe', 'name']

        p = psutil.Process(min(psutil.pids()))
        d = p.as_dict(attrs=['net_connections'], ad_value='foo')
        if not isinstance(d['net_connections'], list):
            assert d['net_connections'] == 'foo'

        # 025683.python.test_process.line1249.comment Test ad_value is set on AccessDenied.
        with mock.patch(
            'psutil.Process.nice', create=True, side_effect=psutil.AccessDenied
        ):
            assert p.as_dict(attrs=["nice"], ad_value=1) == {"nice": 1}

        # 025684.python.test_process.line1255.comment Test that NoSuchProcess bubbles up.
        with mock.patch(
            'psutil.Process.nice',
            create=True,
            side_effect=psutil.NoSuchProcess(p.pid, "name"),
        ):
            with pytest.raises(psutil.NoSuchProcess):
                p.as_dict(attrs=["nice"])

        # 025685.python.test_process.line1264.comment Test that ZombieProcess is swallowed.
        with mock.patch(
            'psutil.Process.nice',
            create=True,
            side_effect=psutil.ZombieProcess(p.pid, "name"),
        ):
            assert p.as_dict(attrs=["nice"], ad_value="foo") == {"nice": "foo"}

        # 025686.python.test_process.line1272.comment By default APIs raising NotImplementedError are
        # 025687.python.test_process.line1273.comment supposed to be skipped.
        with mock.patch(
            'psutil.Process.nice', create=True, side_effect=NotImplementedError
        ):
            d = p.as_dict()
            assert 'nice' not in list(d.keys())
            # 025688.python.test_process.line1279.comment ...unless the user explicitly asked for some attr.
            with pytest.raises(NotImplementedError):
                p.as_dict(attrs=["nice"])

        # 025689.python.test_process.line1283.comment errors
        with pytest.raises(TypeError):
            p.as_dict('name')
        with pytest.raises(ValueError):
            p.as_dict(['foo'])
        with pytest.raises(ValueError):
            p.as_dict(['foo', 'bar'])

    def test_oneshot(self):
        p = psutil.Process()
        with mock.patch("psutil._psplatform.Process.cpu_times") as m:
            with p.oneshot():
                p.cpu_times()
                p.cpu_times()
            assert m.call_count == 1

        with mock.patch("psutil._psplatform.Process.cpu_times") as m:
            p.cpu_times()
            p.cpu_times()
        assert m.call_count == 2

    def test_oneshot_twice(self):
        # 025690.python.test_process.line1305.comment Test the case where the ctx manager is __enter__ed twice.
        # 025691.python.test_process.line1306.comment The second __enter__ is supposed to resut in a NOOP.
        p = psutil.Process()
        with mock.patch("psutil._psplatform.Process.cpu_times") as m1:
            with mock.patch("psutil._psplatform.Process.oneshot_enter") as m2:
                with p.oneshot():
                    p.cpu_times()
                    p.cpu_times()
                    with p.oneshot():
                        p.cpu_times()
                        p.cpu_times()
                assert m1.call_count == 1
                assert m2.call_count == 1

        with mock.patch("psutil._psplatform.Process.cpu_times") as m:
            p.cpu_times()
            p.cpu_times()
        assert m.call_count == 2

    def test_oneshot_cache(self):
        # 025692.python.test_process.line1325.comment Make sure oneshot() cache is nonglobal. Instead it's
        # 025693.python.test_process.line1326.comment supposed to be bound to the Process instance, see:
        # 025694.python.test_process.line1327.comment https://github.com/giampaolo/psutil/issues/1373
        p1, p2 = self.spawn_children_pair()
        p1_ppid = p1.ppid()
        p2_ppid = p2.ppid()
        assert p1_ppid != p2_ppid
        with p1.oneshot():
            assert p1.ppid() == p1_ppid
            assert p2.ppid() == p2_ppid
        with p2.oneshot():
            assert p1.ppid() == p1_ppid
            assert p2.ppid() == p2_ppid

    def test_halfway_terminated_process(self):
        # 025695.python.test_process.line1340.comment Test that NoSuchProcess exception gets raised in case the
        # 025696.python.test_process.line1341.comment process dies after we create the Process object.
        # 025697.python.test_process.line1342.comment Example:
        # 025698.python.test_process.line1343.comment >>> proc = Process(1234)
        # 025699.python.test_process.line1344.comment >>> time.sleep(2)  # time-consuming task, process dies in meantime
        # 025700.python.test_process.line1345.comment >>> proc.name()
        # 025701.python.test_process.line1346.comment Refers to Issue #15
        def assert_raises_nsp(fun, fun_name):
            try:
                ret = fun()
            except psutil.ZombieProcess:  # differentiate from NSP
                raise
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                if OPENBSD and fun_name in {'threads', 'num_threads'}:
                    return
                raise
            else:
                # 025703.python.test_process.line1359.comment NtQuerySystemInformation succeeds even if process is gone.
                if WINDOWS and fun_name in {'exe', 'name'}:
                    return
                raise pytest.fail(
                    f"{fun!r} didn't raise NSP and returned {ret!r} instead"
                )

        p = self.spawn_psproc()
        p.terminate()
        p.wait()
        if WINDOWS:  # XXX
            call_until(lambda: p.pid not in psutil.pids())
        self.assert_proc_gone(p)

        ns = process_namespace(p)
        for fun, name in ns.iter(ns.all):
            assert_raises_nsp(fun, name)

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_zombie_process(self):
        _parent, zombie = self.spawn_zombie()
        self.assert_proc_zombie(zombie)

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_zombie_process_is_running_w_exc(self):
        # 025705.python.test_process.line1384.comment Emulate a case where internally is_running() raises
        # 025706.python.test_process.line1385.comment ZombieProcess.
        p = psutil.Process()
        with mock.patch(
            "psutil.Process", side_effect=psutil.ZombieProcess(0)
        ) as m:
            assert p.is_running()
            assert m.called

    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    def test_zombie_process_status_w_exc(self):
        # 025707.python.test_process.line1395.comment Emulate a case where internally status() raises
        # 025708.python.test_process.line1396.comment ZombieProcess.
        p = psutil.Process()
        with mock.patch(
            "psutil._psplatform.Process.status",
            side_effect=psutil.ZombieProcess(0),
        ) as m:
            assert p.status() == psutil.STATUS_ZOMBIE
            assert m.called

    def test_reused_pid(self):
        # 025709.python.test_process.line1406.comment Emulate a case where PID has been reused by another process.
        subp = self.spawn_subproc()
        p = psutil.Process(subp.pid)
        p._ident = (p.pid, p.create_time() + 100)

        list(psutil.process_iter())
        assert p.pid in psutil._pmap
        assert not p.is_running()

        # 025710.python.test_process.line1415.comment make sure is_running() removed PID from process_iter()
        # 025711.python.test_process.line1416.comment internal cache
        with mock.patch.object(psutil._common, "PSUTIL_DEBUG", True):
            with contextlib.redirect_stderr(io.StringIO()) as f:
                list(psutil.process_iter())
        assert (
            f"refreshing Process instance for reused PID {p.pid}"
            in f.getvalue()
        )
        assert p.pid not in psutil._pmap

        assert p != psutil.Process(subp.pid)
        msg = "process no longer exists and its PID has been reused"
        ns = process_namespace(p)
        for fun, name in ns.iter(ns.setters + ns.killers, clear_cache=False):
            with self.subTest(name=name):
                with pytest.raises(psutil.NoSuchProcess, match=msg):
                    fun()

        assert "terminated + PID reused" in str(p)
        assert "terminated + PID reused" in repr(p)

        with pytest.raises(psutil.NoSuchProcess, match=msg):
            p.ppid()
        with pytest.raises(psutil.NoSuchProcess, match=msg):
            p.parent()
        with pytest.raises(psutil.NoSuchProcess, match=msg):
            p.parents()
        with pytest.raises(psutil.NoSuchProcess, match=msg):
            p.children()

    def test_pid_0(self):
        # 025712.python.test_process.line1447.comment Process(0) is supposed to work on all platforms except Linux
        if 0 not in psutil.pids():
            with pytest.raises(psutil.NoSuchProcess):
                psutil.Process(0)
            # 025713.python.test_process.line1451.comment These 2 are a contradiction, but "ps" says PID 1's parent
            # 025714.python.test_process.line1452.comment is PID 0.
            assert not psutil.pid_exists(0)
            assert psutil.Process(1).ppid() == 0
            return

        p = psutil.Process(0)
        exc = psutil.AccessDenied if WINDOWS else ValueError
        with pytest.raises(exc):
            p.wait()
        with pytest.raises(exc):
            p.terminate()
        with pytest.raises(exc):
            p.suspend()
        with pytest.raises(exc):
            p.resume()
        with pytest.raises(exc):
            p.kill()
        with pytest.raises(exc):
            p.send_signal(signal.SIGTERM)

        # 025715.python.test_process.line1472.comment test all methods
        ns = process_namespace(p)
        for fun, name in ns.iter(ns.getters + ns.setters):
            try:
                ret = fun()
            except psutil.AccessDenied:
                pass
            else:
                if name in {"uids", "gids"}:
                    assert ret.real == 0
                elif name == "username":
                    user = 'NT AUTHORITY\\SYSTEM' if WINDOWS else 'root'
                    assert p.username() == user
                elif name == "name":
                    assert name, name

        if not OPENBSD:
            assert 0 in psutil.pids()
            assert psutil.pid_exists(0)

    @pytest.mark.skipif(not HAS_ENVIRON, reason="not supported")
    def test_environ(self):
        def clean_dict(d):
            exclude = ["PLAT", "HOME", "PYTEST_CURRENT_TEST", "PYTEST_VERSION"]
            if MACOS:
                exclude.extend([
                    "__CF_USER_TEXT_ENCODING",
                    "VERSIONER_PYTHON_PREFER_32_BIT",
                    "VERSIONER_PYTHON_VERSION",
                    "VERSIONER_PYTHON_VERSION",
                ])
            for name in exclude:
                d.pop(name, None)
            return {
                k.replace("\r", "").replace("\n", ""): (
                    v.replace("\r", "").replace("\n", "")
                )
                for k, v in d.items()
            }

        self.maxDiff = None
        p = psutil.Process()
        d1 = clean_dict(p.environ())
        d2 = clean_dict(os.environ.copy())
        if not OSX and GITHUB_ACTIONS:
            assert d1 == d2

    @pytest.mark.skipif(not HAS_ENVIRON, reason="not supported")
    @pytest.mark.skipif(not POSIX, reason="POSIX only")
    @pytest.mark.skipif(
        MACOS_11PLUS,
        reason="macOS 11+ can't get another process environment, issue #2084",
    )
    @pytest.mark.skipif(
        NETBSD, reason="sometimes fails on `assert is_running()`"
    )
    def test_weird_environ(self):
        # 025716.python.test_process.line1529.comment environment variables can contain values without an equals sign
        code = textwrap.dedent("""
            #include <unistd.h>
            #include <fcntl.h>

            char * const argv[] = {"cat", 0};
            char * const envp[] = {"A=1", "X", "C=3", 0};

            int main(void) {
                // Close stderr on exec so parent can wait for the
                // execve to finish.
                if (fcntl(2, F_SETFD, FD_CLOEXEC) != 0)
                    return 0;
                return execve("/bin/cat", argv, envp);
            }
            """)
        cexe = create_c_exe(self.get_testfn(), c_code=code)
        sproc = self.spawn_subproc(
            [cexe], stdin=subprocess.PIPE, stderr=subprocess.PIPE
        )
        p = psutil.Process(sproc.pid)
        wait_for_pid(p.pid)
        assert p.is_running()
        # 025717.python.test_process.line1552.comment Wait for process to exec or exit.
        assert sproc.stderr.read() == b""
        if MACOS and CI_TESTING:
            try:
                env = p.environ()
            except psutil.AccessDenied:
                # 025718.python.test_process.line1558.comment XXX: fails sometimes with:
                # 025719.python.test_process.line1559.comment PermissionError from 'sysctl(KERN_PROCARGS2) -> EIO'
                return
        else:
            env = p.environ()
        assert env == {"A": "1", "C": "3"}
        sproc.communicate()
        assert sproc.returncode == 0


# 025720.python.test_process.line1568.comment ===================================================================
# 025721.python.test_process.line1569.comment --- psutil.Popen tests
# 025722.python.test_process.line1570.comment ===================================================================


class TestPopen(PsutilTestCase):
    """Tests for psutil.Popen class."""

    @classmethod
    def tearDownClass(cls):
        reap_children()

    @pytest.mark.skipif(MACOS and GITHUB_ACTIONS, reason="hangs on OSX + CI")
    def test_misc(self):
        # 025723.python.test_process.line1582.comment XXX this test causes a ResourceWarning because
        # 025724.python.test_process.line1583.comment psutil.__subproc instance doesn't get properly freed.
        # 025725.python.test_process.line1584.comment Not sure what to do though.
        cmd = [
            PYTHON_EXE,
            "-c",
            "import time; [time.sleep(0.1) for x in range(100)];",
        ]
        with psutil.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=PYTHON_EXE_ENV,
        ) as proc:
            proc.name()
            proc.cpu_times()
            proc.stdin  # noqa: B018
            assert dir(proc)
            with pytest.raises(AttributeError):
                proc.foo  # noqa: B018
            proc.terminate()
        if POSIX:
            assert proc.wait(5) == -signal.SIGTERM
        else:
            assert proc.wait(5) == signal.SIGTERM

    def test_ctx_manager(self):
        with psutil.Popen(
            [PYTHON_EXE, "-V"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=PYTHON_EXE_ENV,
        ) as proc:
            proc.communicate()
        assert proc.stdout.closed
        assert proc.stderr.closed
        assert proc.stdin.closed
        assert proc.returncode == 0

    def test_kill_terminate(self):
        # 025728.python.test_process.line1623.comment subprocess.Popen()'s terminate(), kill() and send_signal() do
        # 025729.python.test_process.line1624.comment not raise exception after the process is gone. psutil.Popen
        # 025730.python.test_process.line1625.comment diverges from that.
        cmd = [
            PYTHON_EXE,
            "-c",
            "import time; [time.sleep(0.1) for x in range(100)];",
        ]
        with psutil.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=PYTHON_EXE_ENV,
        ) as proc:
            proc.terminate()
            proc.wait()
            with pytest.raises(psutil.NoSuchProcess):
                proc.terminate()
            with pytest.raises(psutil.NoSuchProcess):
                proc.kill()
            with pytest.raises(psutil.NoSuchProcess):
                proc.send_signal(signal.SIGTERM)
            if WINDOWS:
                with pytest.raises(psutil.NoSuchProcess):
                    proc.send_signal(signal.CTRL_C_EVENT)
                with pytest.raises(psutil.NoSuchProcess):
                    proc.send_signal(signal.CTRL_BREAK_EVENT)

    def test__getattribute__(self):
        cmd = [
            PYTHON_EXE,
            "-c",
            "import time; [time.sleep(0.1) for x in range(100)];",
        ]
        with psutil.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=PYTHON_EXE_ENV,
        ) as proc:
            proc.terminate()
            proc.wait()
            with pytest.raises(AttributeError):
                proc.foo  # noqa: B018
