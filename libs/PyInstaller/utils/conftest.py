# 009640.python.conftest.line1.comment -----------------------------------------------------------------------------
# 009641.python.conftest.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009642.python.conftest.line3.comment
# 009643.python.conftest.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009644.python.conftest.line5.comment or later) with exception for distributing the bootloader.
# 009645.python.conftest.line6.comment
# 009646.python.conftest.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009647.python.conftest.line8.comment
# 009648.python.conftest.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009649.python.conftest.line10.comment -----------------------------------------------------------------------------

import contextlib
import copy
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import time

# 009650.python.conftest.line23.comment Set a handler for the root-logger to inhibit 'basicConfig()' (called in PyInstaller.log) is setting up a stream
# 009651.python.conftest.line24.comment handler writing to stderr. This avoids log messages to be written (and captured) twice: once on stderr and
# 009652.python.conftest.line25.comment once by pytests's caplog.
logging.getLogger().addHandler(logging.NullHandler())

# 009653.python.conftest.line28.comment psutil is used for process tree clean-up on time-out when running the test frozen application. If unavailable
# 009654.python.conftest.line29.comment (for example, on cygwin), we fall back to trying to terminate only the main application process.
try:
    import psutil  # noqa: E402
except ModuleNotFoundError:
    psutil = None

import pytest  # noqa: E402

from PyInstaller import __main__ as pyi_main  # noqa: E402
from PyInstaller import configure  # noqa: E402
from PyInstaller.compat import is_cygwin, is_darwin, is_win  # noqa: E402
from PyInstaller.depend.analysis import initialize_modgraph  # noqa: E402
from PyInstaller.archive.readers import pkg_archive_contents  # noqa: E402
from PyInstaller.utils.tests import gen_sourcefile  # noqa: E402
from PyInstaller.utils.win32 import winutils  # noqa: E402

# 009664.python.conftest.line45.comment Timeout for running the executable. If executable does not exit in this time, it is interpreted as a test failure.
_EXE_TIMEOUT = 3 * 60  # In sec.
# 009666.python.conftest.line47.comment All currently supported platforms
SUPPORTED_OSES = {"darwin", "linux", "win32"}
# 009667.python.conftest.line49.comment Have pyi_builder fixure clean-up the temporary directories of successful tests. Controlled by environment variable.
_PYI_BUILDER_CLEANUP = os.environ.get("PYI_BUILDER_CLEANUP", "1") == "1"

# 009668.python.conftest.line52.comment Fixtures
# 009669.python.conftest.line53.comment --------


