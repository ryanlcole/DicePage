#!/usr/bin/env python3

# 025376.python.test_misc.line3.comment Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# 025377.python.test_misc.line4.comment Use of this source code is governed by a BSD-style license that can be
# 025378.python.test_misc.line5.comment found in the LICENSE file.

"""Miscellaneous tests."""

import collections
import contextlib
import io
import json
import os
import pickle
import socket
import sys
from unittest import mock

import psutil
import psutil.tests
from psutil import WINDOWS
from psutil._common import bcat
from psutil._common import cat
from psutil._common import debug
from psutil._common import isfile_strict
from psutil._common import memoize
from psutil._common import memoize_when_activated
from psutil._common import parse_environ_block
from psutil._common import supports_ipv6
from psutil._common import wrap_numbers
from psutil.tests import HAS_NET_IO_COUNTERS
from psutil.tests import PsutilTestCase
from psutil.tests import process_namespace
from psutil.tests import pytest
from psutil.tests import reload_module
from psutil.tests import system_namespace

# 025379.python.test_misc.line38.comment ===================================================================
# 025380.python.test_misc.line39.comment --- Test classes' repr(), str(), ...
# 025381.python.test_misc.line40.comment ===================================================================


class TestSpecialMethods(PsutilTestCase):
    def test_check_pid_range(self):
        with pytest.raises(OverflowError):
            psutil._psplatform.cext.check_pid_range(2**128)
        with pytest.raises(psutil.NoSuchProcess):
            psutil.Process(2**128)

    def test_process__repr__(self, func=repr):
        p = psutil.Process(self.spawn_subproc().pid)
        r = func(p)
        assert "psutil.Process" in r
        assert f"pid={p.pid}" in r
        assert f"name='{p.name()}'" in r.replace("name=u'", "name='")
        assert "status=" in r
        assert "exitcode=" not in r
        p.terminate()
        p.wait()
        r = func(p)
        assert "status='terminated'" in r
        assert "exitcode=" in r

        with mock.patch.object(
            psutil.Process,
            "name",
            side_effect=psutil.ZombieProcess(os.getpid()),
        ):
            p = psutil.Process()
            r = func(p)
            assert f"pid={p.pid}" in r
            assert "status='zombie'" in r
            assert "name=" not in r
        with mock.patch.object(
            psutil.Process,
            "name",
            side_effect=psutil.NoSuchProcess(os.getpid()),
        ):
            p = psutil.Process()
            r = func(p)
            assert f"pid={p.pid}" in r
            assert "terminated" in r
            assert "name=" not in r
        with mock.patch.object(
            psutil.Process,
            "name",
            side_effect=psutil.AccessDenied(os.getpid()),
        ):
            p = psutil.Process()
            r = func(p)
            assert f"pid={p.pid}" in r
            assert "name=" not in r

    def test_process__str__(self):
        self.test_process__repr__(func=str)

    def test_error__repr__(self):
        assert repr(psutil.Error()) == "psutil.Error()"

    def test_error__str__(self):
        assert str(psutil.Error()) == ""

    def test_no_such_process__repr__(self):
        assert (
            repr(psutil.NoSuchProcess(321))
            == "psutil.NoSuchProcess(pid=321, msg='process no longer exists')"
        )
        assert (
            repr(psutil.NoSuchProcess(321, name="name", msg="msg"))
            == "psutil.NoSuchProcess(pid=321, name='name', msg='msg')"
        )

    def test_no_such_process__str__(self):
        assert (
            str(psutil.NoSuchProcess(321))
            == "process no longer exists (pid=321)"
        )
        assert (
            str(psutil.NoSuchProcess(321, name="name", msg="msg"))
            == "msg (pid=321, name='name')"
        )

    def test_zombie_process__repr__(self):
        assert (
            repr(psutil.ZombieProcess(321))
            == 'psutil.ZombieProcess(pid=321, msg="PID still '
            'exists but it\'s a zombie")'
        )
        assert (
            repr(psutil.ZombieProcess(321, name="name", ppid=320, msg="foo"))
            == "psutil.ZombieProcess(pid=321, ppid=320, name='name',"
            " msg='foo')"
        )

    def test_zombie_process__str__(self):
        assert (
            str(psutil.ZombieProcess(321))
            == "PID still exists but it's a zombie (pid=321)"
        )
        assert (
            str(psutil.ZombieProcess(321, name="name", ppid=320, msg="foo"))
            == "foo (pid=321, ppid=320, name='name')"
        )

    def test_access_denied__repr__(self):
        assert repr(psutil.AccessDenied(321)) == "psutil.AccessDenied(pid=321)"
        assert (
            repr(psutil.AccessDenied(321, name="name", msg="msg"))
            == "psutil.AccessDenied(pid=321, name='name', msg='msg')"
        )

    def test_access_denied__str__(self):
        assert str(psutil.AccessDenied(321)) == "(pid=321)"
        assert (
            str(psutil.AccessDenied(321, name="name", msg="msg"))
            == "msg (pid=321, name='name')"
        )

    def test_timeout_expired__repr__(self):
        assert (
            repr(psutil.TimeoutExpired(5))
            == "psutil.TimeoutExpired(seconds=5, msg='timeout after 5"
            " seconds')"
        )
        assert (
            repr(psutil.TimeoutExpired(5, pid=321, name="name"))
            == "psutil.TimeoutExpired(pid=321, name='name', seconds=5, "
            "msg='timeout after 5 seconds')"
        )

    def test_timeout_expired__str__(self):
        assert str(psutil.TimeoutExpired(5)) == "timeout after 5 seconds"
        assert (
            str(psutil.TimeoutExpired(5, pid=321, name="name"))
            == "timeout after 5 seconds (pid=321, name='name')"
        )

    def test_process__eq__(self):
        p1 = psutil.Process()
        p2 = psutil.Process()
        assert p1 == p2
        p2._ident = (0, 0)
        assert p1 != p2
        assert p1 != 'foo'

    def test_process__hash__(self):
        s = {psutil.Process(), psutil.Process()}
        assert len(s) == 1


