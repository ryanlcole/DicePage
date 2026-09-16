"""Tests for distutils.spawn."""

import os
import stat
import sys
import unittest.mock as mock
from distutils.errors import DistutilsExecError
from distutils.spawn import find_executable, spawn
from distutils.tests import support

import path
import pytest
from test.support import unix_shell

from .compat import py39 as os_helper


class TestSpawn(support.TempdirManager):
    @pytest.mark.skipif("os.name not in ('nt', 'posix')")
    def test_spawn(self):
        tmpdir = self.mkdtemp()

        # 041216.python.test_spawn.line23.comment creating something executable
        # 041217.python.test_spawn.line24.comment through the shell that returns 1
        if sys.platform != 'win32':
            exe = os.path.join(tmpdir, 'foo.sh')
            self.write_file(exe, f'#!{unix_shell}\nexit 1')
        else:
            exe = os.path.join(tmpdir, 'foo.bat')
            self.write_file(exe, 'exit 1')

        os.chmod(exe, 0o777)
        with pytest.raises(DistutilsExecError):
            spawn([exe])

        # 041218.python.test_spawn.line36.comment now something that works
        if sys.platform != 'win32':
            exe = os.path.join(tmpdir, 'foo.sh')
            self.write_file(exe, f'#!{unix_shell}\nexit 0')
        else:
            exe = os.path.join(tmpdir, 'foo.bat')
            self.write_file(exe, 'exit 0')

        os.chmod(exe, 0o777)
        spawn([exe])  # should work without any error

    def test_find_executable(self, tmp_path):
        program_path = self._make_executable(tmp_path, '.exe')
        program = program_path.name
        program_noeext = program_path.with_suffix('').name
        filename = str(program_path)
        tmp_dir = path.Path(tmp_path)

        # 041220.python.test_spawn.line54.comment test path parameter
        rv = find_executable(program, path=tmp_dir)
        assert rv == filename

        if sys.platform == 'win32':
            # 041221.python.test_spawn.line59.comment test without ".exe" extension
            rv = find_executable(program_noeext, path=tmp_dir)
            assert rv == filename

        # 041222.python.test_spawn.line63.comment test find in the current directory
        with tmp_dir:
            rv = find_executable(program)
            assert rv == program

        # 041223.python.test_spawn.line68.comment test non-existent program
        dont_exist_program = "dontexist_" + program
        rv = find_executable(dont_exist_program, path=tmp_dir)
        assert rv is None

        # 041224.python.test_spawn.line73.comment PATH='': no match, except in the current directory
        with os_helper.EnvironmentVarGuard() as env:
            env['PATH'] = ''
            with (
                mock.patch(
                    'distutils.spawn.os.confstr', return_value=tmp_dir, create=True
                ),
                mock.patch('distutils.spawn.os.defpath', tmp_dir),
            ):
                rv = find_executable(program)
                assert rv is None

                # 041225.python.test_spawn.line85.comment look in current directory
                with tmp_dir:
                    rv = find_executable(program)
                    assert rv == program

        # 041226.python.test_spawn.line90.comment PATH=':': explicitly looks in the current directory
        with os_helper.EnvironmentVarGuard() as env:
            env['PATH'] = os.pathsep
            with (
                mock.patch('distutils.spawn.os.confstr', return_value='', create=True),
                mock.patch('distutils.spawn.os.defpath', ''),
            ):
                rv = find_executable(program)
                assert rv is None

                # 041227.python.test_spawn.line100.comment look in current directory
                with tmp_dir:
                    rv = find_executable(program)
                    assert rv == program

        # 041228.python.test_spawn.line105.comment missing PATH: test os.confstr("CS_PATH") and os.defpath
        with os_helper.EnvironmentVarGuard() as env:
            env.pop('PATH', None)

            # 041229.python.test_spawn.line109.comment without confstr
            with (
                mock.patch(
                    'distutils.spawn.os.confstr', side_effect=ValueError, create=True
                ),
                mock.patch('distutils.spawn.os.defpath', tmp_dir),
            ):
                rv = find_executable(program)
                assert rv == filename

            # 041230.python.test_spawn.line119.comment with confstr
            with (
                mock.patch(
                    'distutils.spawn.os.confstr', return_value=tmp_dir, create=True
                ),
                mock.patch('distutils.spawn.os.defpath', ''),
            ):
                rv = find_executable(program)
                assert rv == filename

    @staticmethod
    def _make_executable(tmp_path, ext):
        # 041231.python.test_spawn.line131.comment Give the temporary program a suffix regardless of platform.
        # 041232.python.test_spawn.line132.comment It's needed on Windows and not harmful on others.
        program = tmp_path.joinpath('program').with_suffix(ext)
        program.write_text("", encoding='utf-8')
        program.chmod(stat.S_IXUSR)
        return program

    def test_spawn_missing_exe(self):
        with pytest.raises(DistutilsExecError) as ctx:
            spawn(['does-not-exist'])
        assert "command 'does-not-exist' failed" in str(ctx.value)