def pytest_runtest_setup(item):
    """
    Markers to skip tests based on the current platform.
    https://pytest.org/en/stable/example/markers.html#marking-platform-specific-tests-with-pytest

    Available markers: see pytest.ini markers
        - @pytest.mark.darwin (macOS)
        - @pytest.mark.linux (GNU/Linux)
        - @pytest.mark.win32 (Windows)
    """
    supported_platforms = SUPPORTED_OSES.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip(f"does not run on {plat}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # 009670.python.conftest.line74.comment Execute all other hooks to obtain the report object.
    outcome = yield
    rep = outcome.get_result()

    # 009671.python.conftest.line78.comment Set a report attribute for each phase of a call, which can be "setup", "call", "teardown".
    setattr(item, f"rep_{rep.when}", rep)


# 009672.python.conftest.line82.comment Return the base directory which contains the current test module.
def _get_base_dir(request):
    return request.path.resolve().parent  # pathlib.Path instance


# 009674.python.conftest.line87.comment Directory with Python scripts for functional tests.
def _get_script_dir(request):
    return _get_base_dir(request) / 'scripts'


# 009675.python.conftest.line92.comment Directory with testing modules used in some tests.
def _get_modules_dir(request):
    return _get_base_dir(request) / 'modules'


# 009676.python.conftest.line97.comment Directory with .toc log files.
def _get_logs_dir(request):
    return _get_base_dir(request) / 'logs'


# 009677.python.conftest.line102.comment Return the directory where data for tests is located.
def _get_data_dir(request):
    return _get_base_dir(request) / 'data'


# 009678.python.conftest.line107.comment Directory with .spec files used in some tests.
def _get_spec_dir(request):
    return _get_base_dir(request) / 'specs'


@pytest.fixture
def spec_dir(request):
    """
    Return the directory where the test spec-files reside.
    """
    return _get_spec_dir(request)


@pytest.fixture
def script_dir(request):
    """
    Return the directory where the test scripts reside.
    """
    return _get_script_dir(request)


# 009679.python.conftest.line128.comment A fixture that copies test's data directory into test's temporary directory. The data directory is assumed to be
# 009680.python.conftest.line129.comment `data/{test-name}` found next to the .py file that contains test.
@pytest.fixture
def data_dir(
    # 009681.python.conftest.line132.comment The request object for this test. Used to infer name of the test and location of the source .py file.
    # 009682.python.conftest.line133.comment See
    # 009683.python.conftest.line134.comment https://pytest.org/latest/builtin.html#_pytest.python.FixtureRequest
    # 009684.python.conftest.line135.comment and
    # 009685.python.conftest.line136.comment https://pytest.org/latest/fixture.html#fixtures-can-introspect-the-requesting-test-context.
    request,
    # 009686.python.conftest.line138.comment The tmp_path object for this test. See: https://pytest.org/latest/tmp_path.html.
    tmp_path
):
    # 009687.python.conftest.line141.comment Strip the leading 'test_' from the test's name.
    test_name = request.function.__name__[5:]

    # 009688.python.conftest.line144.comment Copy to data dir and return the path.
    source_data_dir = _get_data_dir(request) / test_name
    tmp_data_dir = tmp_path / 'data'
    # 009689.python.conftest.line147.comment Copy the data.
    shutil.copytree(source_data_dir, tmp_data_dir)
    # 009690.python.conftest.line149.comment Return the temporary data directory, so that the copied data can now be used.
    return tmp_data_dir


class AppBuilder:
    def __init__(self, tmp_path, request, bundle_mode):
        self._tmp_path = tmp_path
        self._request = request
        self._mode = bundle_mode
        self._spec_dir = tmp_path
        self._dist_dir = tmp_path / 'dist'
        self._build_dir = tmp_path / 'build'
        self._is_spec = False

    def test_spec(self, specfile, *args, **kwargs):
        """
        Test a Python script that is referenced in the supplied .spec file.
        """
        __tracebackhide__ = True
        specfile = _get_spec_dir(self._request) / specfile
        # 009691.python.conftest.line169.comment 'test_script' should handle .spec properly as script.
        self._is_spec = True
        return self.test_script(specfile, *args, **kwargs)

    def test_source(self, source, *args, **kwargs):
        """
        Test a Python script given as source code.

        The source will be written into a file named like the test-function. This file will then be passed to
        `test_script`. If you need other related file, e.g., as `.toc`-file for testing the content, put it at at the
        normal place. Just mind to take the basnename from the test-function's name.

        :param script: Source code to create executable from. This will be saved into a temporary file which is then
                       passed on to `test_script`.

        :param test_id: Test-id for parametrized tests. If given, it will be appended to the script filename, separated
                        by two underscores.

        All other arguments are passed straight on to `test_script`.
        """
        __tracebackhide__ = True
        # 009692.python.conftest.line190.comment For parametrized test append the test-id.
        scriptfile = gen_sourcefile(self._tmp_path, source, kwargs.setdefault('test_id'))
        del kwargs['test_id']
        return self.test_script(scriptfile, *args, **kwargs)

    def _display_message(self, step_name, message):
        # 009693.python.conftest.line196.comment Print the given message to both stderr and stdout, and it with APP-BUILDER to make it clear where it
        # 009694.python.conftest.line197.comment originates from.
        print(f'[APP-BUILDER:{step_name}] {message}', file=sys.stdout)
        print(f'[APP-BUILDER:{step_name}] {message}', file=sys.stderr)

    def test_script(
        self, script, pyi_args=None, app_name=None, app_args=None, runtime=None, run_from_path=False, **kwargs
    ):
        """
        Main method to wrap all phases of testing a Python script.

        :param script: Name of script to create executable from.
        :param pyi_args: Additional arguments to pass to PyInstaller when creating executable.
        :param app_name: Name of the executable. This is equivalent to argument --name=APPNAME.
        :param app_args: Additional arguments to pass to
        :param runtime: Time in seconds how long to keep executable running.
        :param toc_log: List of modules that are expected to be bundled with the executable.
        """
        __tracebackhide__ = True

        # 009695.python.conftest.line216.comment Skip interactive tests (the ones with `runtime` set) if `psutil` is unavailable, as we need it to properly
        # 009696.python.conftest.line217.comment clean up the process tree.
        if runtime and psutil is None:
            pytest.skip('Interactive tests require psutil for proper cleanup.')

        if pyi_args is None:
            pyi_args = []
        if app_args is None:
            app_args = []

        if app_name:
            if not self._is_spec:
                pyi_args.extend(['--name', app_name])
        else:
            # 009697.python.conftest.line230.comment Derive name from script name.
            app_name = os.path.splitext(os.path.basename(script))[0]

        # 009698.python.conftest.line233.comment Relative path means that a script from _script_dir is referenced.
        if not os.path.isabs(script):
            script = _get_script_dir(self._request) / script
        self.script = str(script)  # might be a pathlib.Path at this point!
        assert os.path.exists(self.script), f'Script {self.script!r} not found.'

        self._display_message('TEST-SCRIPT', 'Starting build...')
        if not self._test_building(args=pyi_args):
            pytest.fail(f'Building of {script} failed.')

        self._display_message('TEST-SCRIPT', 'Build finished, now running executable...')
        self._test_executables(app_name, args=app_args, runtime=runtime, run_from_path=run_from_path, **kwargs)
        self._display_message('TEST-SCRIPT', 'Running executable finished.')

    def _test_executables(self, name, args, runtime, run_from_path, **kwargs):
        """
        Run created executable to make sure it works.

        Multipackage-tests generate more than one exe-file and all of them have to be run.

        :param args: CLI options to pass to the created executable.
        :param runtime: Time in seconds how long to keep the executable running.

        :return: Exit code of the executable.
        """
        __tracebackhide__ = True
        exes = self._find_executables(name)
        # 009700.python.conftest.line260.comment Empty list means that PyInstaller probably failed to create any executable.
        assert exes != [], 'No executable file was found.'
        for exe in exes:
            # 009701.python.conftest.line263.comment Try to find .toc log file. .toc log file has the same basename as exe file.
            toc_log = os.path.splitext(os.path.basename(exe))[0] + '.toc'
            toc_log = _get_logs_dir(self._request) / toc_log
            if toc_log.exists():
                if not self._examine_executable(exe, toc_log):
                    pytest.fail(f'Matching .toc of {exe} failed.')
            retcode = self._run_executable(exe, args, run_from_path, runtime)
            if retcode != kwargs.get('retcode', 0):
                pytest.fail(f'Running exe {exe} failed with return-code {retcode}.')

    def _find_executables(self, name):
        """
        Search for all executables generated by the testcase.

        If the test-case is called e.g. 'test_multipackage1', this is searching for each of 'test_multipackage1.exe'
        and 'multipackage1_?.exe' in both one-file- and one-dir-mode.

        :param name: Name of the executable to look for.

        :return: List of executables
        """
        exes = []
        onedir_pt = str(self._dist_dir / name / name)
        onefile_pt = str(self._dist_dir / name)
        patterns = [
            onedir_pt,
            onefile_pt,
            # 009702.python.conftest.line290.comment Multipackage one-dir
            onedir_pt + '_?',
            # 009703.python.conftest.line292.comment Multipackage one-file
            onefile_pt + '_?'
        ]
        # 009704.python.conftest.line295.comment For Windows append .exe extension to patterns.
        if is_win:
            patterns = [pt + '.exe' for pt in patterns]
        # 009705.python.conftest.line298.comment For macOS append pattern for .app bundles.
        if is_darwin:
            # 009706.python.conftest.line300.comment e.g:  ./dist/name.app/Contents/MacOS/name
            app_bundle_pt = str(self._dist_dir / f'{name}.app' / 'Contents' / 'MacOS' / name)
            patterns.append(app_bundle_pt)
        # 009707.python.conftest.line303.comment Apply file patterns.
        for pattern in patterns:
            for prog in glob.glob(pattern):
                if os.path.isfile(prog):
                    exes.append(prog)
        return exes

    def _run_executable(self, prog, args, run_from_path, runtime):
        """
        Run executable created by PyInstaller.

        :param args: CLI options to pass to the created executable.
        """
        # 009708.python.conftest.line316.comment Run the test in a clean environment to make sure they're really self-contained.
        prog_env = copy.deepcopy(os.environ)
        prog_env['PATH'] = ''
        del prog_env['PATH']
        # 009709.python.conftest.line320.comment For Windows we need to keep minimal PATH for successful running of some tests.
        if is_win:
            # 009710.python.conftest.line322.comment Minimum Windows PATH is in most cases:   C:\Windows\system32;C:\Windows
            prog_env['PATH'] = os.pathsep.join(winutils.get_system_path())
        # 009711.python.conftest.line324.comment Same for Cygwin - if /usr/bin is not in PATH, cygwin1.dll cannot be discovered.
        if is_cygwin:
            prog_env['PATH'] = os.pathsep.join(['/usr/local/bin', '/usr/bin'])
        # 009712.python.conftest.line327.comment On macOS, we similarly set up minimal PATH with system directories, in case utilities from there are used by
        # 009713.python.conftest.line328.comment tested python code (for example, matplotlib >= 3.9.0 uses `system_profiler` that is found in /usr/sbin).
        if is_darwin:
            # 009714.python.conftest.line330.comment The following paths are registered when application is launched via Finder, and are a subset of what is
            # 009715.python.conftest.line331.comment typically available in the shell.
            prog_env['PATH'] = os.pathsep.join(['/usr/bin', '/bin', '/usr/sbin', '/sbin'])

        exe_path = prog
        if run_from_path:
            # 009716.python.conftest.line336.comment Run executable in the temp directory. Add the directory containing the executable to $PATH. Basically,
            # 009717.python.conftest.line337.comment pretend we are a shell executing the program from $PATH.
            prog_cwd = str(self._tmp_path)
            prog_name = os.path.basename(prog)
            prog_env['PATH'] = os.pathsep.join([prog_env.get('PATH', ''), os.path.dirname(prog)])

        else:
            # 009718.python.conftest.line343.comment Run executable in the directory where it is.
            prog_cwd = os.path.dirname(prog)
            # 009719.python.conftest.line345.comment The executable will be called with argv[0] as relative not absolute path.
            prog_name = os.path.join(os.curdir, os.path.basename(prog))

        args = [prog_name] + args
        # 009720.python.conftest.line349.comment Using sys.stdout/sys.stderr for subprocess fixes printing messages in Windows command prompt. Py.test is then
        # 009721.python.conftest.line350.comment able to collect stdout/sterr messages and display them if a test fails.
        return self._run_executable_(args, exe_path, prog_env, prog_cwd, runtime)

    def _run_executable_(self, args, exe_path, prog_env, prog_cwd, runtime):
        # 009722.python.conftest.line354.comment Use psutil.Popen, if available; otherwise, fall back to subprocess.Popen
        popen_implementation = subprocess.Popen if psutil is None else psutil.Popen

        # 009723.python.conftest.line357.comment Run the executable
        self._display_message('RUN-EXE', f'Running {exe_path!r}, args: {args!r}')
        start_time = time.time()
        process = popen_implementation(args, executable=exe_path, env=prog_env, cwd=prog_cwd)

        # 009724.python.conftest.line362.comment Wait for the process to finish. If no run-time (= timeout) is specified, we expect the process to exit on
        # 009725.python.conftest.line363.comment its own, and use global _EXE_TIMEOUT. If run-time is specified, we expect the application to be running
        # 009726.python.conftest.line364.comment for at least the specified amount of time, which is useful in "interactive" test applications that are not
        # 009727.python.conftest.line365.comment expected exit on their own.
        stdout = stderr = None
        try:
            timeout = runtime if runtime else _EXE_TIMEOUT
            stdout, stderr = process.communicate(timeout=timeout)
            elapsed = time.time() - start_time
            retcode = process.returncode
            self._display_message(
                'RUN-EXE', f'Process exited on its own after {elapsed:.1f} seconds with return code {retcode}.'
            )
        except (subprocess.TimeoutExpired) if psutil is None else (psutil.TimeoutExpired, subprocess.TimeoutExpired):
            if runtime:
                # 009728.python.conftest.line377.comment When 'runtime' is set, the expired timeout is a good sign that the executable was running successfully
                # 009729.python.conftest.line378.comment for the specified time.
                self._display_message('RUN-EXE', f'Process reached expected run-time of {runtime} seconds.')
                retcode = 0
            else:
                # 009730.python.conftest.line382.comment Executable is still running and it is not interactive. Clean up the process tree, and fail the test.
                self._display_message('RUN-EXE', f'Timeout while running executable (timeout: {timeout} seconds)!')
                retcode = 1

            if psutil is None:
                # 009731.python.conftest.line387.comment We are using subprocess.Popen(). Without psutil, we have no access to process tree; this poses a
                # 009732.python.conftest.line388.comment problem for onefile builds, where we would need to first kill the child (main application) process,
                # 009733.python.conftest.line389.comment and let the onefile parent perform its cleanup. As a best-effort approach, we can first call
                # 009734.python.conftest.line390.comment process.terminate(); on POSIX systems, this sends SIGTERM to the parent process, and in most
                # 009735.python.conftest.line391.comment situations, the bootloader will forward it to the child process. Then wait 5 seconds, and call
                # 009736.python.conftest.line392.comment process.kill() if necessary. On Windows, however, both process.terminate() and process.kill() do
                # 009737.python.conftest.line393.comment the same. Therefore, we should avoid running "interactive" tests with expected run-time if we do
                # 009738.python.conftest.line394.comment not have psutil available.
                try:
                    self._display_message('RUN-EXE', 'Stopping the process using Popen.terminate()...')
                    process.terminate()
                    stdout, stderr = process.communicate(timeout=5)
                    self._display_message('RUN-EXE', 'Process stopped.')
                except subprocess.TimeoutExpired:
                    # 009739.python.conftest.line401.comment Kill the process.
                    try:
                        self._display_message('RUN-EXE', 'Stopping the process using Popen.kill()...')
                        process.kill()
                        # 009740.python.conftest.line405.comment process.communicate() waits for end-of-file, which may never arrive if there is a child
                        # 009741.python.conftest.line406.comment process still alive. Nothing we can really do about it here, so add a short timeout and
                        # 009742.python.conftest.line407.comment display a warning.
                        stdout, stderr = process.communicate(timeout=1)
                        self._display_message('RUN-EXE', 'Process stopped.')
                    except subprocess.TimeoutExpired:
                        self._display_message('RUN-EXE', 'Failed to stop the process (or its child process(es))!')
            else:
                # 009743.python.conftest.line413.comment We are using psutil.Popen(). First, force-kill all child processes; in onefile mode, this includes
                # 009744.python.conftest.line414.comment the application process, whose termination should trigger cleanup and exit of the parent onefile
                # 009745.python.conftest.line415.comment process.
                self._display_message('RUN-EXE', 'Stopping child processes...')
                for child_process in list(process.children(recursive=True)):
                    with contextlib.suppress(psutil.NoSuchProcess):
                        self._display_message('RUN-EXE', f'Stopping child process {child_process.pid}...')
                        child_process.kill()

                # 009746.python.conftest.line422.comment Give the main process 5 seconds to exit on its own (to accommodate cleanup in onefile mode).
                try:
                    self._display_message('RUN-EXE', f'Waiting for main process ({process.pid}) to stop...')
                    stdout, stderr = process.communicate(timeout=5)
                    self._display_message('RUN-EXE', 'Process stopped on its own.')
                except (psutil.TimeoutExpired, subprocess.TimeoutExpired):
                    # 009747.python.conftest.line428.comment End of the line - kill the main process.
                    self._display_message('RUN-EXE', 'Stopping the process using Popen.kill()...')
                    with contextlib.suppress(psutil.NoSuchProcess):
                        process.kill()
                    # 009748.python.conftest.line432.comment Try to retrieve stdout/stderr - but keep a short timeout, just in case...
                    try:
                        stdout, stderr = process.communicate(timeout=1)
                        self._display_message('RUN-EXE', 'Process stopped.')
                    except (psutil.TimeoutExpired, subprocess.TimeoutExpire):
                        self._display_message('RUN-EXE', 'Failed to stop the process (or its child process(es))!')

        self._display_message('RUN-EXE', f'Done! Return code: {retcode}')

        return retcode

    def _test_building(self, args):
        """
        Run building of test script.

        :param args: additional CLI options for PyInstaller.

        Return True if build succeeded False otherwise.
        """
        if self._is_spec:
            default_args = [
                '--distpath', str(self._dist_dir),
                '--workpath', str(self._build_dir),
                '--log-level', 'INFO',
            ]  # yapf: disable
        else:
            default_args = [
                '--debug=bootloader',
                '--noupx',
                '--specpath', str(self._spec_dir),
                '--distpath', str(self._dist_dir),
                '--workpath', str(self._build_dir),
                '--path', str(_get_modules_dir(self._request)),
                '--log-level', 'INFO',
            ]  # yapf: disable

            # 009751.python.conftest.line468.comment Choose bundle mode.
            if self._mode == 'onedir':
                default_args.append('--onedir')
            elif self._mode == 'onefile':
                default_args.append('--onefile')
            # 009752.python.conftest.line473.comment if self._mode is None then just the spec file was supplied.

        pyi_args = [self.script, *default_args, *args]
        # 009753.python.conftest.line476.comment TODO: fix return code in running PyInstaller programmatically.
        PYI_CONFIG = configure.get_config()
        # 009754.python.conftest.line478.comment Override CACHEDIR for PyInstaller; relocate cache into `self._tmp_path`.
        PYI_CONFIG['cachedir'] = str(self._tmp_path)

        pyi_main.run(pyi_args, PYI_CONFIG)
        retcode = 0

        return retcode == 0

    def _examine_executable(self, exe, toc_log):
        """
        Compare log files (now used mostly by multipackage test_name).

        :return: True if .toc files match
        """
        self._display_message('EXAMINE-EXE', f'Matching against TOC log: {str(toc_log)!r}')
        fname_list = pkg_archive_contents(exe)
        with open(toc_log, 'r', encoding='utf-8') as f:
            pattern_list = eval(f.read())
        # 009755.python.conftest.line496.comment Alphabetical order of patterns.
        pattern_list.sort()
        missing = []
        for pattern in pattern_list:
            for fname in fname_list:
                if re.match(pattern, fname):
                    self._display_message('EXAMINE-EXE', f'Entry found: {pattern!r} --> {fname!r}')
                    break
            else:
                # 009756.python.conftest.line505.comment No matching entry found
                missing.append(pattern)
                self._display_message('EXAMINE-EXE', f'Entry MISSING: {pattern!r}')

        # 009757.python.conftest.line509.comment We expect the missing list to be empty
        return not missing


# 009758.python.conftest.line513.comment Scope 'session' should keep the object unchanged for whole tests. This fixture caches basic module graph dependencies
# 009759.python.conftest.line514.comment that are same for every executable.
@pytest.fixture(scope='session')
def pyi_modgraph():
    # 009760.python.conftest.line517.comment Explicitly set the log level since the plugin `pytest-catchlog` (un-) sets the root logger's level to NOTSET for
    # 009761.python.conftest.line518.comment the setup phase, which will lead to TRACE messages been written out.
    import PyInstaller.log as logging
    logging.logger.setLevel(logging.DEBUG)
    initialize_modgraph()


# 009762.python.conftest.line524.comment Run by default test as onedir and onefile.
@pytest.fixture(params=['onedir', 'onefile'])
def pyi_builder(tmp_path, monkeypatch, request, pyi_modgraph):
    # 009763.python.conftest.line527.comment Save/restore environment variable PATH.
    monkeypatch.setenv('PATH', os.environ['PATH'])
    # 009764.python.conftest.line529.comment PyInstaller or a test case might manipulate 'sys.path'. Reset it for every test.
    monkeypatch.syspath_prepend(None)
    # 009765.python.conftest.line531.comment Set current working directory to
    monkeypatch.chdir(tmp_path)
    # 009766.python.conftest.line533.comment Clean up configuration and force PyInstaller to do a clean configuration for another app/test. The value is same
    # 009767.python.conftest.line534.comment as the original value.
    monkeypatch.setattr('PyInstaller.config.CONF', {'pathex': []})

    yield AppBuilder(tmp_path, request, request.param)

    # 009768.python.conftest.line539.comment Clean up the temporary directory of a successful test
    if _PYI_BUILDER_CLEANUP and request.node.rep_setup.passed and request.node.rep_call.passed:
        if tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)