# 025382.python.test_misc.line191.comment ===================================================================
# 025383.python.test_misc.line192.comment --- Misc, generic, corner cases
# 025384.python.test_misc.line193.comment ===================================================================


class TestMisc(PsutilTestCase):
    def test__all__(self):
        dir_psutil = dir(psutil)
        for name in dir_psutil:
            if name in {
                'debug',
                'tests',
                'test',
                'PermissionError',
                'ProcessLookupError',
            }:
                continue
            if not name.startswith('_'):
                try:
                    __import__(name)
                except ImportError:
                    if name not in psutil.__all__:
                        fun = getattr(psutil, name)
                        if fun is None:
                            continue
                        if (
                            fun.__doc__ is not None
                            and 'deprecated' not in fun.__doc__.lower()
                        ):
                            raise pytest.fail(
                                f"{name!r} not in psutil.__all__"
                            )

        # 025385.python.test_misc.line224.comment Import 'star' will break if __all__ is inconsistent, see:
        # 025386.python.test_misc.line225.comment https://github.com/giampaolo/psutil/issues/656
        # 025387.python.test_misc.line226.comment Can't do `from psutil import *` as it won't work
        # 025388.python.test_misc.line227.comment so we simply iterate over __all__.
        for name in psutil.__all__:
            assert name in dir_psutil

    def test_version(self):
        assert (
            '.'.join([str(x) for x in psutil.version_info])
            == psutil.__version__
        )

    def test_process_as_dict_no_new_names(self):
        # 025389.python.test_misc.line238.comment See https://github.com/giampaolo/psutil/issues/813
        p = psutil.Process()
        p.foo = '1'
        assert 'foo' not in p.as_dict()

    def test_serialization(self):
        def check(ret):
            json.loads(json.dumps(ret))

            a = pickle.dumps(ret)
            b = pickle.loads(a)
            assert ret == b

        # 025390.python.test_misc.line251.comment --- process APIs

        proc = psutil.Process()
        check(psutil.Process().as_dict())

        ns = process_namespace(proc)
        for fun, name in ns.iter(ns.getters, clear_cache=True):
            with self.subTest(proc=str(proc), name=name):
                try:
                    ret = fun()
                except psutil.Error:
                    pass
                else:
                    check(ret)

        # 025391.python.test_misc.line266.comment --- system APIs

        ns = system_namespace()
        for fun, name in ns.iter(ns.getters):
            if name in {"win_service_iter", "win_service_get"}:
                continue
            with self.subTest(name=name):
                try:
                    ret = fun()
                except psutil.AccessDenied:
                    pass
                else:
                    check(ret)

        # 025392.python.test_misc.line280.comment --- exception classes

        b = pickle.loads(
            pickle.dumps(
                psutil.NoSuchProcess(pid=4567, name='name', msg='msg')
            )
        )
        assert isinstance(b, psutil.NoSuchProcess)
        assert b.pid == 4567
        assert b.name == 'name'
        assert b.msg == 'msg'

        b = pickle.loads(
            pickle.dumps(
                psutil.ZombieProcess(pid=4567, name='name', ppid=42, msg='msg')
            )
        )
        assert isinstance(b, psutil.ZombieProcess)
        assert b.pid == 4567
        assert b.ppid == 42
        assert b.name == 'name'
        assert b.msg == 'msg'

        b = pickle.loads(
            pickle.dumps(psutil.AccessDenied(pid=123, name='name', msg='msg'))
        )
        assert isinstance(b, psutil.AccessDenied)
        assert b.pid == 123
        assert b.name == 'name'
        assert b.msg == 'msg'

        b = pickle.loads(
            pickle.dumps(
                psutil.TimeoutExpired(seconds=33, pid=4567, name='name')
            )
        )
        assert isinstance(b, psutil.TimeoutExpired)
        assert b.seconds == 33
        assert b.pid == 4567
        assert b.name == 'name'

    def test_ad_on_process_creation(self):
        # 025393.python.test_misc.line322.comment We are supposed to be able to instantiate Process also in case
        # 025394.python.test_misc.line323.comment of zombie processes or access denied.
        with mock.patch.object(
            psutil.Process, '_get_ident', side_effect=psutil.AccessDenied
        ) as meth:
            psutil.Process()
            assert meth.called

        with mock.patch.object(
            psutil.Process, '_get_ident', side_effect=psutil.ZombieProcess(1)
        ) as meth:
            psutil.Process()
            assert meth.called

        with mock.patch.object(
            psutil.Process, '_get_ident', side_effect=ValueError
        ) as meth:
            with pytest.raises(ValueError):
                psutil.Process()
            assert meth.called

        with mock.patch.object(
            psutil.Process, '_get_ident', side_effect=psutil.NoSuchProcess(1)
        ) as meth:
            with pytest.raises(psutil.NoSuchProcess):
                psutil.Process()
            assert meth.called

    def test_sanity_version_check(self):
        # 025395.python.test_misc.line351.comment see: https://github.com/giampaolo/psutil/issues/564
        with mock.patch(
            "psutil._psplatform.cext.version", return_value="0.0.0"
        ):
            with pytest.raises(ImportError) as cm:
                reload_module(psutil)
            assert "version conflict" in str(cm.value).lower()


# 025396.python.test_misc.line360.comment ===================================================================
# 025397.python.test_misc.line361.comment --- psutil/_common.py utils
# 025398.python.test_misc.line362.comment ===================================================================


class TestMemoizeDecorator(PsutilTestCase):
    def setUp(self):
        self.calls = []

    tearDown = setUp

    def run_against(self, obj, expected_retval=None):
        # 025399.python.test_misc.line372.comment no args
        for _ in range(2):
            ret = obj()
            assert self.calls == [((), {})]
            if expected_retval is not None:
                assert ret == expected_retval
        # 025400.python.test_misc.line378.comment with args
        for _ in range(2):
            ret = obj(1)
            assert self.calls == [((), {}), ((1,), {})]
            if expected_retval is not None:
                assert ret == expected_retval
        # 025401.python.test_misc.line384.comment with args + kwargs
        for _ in range(2):
            ret = obj(1, bar=2)
            assert self.calls == [((), {}), ((1,), {}), ((1,), {'bar': 2})]
            if expected_retval is not None:
                assert ret == expected_retval
        # 025402.python.test_misc.line390.comment clear cache
        assert len(self.calls) == 3
        obj.cache_clear()
        ret = obj()
        if expected_retval is not None:
            assert ret == expected_retval
        assert len(self.calls) == 4
        # 025403.python.test_misc.line397.comment docstring
        assert obj.__doc__ == "My docstring."

    def test_function(self):
        @memoize
        def foo(*args, **kwargs):
            """My docstring."""
            baseclass.calls.append((args, kwargs))
            return 22

        baseclass = self
        self.run_against(foo, expected_retval=22)

    def test_class(self):
        @memoize
        class Foo:
            """My docstring."""

            def __init__(self, *args, **kwargs):
                baseclass.calls.append((args, kwargs))

            def bar(self):
                return 22

        baseclass = self
        self.run_against(Foo, expected_retval=None)
        assert Foo().bar() == 22

    def test_class_singleton(self):
        # 025404.python.test_misc.line426.comment @memoize can be used against classes to create singletons
        @memoize
        class Bar:
            def __init__(self, *args, **kwargs):
                pass

        assert Bar() is Bar()
        assert id(Bar()) == id(Bar())
        assert id(Bar(1)) == id(Bar(1))
        assert id(Bar(1, foo=3)) == id(Bar(1, foo=3))
        assert id(Bar(1)) != id(Bar(2))

    def test_staticmethod(self):
        class Foo:
            @staticmethod
            @memoize
            def bar(*args, **kwargs):
                """My docstring."""
                baseclass.calls.append((args, kwargs))
                return 22

        baseclass = self
        self.run_against(Foo().bar, expected_retval=22)

    def test_classmethod(self):
        class Foo:
            @classmethod
            @memoize
            def bar(cls, *args, **kwargs):
                """My docstring."""
                baseclass.calls.append((args, kwargs))
                return 22

        baseclass = self
        self.run_against(Foo().bar, expected_retval=22)

    def test_original(self):
        # 025405.python.test_misc.line463.comment This was the original test before I made it dynamic to test it
        # 025406.python.test_misc.line464.comment against different types. Keeping it anyway.
        @memoize
        def foo(*args, **kwargs):
            """Foo docstring."""
            calls.append(None)
            return (args, kwargs)

        calls = []
        # 025407.python.test_misc.line472.comment no args
        for _ in range(2):
            ret = foo()
            expected = ((), {})
            assert ret == expected
            assert len(calls) == 1
        # 025408.python.test_misc.line478.comment with args
        for _ in range(2):
            ret = foo(1)
            expected = ((1,), {})
            assert ret == expected
            assert len(calls) == 2
        # 025409.python.test_misc.line484.comment with args + kwargs
        for _ in range(2):
            ret = foo(1, bar=2)
            expected = ((1,), {'bar': 2})
            assert ret == expected
            assert len(calls) == 3
        # 025410.python.test_misc.line490.comment clear cache
        foo.cache_clear()
        ret = foo()
        expected = ((), {})
        assert ret == expected
        assert len(calls) == 4
        # 025411.python.test_misc.line496.comment docstring
        assert foo.__doc__ == "Foo docstring."