# 009769.python.conftest.line545.comment Fixture for .spec based tests. With .spec it does not make sense to differentiate onefile/onedir mode.
@pytest.fixture
def pyi_builder_spec(tmp_path, request, monkeypatch, pyi_modgraph):
    # 009770.python.conftest.line548.comment Save/restore environment variable PATH.
    monkeypatch.setenv('PATH', os.environ['PATH'])
    # 009771.python.conftest.line550.comment Set current working directory to
    monkeypatch.chdir(tmp_path)
    # 009772.python.conftest.line552.comment PyInstaller or a test case might manipulate 'sys.path'. Reset it for every test.
    monkeypatch.syspath_prepend(None)
    # 009773.python.conftest.line554.comment Clean up configuration and force PyInstaller to do a clean configuration for another app/test. The value is same
    # 009774.python.conftest.line555.comment as the original value.
    monkeypatch.setattr('PyInstaller.config.CONF', {'pathex': []})

    yield AppBuilder(tmp_path, request, None)

    # 009775.python.conftest.line560.comment Clean up the temporary directory of a successful test
    if _PYI_BUILDER_CLEANUP and request.node.rep_setup.passed and request.node.rep_call.passed:
        if tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def pyi_windowed_builder(pyi_builder: AppBuilder):
    """A pyi_builder equivalent for testing --windowed applications."""

    # 009776.python.conftest.line570.comment psutil.Popen() somehow bypasses an application's windowed/console mode so that any application built in
    # 009777.python.conftest.line571.comment --windowed mode but invoked with psutil still receives valid std{in,out,err} handles and behaves exactly like
    # 009778.python.conftest.line572.comment a console application. In short, testing windowed mode with psutil is a null test. We must instead use subprocess.

    def _run_executable_(args, exe_path, prog_env, prog_cwd, runtime):
        return subprocess.run([exe_path, *args], env=prog_env, cwd=prog_cwd, timeout=runtime).returncode

    pyi_builder._run_executable_ = _run_executable_
    yield pyi_builder