class TestCommonModule(PsutilTestCase):
    def test_memoize_when_activated(self):
        class Foo:
            @memoize_when_activated
            def foo(self):
                calls.append(None)

        f = Foo()
        calls = []
        f.foo()
        f.foo()
        assert len(calls) == 2

        # 025412.python.test_misc.line513.comment activate
        calls = []
        f.foo.cache_activate(f)
        f.foo()
        f.foo()
        assert len(calls) == 1

        # 025413.python.test_misc.line520.comment deactivate
        calls = []
        f.foo.cache_deactivate(f)
        f.foo()
        f.foo()
        assert len(calls) == 2

    def test_parse_environ_block(self):
        def k(s):
            return s.upper() if WINDOWS else s

        assert parse_environ_block("a=1\0") == {k("a"): "1"}
        assert parse_environ_block("a=1\0b=2\0\0") == {
            k("a"): "1",
            k("b"): "2",
        }
        assert parse_environ_block("a=1\0b=\0\0") == {k("a"): "1", k("b"): ""}
        # 025414.python.test_misc.line537.comment ignore everything after \0\0
        assert parse_environ_block("a=1\0b=2\0\0c=3\0") == {
            k("a"): "1",
            k("b"): "2",
        }
        # 025415.python.test_misc.line542.comment ignore everything that is not an assignment
        assert parse_environ_block("xxx\0a=1\0") == {k("a"): "1"}
        assert parse_environ_block("a=1\0=b=2\0") == {k("a"): "1"}
        # 025416.python.test_misc.line545.comment do not fail if the block is incomplete
        assert parse_environ_block("a=1\0b=2") == {k("a"): "1"}

    def test_supports_ipv6(self):
        if supports_ipv6():
            with mock.patch('psutil._common.socket') as s:
                s.has_ipv6 = False
                assert not supports_ipv6()

            with mock.patch(
                'psutil._common.socket.socket', side_effect=OSError
            ) as s:
                assert not supports_ipv6()
                assert s.called

            with mock.patch(
                'psutil._common.socket.socket', side_effect=socket.gaierror
            ) as s:
                assert not supports_ipv6()
                assert s.called

            with mock.patch(
                'psutil._common.socket.socket.bind',
                side_effect=socket.gaierror,
            ) as s:
                assert not supports_ipv6()
                assert s.called
        else:
            with pytest.raises(OSError):
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                try:
                    sock.bind(("::1", 0))
                finally:
                    sock.close()

    def test_isfile_strict(self):
        this_file = os.path.abspath(__file__)
        assert isfile_strict(this_file)
        assert not isfile_strict(os.path.dirname(this_file))
        with mock.patch('psutil._common.os.stat', side_effect=PermissionError):
            with pytest.raises(OSError):
                isfile_strict(this_file)
        with mock.patch(
            'psutil._common.os.stat', side_effect=FileNotFoundError
        ):
            assert not isfile_strict(this_file)
        with mock.patch('psutil._common.stat.S_ISREG', return_value=False):
            assert not isfile_strict(this_file)

    def test_debug(self):
        with mock.patch.object(psutil._common, "PSUTIL_DEBUG", True):
            with contextlib.redirect_stderr(io.StringIO()) as f:
                debug("hello")
                sys.stderr.flush()
        msg = f.getvalue()
        assert msg.startswith("psutil-debug"), msg
        assert "hello" in msg
        assert __file__.replace('.pyc', '.py') in msg

        # 025417.python.test_misc.line604.comment supposed to use repr(exc)
        with mock.patch.object(psutil._common, "PSUTIL_DEBUG", True):
            with contextlib.redirect_stderr(io.StringIO()) as f:
                debug(ValueError("this is an error"))
        msg = f.getvalue()
        assert "ignoring ValueError" in msg
        assert "'this is an error'" in msg

        # 025418.python.test_misc.line612.comment supposed to use str(exc), because of extra info about file name
        with mock.patch.object(psutil._common, "PSUTIL_DEBUG", True):
            with contextlib.redirect_stderr(io.StringIO()) as f:
                exc = OSError(2, "no such file")
                exc.filename = "/foo"
                debug(exc)
        msg = f.getvalue()
        assert "no such file" in msg
        assert "/foo" in msg

    def test_cat_bcat(self):
        testfn = self.get_testfn()
        with open(testfn, "w") as f:
            f.write("foo")
        assert cat(testfn) == "foo"
        assert bcat(testfn) == b"foo"
        with pytest.raises(FileNotFoundError):
            cat(testfn + '-invalid')
        with pytest.raises(FileNotFoundError):
            bcat(testfn + '-invalid')
        assert cat(testfn + '-invalid', fallback="bar") == "bar"
        assert bcat(testfn + '-invalid', fallback="bar") == "bar"


# 025419.python.test_misc.line636.comment ===================================================================
# 025420.python.test_misc.line637.comment --- Tests for wrap_numbers() function.
# 025421.python.test_misc.line638.comment ===================================================================


nt = collections.namedtuple('foo', 'a b c')


class TestWrapNumbers(PsutilTestCase):
    def setUp(self):
        wrap_numbers.cache_clear()

    tearDown = setUp

    def test_first_call(self):
        input = {'disk1': nt(5, 5, 5)}
        assert wrap_numbers(input, 'disk_io') == input

    def test_input_hasnt_changed(self):
        input = {'disk1': nt(5, 5, 5)}
        assert wrap_numbers(input, 'disk_io') == input
        assert wrap_numbers(input, 'disk_io') == input

    def test_increase_but_no_wrap(self):
        input = {'disk1': nt(5, 5, 5)}
        assert wrap_numbers(input, 'disk_io') == input
        input = {'disk1': nt(10, 15, 20)}
        assert wrap_numbers(input, 'disk_io') == input
        input = {'disk1': nt(20, 25, 30)}
        assert wrap_numbers(input, 'disk_io') == input
        input = {'disk1': nt(20, 25, 30)}
        assert wrap_numbers(input, 'disk_io') == input

    def test_wrap(self):
        # 025422.python.test_misc.line670.comment let's say 100 is the threshold
        input = {'disk1': nt(100, 100, 100)}
        assert wrap_numbers(input, 'disk_io') == input
        # 025423.python.test_misc.line673.comment first wrap restarts from 10
        input = {'disk1': nt(100, 100, 10)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(100, 100, 110)}
        # 025424.python.test_misc.line676.comment then it remains the same
        input = {'disk1': nt(100, 100, 10)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(100, 100, 110)}
        # 025425.python.test_misc.line679.comment then it goes up
        input = {'disk1': nt(100, 100, 90)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(100, 100, 190)}
        # 025426.python.test_misc.line682.comment then it wraps again
        input = {'disk1': nt(100, 100, 20)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(100, 100, 210)}
        # 025427.python.test_misc.line685.comment and remains the same
        input = {'disk1': nt(100, 100, 20)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(100, 100, 210)}
        # 025428.python.test_misc.line688.comment now wrap another num
        input = {'disk1': nt(50, 100, 20)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(150, 100, 210)}
        # 025429.python.test_misc.line691.comment and again
        input = {'disk1': nt(40, 100, 20)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(190, 100, 210)}
        # 025430.python.test_misc.line694.comment keep it the same
        input = {'disk1': nt(40, 100, 20)}
        assert wrap_numbers(input, 'disk_io') == {'disk1': nt(190, 100, 210)}

    def test_changing_keys(self):
        # 025431.python.test_misc.line699.comment Emulate a case where the second call to disk_io()
        # 025432.python.test_misc.line700.comment (or whatever) provides a new disk, then the new disk
        # 025433.python.test_misc.line701.comment disappears on the third call.
        input = {'disk1': nt(5, 5, 5)}
        assert wrap_numbers(input, 'disk_io') == input
        input = {'disk1': nt(5, 5, 5), 'disk2': nt(7, 7, 7)}
        assert wrap_numbers(input, 'disk_io') == input
        input = {'disk1': nt(8, 8, 8)}
        assert wrap_numbers(input, 'disk_io') == input

    def test_changing_keys_w_wrap(self):
        input = {'disk1': nt(50, 50, 50), 'disk2': nt(100, 100, 100)}
        assert wrap_numbers(input, 'disk_io') == input
        # 025434.python.test_misc.line712.comment disk 2 wraps
        input = {'disk1': nt(50, 50, 50), 'disk2': nt(100, 100, 10)}
        assert wrap_numbers(input, 'disk_io') == {
            'disk1': nt(50, 50, 50),
            'disk2': nt(100, 100, 110),
        }
        # 025435.python.test_misc.line718.comment disk 2 disappears
        input = {'disk1': nt(50, 50, 50)}
        assert wrap_numbers(input, 'disk_io') == input

        # 025436.python.test_misc.line722.comment then it appears again; the old wrap is supposed to be
        # 025437.python.test_misc.line723.comment gone.
        input = {'disk1': nt(50, 50, 50), 'disk2': nt(100, 100, 100)}
        assert wrap_numbers(input, 'disk_io') == input
        # 025438.python.test_misc.line726.comment remains the same
        input = {'disk1': nt(50, 50, 50), 'disk2': nt(100, 100, 100)}
        assert wrap_numbers(input, 'disk_io') == input
        # 025439.python.test_misc.line729.comment and then wraps again
        input = {'disk1': nt(50, 50, 50), 'disk2': nt(100, 100, 10)}
        assert wrap_numbers(input, 'disk_io') == {
            'disk1': nt(50, 50, 50),
            'disk2': nt(100, 100, 110),
        }

    def test_real_data(self):
        d = {
            'nvme0n1': (300, 508, 640, 1571, 5970, 1987, 2049, 451751, 47048),
            'nvme0n1p1': (1171, 2, 5600256, 1024, 516, 0, 0, 0, 8),
            'nvme0n1p2': (54, 54, 2396160, 5165056, 4, 24, 30, 1207, 28),
            'nvme0n1p3': (2389, 4539, 5154, 150, 4828, 1844, 2019, 398, 348),
        }
        assert wrap_numbers(d, 'disk_io') == d
        assert wrap_numbers(d, 'disk_io') == d
        # 025440.python.test_misc.line745.comment decrease this   ↓
        d = {
            'nvme0n1': (100, 508, 640, 1571, 5970, 1987, 2049, 451751, 47048),
            'nvme0n1p1': (1171, 2, 5600256, 1024, 516, 0, 0, 0, 8),
            'nvme0n1p2': (54, 54, 2396160, 5165056, 4, 24, 30, 1207, 28),
            'nvme0n1p3': (2389, 4539, 5154, 150, 4828, 1844, 2019, 398, 348),
        }
        out = wrap_numbers(d, 'disk_io')
        assert out['nvme0n1'][0] == 400

    # 025441.python.test_misc.line755.comment --- cache tests

    def test_cache_first_call(self):
        input = {'disk1': nt(5, 5, 5)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        assert cache[1] == {'disk_io': {}}
        assert cache[2] == {'disk_io': {}}

    def test_cache_call_twice(self):
        input = {'disk1': nt(5, 5, 5)}
        wrap_numbers(input, 'disk_io')
        input = {'disk1': nt(10, 10, 10)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        assert cache[1] == {
            'disk_io': {('disk1', 0): 0, ('disk1', 1): 0, ('disk1', 2): 0}
        }
        assert cache[2] == {'disk_io': {}}

    def test_cache_wrap(self):
        # 025442.python.test_misc.line778.comment let's say 100 is the threshold
        input = {'disk1': nt(100, 100, 100)}
        wrap_numbers(input, 'disk_io')

        # 025443.python.test_misc.line782.comment first wrap restarts from 10
        input = {'disk1': nt(100, 100, 10)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        assert cache[1] == {
            'disk_io': {('disk1', 0): 0, ('disk1', 1): 0, ('disk1', 2): 100}
        }
        assert cache[2] == {'disk_io': {'disk1': {('disk1', 2)}}}

        def check_cache_info():
            cache = wrap_numbers.cache_info()
            assert cache[1] == {
                'disk_io': {
                    ('disk1', 0): 0,
                    ('disk1', 1): 0,
                    ('disk1', 2): 100,
                }
            }
            assert cache[2] == {'disk_io': {'disk1': {('disk1', 2)}}}

        # 025444.python.test_misc.line803.comment then it remains the same
        input = {'disk1': nt(100, 100, 10)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        check_cache_info()

        # 025445.python.test_misc.line810.comment then it goes up
        input = {'disk1': nt(100, 100, 90)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        check_cache_info()

        # 025446.python.test_misc.line817.comment then it wraps again
        input = {'disk1': nt(100, 100, 20)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        assert cache[1] == {
            'disk_io': {('disk1', 0): 0, ('disk1', 1): 0, ('disk1', 2): 190}
        }
        assert cache[2] == {'disk_io': {'disk1': {('disk1', 2)}}}

    def test_cache_changing_keys(self):
        input = {'disk1': nt(5, 5, 5)}
        wrap_numbers(input, 'disk_io')
        input = {'disk1': nt(5, 5, 5), 'disk2': nt(7, 7, 7)}
        wrap_numbers(input, 'disk_io')
        cache = wrap_numbers.cache_info()
        assert cache[0] == {'disk_io': input}
        assert cache[1] == {
            'disk_io': {('disk1', 0): 0, ('disk1', 1): 0, ('disk1', 2): 0}
        }
        assert cache[2] == {'disk_io': {}}

    def test_cache_clear(self):
        input = {'disk1': nt(5, 5, 5)}
        wrap_numbers(input, 'disk_io')
        wrap_numbers(input, 'disk_io')
        wrap_numbers.cache_clear('disk_io')
        assert wrap_numbers.cache_info() == ({}, {}, {})
        wrap_numbers.cache_clear('disk_io')
        wrap_numbers.cache_clear('?!?')

    @pytest.mark.skipif(not HAS_NET_IO_COUNTERS, reason="not supported")
    def test_cache_clear_public_apis(self):
        if not psutil.disk_io_counters() or not psutil.net_io_counters():
            raise pytest.skip("no disks or NICs available")
        psutil.disk_io_counters()
        psutil.net_io_counters()
        caches = wrap_numbers.cache_info()
        for cache in caches:
            assert 'psutil.disk_io_counters' in cache
            assert 'psutil.net_io_counters' in cache

        psutil.disk_io_counters.cache_clear()
        caches = wrap_numbers.cache_info()
        for cache in caches:
            assert 'psutil.net_io_counters' in cache
            assert 'psutil.disk_io_counters' not in cache

        psutil.net_io_counters.cache_clear()
        caches = wrap_numbers.cache_info()
        assert caches == ({}, {}, {})
