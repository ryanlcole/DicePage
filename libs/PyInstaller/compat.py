# 001708.python.compat.line1.comment ----------------------------------------------------------------------------
# 001709.python.compat.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 001710.python.compat.line3.comment
# 001711.python.compat.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 001712.python.compat.line5.comment or later) with exception for distributing the bootloader.
# 001713.python.compat.line6.comment
# 001714.python.compat.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 001715.python.compat.line8.comment
# 001716.python.compat.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 001717.python.compat.line10.comment ----------------------------------------------------------------------------
"""
Various classes and functions to provide some backwards-compatibility with previous versions of Python onward.
"""
from __future__ import annotations

import errno

import importlib.machinery
import importlib.util
import os
import platform
import site
import subprocess
import sys
import sysconfig
import shutil
import types

from PyInstaller._shared_with_waf import _pyi_machine
from PyInstaller.exceptions import ExecCommandFailed

# 001718.python.compat.line32.comment hatch_build.py sets this environment variable to avoid errors due to unmet run-time dependencies. The
# 001719.python.compat.line33.comment PyInstaller.compat module is imported by hatch_build.py to build wheels, and some dependencies that are otherwise
# 001720.python.compat.line34.comment required at run-time (importlib-metadata on python < 3.10, pywin32-ctypes on Windows) might not be present while
# 001721.python.compat.line35.comment building wheels, nor are they required during that phase.
_setup_py_mode = os.environ.get('_PYINSTALLER_SETUP', '0') != '0'

# 001722.python.compat.line38.comment PyInstaller requires importlib.metadata from python >= 3.10 stdlib, or equivalent importlib-metadata >= 4.6.
if _setup_py_mode:
    importlib_metadata = None
else:
    if sys.version_info >= (3, 10):
        import importlib.metadata as importlib_metadata
    else:
        try:
            import importlib_metadata
        except ImportError as e:
            from PyInstaller.exceptions import ImportlibMetadataError
            raise ImportlibMetadataError() from e

        import packaging.version  # For importlib_metadata version check

        # 001724.python.compat.line53.comment Validate the version
        if packaging.version.parse(importlib_metadata.version("importlib-metadata")) < packaging.version.parse("4.6"):
            from PyInstaller.exceptions import ImportlibMetadataError
            raise ImportlibMetadataError()

# 001725.python.compat.line58.comment Strict collect mode, which raises error when trying to collect duplicate files into PKG/CArchive or COLLECT.
strict_collect_mode = os.environ.get("PYINSTALLER_STRICT_COLLECT_MODE", "0") != "0"

# 001726.python.compat.line61.comment Copied from https://docs.python.org/3/library/platform.html#cross-platform.
is_64bits: bool = sys.maxsize > 2**32

# 001727.python.compat.line64.comment Distinguish specific code for various Python versions. Variables 'is_pyXY' mean that Python X.Y and up is supported.
# 001728.python.compat.line65.comment Keep even unsupported versions here to keep 3rd-party hooks working.
is_py35 = sys.version_info >= (3, 5)
is_py36 = sys.version_info >= (3, 6)
is_py37 = sys.version_info >= (3, 7)
is_py38 = sys.version_info >= (3, 8)
is_py39 = sys.version_info >= (3, 9)
is_py310 = sys.version_info >= (3, 10)
is_py311 = sys.version_info >= (3, 11)
is_py312 = sys.version_info >= (3, 12)
is_py313 = sys.version_info >= (3, 13)
is_py314 = sys.version_info >= (3, 14)

is_win = sys.platform.startswith('win')
is_win_10 = is_win and (platform.win32_ver()[0] == '10')
is_win_11 = is_win and (platform.win32_ver()[0] == '11')
is_win_wine = False  # Running under Wine; determined later on.
is_cygwin = sys.platform == 'cygwin'
is_darwin = sys.platform == 'darwin'  # macOS

# 001731.python.compat.line84.comment Unix platforms
is_linux = sys.platform.startswith('linux')
is_solar = sys.platform.startswith('sun')  # Solaris
is_aix = sys.platform.startswith('aix')
is_freebsd = sys.platform.startswith('freebsd')
is_openbsd = sys.platform.startswith('openbsd')
is_hpux = sys.platform.startswith('hp-ux')

# 001733.python.compat.line92.comment Some code parts are similar to several unix platforms (e.g. Linux, Solaris, AIX).
# 001734.python.compat.line93.comment macOS is not considered as unix since there are many platform-specific details for Mac in PyInstaller.
is_unix = is_linux or is_solar or is_aix or is_freebsd or is_hpux or is_openbsd

# 001735.python.compat.line96.comment Linux distributions such as Alpine or OpenWRT use musl as their libc implementation and resultantly need specially
# 001736.python.compat.line97.comment compiled bootloaders. On musl systems, ldd with no arguments prints 'musl' and its version.
is_musl = is_linux and "musl" in subprocess.run(["ldd"], capture_output=True, encoding="utf-8").stderr

# 001737.python.compat.line100.comment Termux - terminal emulator and Linux environment app for Android.
is_termux = is_linux and hasattr(sys, 'getandroidapilevel')

# 001738.python.compat.line103.comment macOS version
_macos_ver = tuple(int(x) for x in platform.mac_ver()[0].split('.')) if is_darwin else None

# 001739.python.compat.line106.comment macOS 11 (Big Sur): if python is not compiled with Big Sur support, it ends up in compatibility mode by default, which
# 001740.python.compat.line107.comment is indicated by platform.mac_ver() returning '10.16'. The lack of proper Big Sur support breaks find_library()
# 001741.python.compat.line108.comment function from ctypes.util module, as starting with Big Sur, shared libraries are not visible on disk anymore. Support
# 001742.python.compat.line109.comment for the new library search mechanism was added in python 3.9 when compiled with Big Sur support. In such cases,
# 001743.python.compat.line110.comment platform.mac_ver() reports version as '11.x'. The behavior can be further modified via SYSTEM_VERSION_COMPAT
# 001744.python.compat.line111.comment environment variable; which allows explicitly enabling or disabling the compatibility mode. However, note that
# 001745.python.compat.line112.comment disabling the compatibility mode and using python that does not properly support Big Sur still leaves find_library()
# 001746.python.compat.line113.comment broken (which is a scenario that we ignore at the moment).
# 001747.python.compat.line114.comment The same logic applies to macOS 12 (Monterey).
is_macos_11_compat = bool(_macos_ver) and _macos_ver[0:2] == (10, 16)  # Big Sur or newer in compat mode
is_macos_11_native = bool(_macos_ver) and _macos_ver[0:2] >= (11, 0)  # Big Sur or newer in native mode
is_macos_11 = is_macos_11_compat or is_macos_11_native  # Big Sur or newer

# 001751.python.compat.line119.comment Check if python >= 3.13 was built with Py_GIL_DISABLED / free-threading (PEP703).
# 001752.python.compat.line120.comment
# 001753.python.compat.line121.comment This affects the shared library name, which has the "t" ABI suffix, as per:
# 001754.python.compat.line122.comment https://github.com/python/steering-council/issues/221#issuecomment-1841593283
# 001755.python.compat.line123.comment
# 001756.python.compat.line124.comment It also affects the layout of PyConfig structure used by bootloader; consequently we need to inform bootloader what
# 001757.python.compat.line125.comment kind of build it is dealing with (only in python 3.13; with 3.14 and later, we use PEP741 configuration API in the
# 001758.python.compat.line126.comment bootloader, and do not need to know the layout of PyConfig structure anymore)
is_nogil = bool(sysconfig.get_config_var('Py_GIL_DISABLED'))

# 001759.python.compat.line129.comment In a virtual environment created by virtualenv (github.com/pypa/virtualenv) there exists sys.real_prefix with the path
# 001760.python.compat.line130.comment to the base Python installation from which the virtual environment was created. This is true regardless of the version
# 001761.python.compat.line131.comment of Python used to execute the virtualenv command.
# 001762.python.compat.line132.comment
# 001763.python.compat.line133.comment In a virtual environment created by the venv module available in the Python standard lib, there exists sys.base_prefix
# 001764.python.compat.line134.comment with the path to the base implementation. This does not exist in a virtual environment created by virtualenv.
# 001765.python.compat.line135.comment
# 001766.python.compat.line136.comment The following code creates compat.is_venv and is.virtualenv that are True when running a virtual environment, and also
# 001767.python.compat.line137.comment compat.base_prefix with the path to the base Python installation.

base_prefix: str = os.path.abspath(getattr(sys, 'real_prefix', getattr(sys, 'base_prefix', sys.prefix)))
# 001768.python.compat.line140.comment Ensure `base_prefix` is not containing any relative parts.
is_venv = is_virtualenv = base_prefix != os.path.abspath(sys.prefix)

# 001769.python.compat.line143.comment Conda environments sometimes have different paths or apply patches to packages that can affect how a hook or package
# 001770.python.compat.line144.comment should access resources. Method for determining conda taken from https://stackoverflow.com/questions/47610844#47610844
is_conda = os.path.isdir(os.path.join(base_prefix, 'conda-meta'))

# 001771.python.compat.line147.comment Similar to ``is_conda`` but is ``False`` using another ``venv``-like manager on top. In this case, no packages
# 001772.python.compat.line148.comment encountered will be conda packages meaning that the default non-conda behaviour is generally desired from PyInstaller.
is_pure_conda = os.path.isdir(os.path.join(sys.prefix, 'conda-meta'))

# 001773.python.compat.line151.comment Full path to python interpreter.
python_executable = getattr(sys, '_base_executable', sys.executable)

# 001774.python.compat.line154.comment Is this Python from Microsoft App Store (Windows only)? Python from Microsoft App Store has executable pointing at
# 001775.python.compat.line155.comment empty shims.
is_ms_app_store = is_win and os.path.getsize(python_executable) == 0

if is_ms_app_store:
    # 001776.python.compat.line159.comment Locate the actual executable inside base_prefix.
    python_executable = os.path.join(base_prefix, os.path.basename(python_executable))
    if not os.path.exists(python_executable):
        raise SystemExit(
            'ERROR: PyInstaller cannot locate real python executable belonging to Python from Microsoft App Store!'
        )

# 001777.python.compat.line166.comment Bytecode magic value
BYTECODE_MAGIC = importlib.util.MAGIC_NUMBER

# 001778.python.compat.line169.comment List of suffixes for Python C extension modules.
EXTENSION_SUFFIXES = importlib.machinery.EXTENSION_SUFFIXES
ALL_SUFFIXES = importlib.machinery.all_suffixes()

# 001779.python.compat.line173.comment On Windows we require pywin32-ctypes.
# 001780.python.compat.line174.comment -> all pyinstaller modules should use win32api from PyInstaller.compat to
# 001781.python.compat.line175.comment ensure that it can work on MSYS2 (which requires pywin32-ctypes)
if is_win:
    if _setup_py_mode:
        pywintypes = None
        win32api = None
    else:
        try:
            # 001782.python.compat.line182.comment Hide the `cffi` package from win32-ctypes by temporarily blocking its import. This ensures that `ctypes`
            # 001783.python.compat.line183.comment backend is always used, even if `cffi` is available. The `cffi` backend uses `pycparser`, which is
            # 001784.python.compat.line184.comment incompatible with -OO mode (2nd optimization level) due to its removal of docstrings.
            # 001785.python.compat.line185.comment See https://github.com/pyinstaller/pyinstaller/issues/6345
            # 001786.python.compat.line186.comment On the off chance that `cffi` has already been imported, store the `sys.modules` entry so we can restore
            # 001787.python.compat.line187.comment it after importing `pywin32-ctypes` modules.
            orig_cffi = sys.modules.get('cffi')
            sys.modules['cffi'] = None

            from win32ctypes.pywin32 import pywintypes  # noqa: F401, E402
            from win32ctypes.pywin32 import win32api  # noqa: F401, E402
        except ImportError as e:
            raise SystemExit(
                'ERROR: Could not import `pywintypes` or `win32api` from `win32ctypes.pywin32`.\n'
                'Please make sure that `pywin32-ctypes` is installed and importable, for example:\n\n'
                'pip install pywin32-ctypes\n'
            ) from e
        finally:
            # 001790.python.compat.line200.comment Unblock `cffi`.
            if orig_cffi is not None:
                sys.modules['cffi'] = orig_cffi
            else:
                del sys.modules['cffi']
            del orig_cffi

# 001791.python.compat.line207.comment macOS's platform.architecture() can be buggy, so we do this manually here. Based off the python documentation:
# 001792.python.compat.line208.comment https://docs.python.org/3/library/platform.html#platform.architecture
if is_darwin:
    architecture = '64bit' if sys.maxsize > 2**32 else '32bit'
else:
    architecture = platform.architecture()[0]

# 001793.python.compat.line214.comment Cygwin needs special handling, because platform.system() contains identifiers such as MSYS_NT-10.0-19042 and
# 001794.python.compat.line215.comment CYGWIN_NT-10.0-19042 that do not fit PyInstaller's OS naming scheme. Explicitly set `system` to 'Cygwin'.
system = 'Cygwin' if is_cygwin else platform.system()

# 001795.python.compat.line218.comment Machine suffix for bootloader.
if is_win:
    # 001796.python.compat.line220.comment On Windows ARM64 using an x64 Python environment, platform.machine() returns ARM64 but
    # 001797.python.compat.line221.comment we really want the bootloader that matches the Python environment instead of the OS.
    machine = _pyi_machine(os.environ.get("PROCESSOR_ARCHITECTURE", platform.machine()), platform.system())
else:
    machine = _pyi_machine(platform.machine(), platform.system())


# 001798.python.compat.line227.comment Wine detection and support
def is_wine_dll(filename: str | os.PathLike):
    """
    Check if the given PE file is a Wine DLL (PE-converted built-in, or fake/placeholder one).

    Returns True if the given file is a Wine DLL, False if not (or if file cannot be analyzed or does not exist).
    """
    _WINE_SIGNATURES = (
        b'Wine builtin DLL',  # PE-converted Wine DLL
        b'Wine placeholder DLL',  # Fake/placeholder Wine DLL
    )
    _MAX_LEN = max([len(sig) for sig in _WINE_SIGNATURES])

    # 001801.python.compat.line240.comment Wine places their DLL signature in the padding area between the IMAGE_DOS_HEADER and IMAGE_NT_HEADERS. So we need
    # 001802.python.compat.line241.comment to compare the bytes that come right after IMAGE_DOS_HEADER, i.e., after initial 64 bytes. We can read the file
    # 001803.python.compat.line242.comment directly and avoid using the pefile library to avoid performance penalty associated with full header parsing.
    try:
        with open(filename, 'rb') as fp:
            fp.seek(64)
            signature = fp.read(_MAX_LEN)
        return signature.startswith(_WINE_SIGNATURES)
    except Exception:
        pass
    return False


if is_win:
    try:
        import ctypes.util  # noqa: E402
        is_win_wine = is_wine_dll(ctypes.util.find_library('kernel32'))
    except Exception:
        pass

# 001805.python.compat.line260.comment Set and get environment variables does not handle unicode strings correctly on Windows.

# 001806.python.compat.line262.comment Acting on os.environ instead of using getenv()/setenv()/unsetenv(), as suggested in
# 001807.python.compat.line263.comment <http://docs.python.org/library/os.html#os.environ>: "Calling putenv() directly does not change os.environ, so it is
# 001808.python.compat.line264.comment better to modify os.environ." (Same for unsetenv.)


def getenv(name: str, default: str | None = None):
    """
    Returns unicode string containing value of environment variable 'name'.
    """
    return os.environ.get(name, default)


def setenv(name: str, value: str):
    """
    Accepts unicode string and set it as environment variable 'name' containing value 'value'.
    """
    os.environ[name] = value


def unsetenv(name: str):
    """
    Delete the environment variable 'name'.
    """
    # 001809.python.compat.line285.comment Some platforms (e.g., AIX) do not support `os.unsetenv()` and thus `del os.environ[name]` has no effect on the
    # 001810.python.compat.line286.comment real environment. For this case, we set the value to the empty string.
    os.environ[name] = ""
    del os.environ[name]


# 001811.python.compat.line291.comment Exec commands in subprocesses.


def exec_command(
    *cmdargs: str, encoding: str | None = None, raise_enoent: bool | None = None, **kwargs: int | bool | list | None
):
    """
    Run the command specified by the passed positional arguments, optionally configured by the passed keyword arguments.

    .. DANGER::
       **Ignore this function's return value** -- unless this command's standard output contains _only_ pathnames, in
       which case this function returns the correct filesystem-encoded string expected by PyInstaller. In all other
       cases, this function's return value is _not_ safely usable.

       For backward compatibility, this function's return value non-portably depends on the current Python version and
       passed keyword arguments:

       * Under Python 3.x, this value is a **decoded `str` string**. However, even this value is _not_ necessarily
         safely usable:
         * If the `encoding` parameter is passed, this value is guaranteed to be safely usable.
         * Else, this value _cannot_ be safely used for any purpose (e.g., string manipulation or parsing), except to be
           passed directly to another non-Python command. Why? Because this value has been decoded with the encoding
           specified by `sys.getfilesystemencoding()`, the encoding used by `os.fsencode()` and `os.fsdecode()` to
           convert from platform-agnostic to platform-specific pathnames. This is _not_ necessarily the encoding with
           which this command's standard output was encoded. Cue edge-case decoding exceptions.

    Parameters
    ----------
    cmdargs :
        Variadic list whose:
        1. Mandatory first element is the absolute path, relative path, or basename in the current `${PATH}` of the
           command to run.
        2. Optional remaining elements are arguments to pass to this command.
    encoding : str, optional
        Optional keyword argument specifying the encoding with which to decode this command's standard output under
        Python 3. As this function's return value should be ignored, this argument should _never_ be passed.
    raise_enoent : boolean, optional
        Optional keyword argument to simply raise the exception if the executing the command fails since to the command
        is not found. This is useful to checking id a command exists.

    All remaining keyword arguments are passed as is to the `subprocess.Popen()` constructor.

    Returns
    ----------
    str
        Ignore this value. See discussion above.
    """

    proc = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, **kwargs)
    try:
        out = proc.communicate(timeout=60)[0]
    except OSError as e:
        if raise_enoent and e.errno == errno.ENOENT:
            raise
        print('--' * 20, file=sys.stderr)
        print("Error running '%s':" % " ".join(cmdargs), file=sys.stderr)
        print(e, file=sys.stderr)
        print('--' * 20, file=sys.stderr)
        raise ExecCommandFailed("ERROR: Executing command failed!") from e
    except subprocess.TimeoutExpired:
        proc.kill()
        raise

    # 001812.python.compat.line354.comment stdout/stderr are returned as a byte array NOT as string, so we need to convert that to proper encoding.
    try:
        if encoding:
            out = out.decode(encoding)
        else:
            # 001813.python.compat.line359.comment If no encoding is given, assume we are reading filenames from stdout only because it is the common case.
            out = os.fsdecode(out)
    except UnicodeDecodeError as e:
        # 001814.python.compat.line362.comment The sub-process used a different encoding; provide more information to ease debugging.
        print('--' * 20, file=sys.stderr)
        print(str(e), file=sys.stderr)
        print('These are the bytes around the offending byte:', file=sys.stderr)
        print('--' * 20, file=sys.stderr)
        raise
    return out


def exec_command_rc(*cmdargs: str, **kwargs: float | bool | list | None):
    """
    Return the exit code of the command specified by the passed positional arguments, optionally configured by the
    passed keyword arguments.

    Parameters
    ----------
    cmdargs : list
        Variadic list whose:
        1. Mandatory first element is the absolute path, relative path, or basename in the current `${PATH}` of the
           command to run.
        2. Optional remaining elements are arguments to pass to this command.

    All keyword arguments are passed as is to the `subprocess.call()` function.

    Returns
    ----------
    int
        This command's exit code as an unsigned byte in the range `[0, 255]`, where 0 signifies success and all other
        values signal a failure.
    """

    # 001815.python.compat.line393.comment 'encoding' keyword is not supported for 'subprocess.call'; remove it from kwargs.
    if 'encoding' in kwargs:
        kwargs.pop('encoding')
    return subprocess.call(cmdargs, **kwargs)


def exec_command_all(*cmdargs: str, encoding: str | None = None, **kwargs: int | bool | list | None):
    """
    Run the command specified by the passed positional arguments, optionally configured by the passed keyword arguments.

    .. DANGER::
       **Ignore this function's return value.** If this command's standard output consists solely of pathnames, consider
       calling `exec_command()`

    Parameters
    ----------
    cmdargs : str
        Variadic list whose:
        1. Mandatory first element is the absolute path, relative path, or basename in the current `${PATH}` of the
           command to run.
        2. Optional remaining elements are arguments to pass to this command.
    encoding : str, optional
        Optional keyword argument specifying the encoding with which to decode this command's standard output. As this
        function's return value should be ignored, this argument should _never_ be passed.

    All remaining keyword arguments are passed as is to the `subprocess.Popen()` constructor.

    Returns
    ----------
    (int, str, str)
        Ignore this 3-element tuple `(exit_code, stdout, stderr)`. See the `exec_command()` function for discussion.
    """
    proc = subprocess.Popen(
        cmdargs,
        bufsize=-1,  # Default OS buffer size.
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs
    )
    # 001817.python.compat.line432.comment Waits for subprocess to complete.
    try:
        out, err = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise
    # 001818.python.compat.line438.comment stdout/stderr are returned as a byte array NOT as string. Thus we need to convert that to proper encoding.
    try:
        if encoding:
            out = out.decode(encoding)
            err = err.decode(encoding)
        else:
            # 001819.python.compat.line444.comment If no encoding is given, assume we're reading filenames from stdout only because it's the common case.
            out = os.fsdecode(out)
            err = os.fsdecode(err)
    except UnicodeDecodeError as e:
        # 001820.python.compat.line448.comment The sub-process used a different encoding, provide more information to ease debugging.
        print('--' * 20, file=sys.stderr)
        print(str(e), file=sys.stderr)
        print('These are the bytes around the offending byte:', file=sys.stderr)
        print('--' * 20, file=sys.stderr)
        raise

    return proc.returncode, out, err


def __wrap_python(args, kwargs):
    cmdargs = [sys.executable]

    # 001821.python.compat.line461.comment macOS supports universal binaries (binary for multiple architectures. We need to ensure that subprocess
    # 001822.python.compat.line462.comment binaries are running for the same architecture as python executable. It is necessary to run binaries with 'arch'
    # 001823.python.compat.line463.comment command.
    if is_darwin:
        if architecture == '64bit':
            if platform.machine() == 'arm64':
                py_prefix = ['arch', '-arm64']  # Apple M1
            else:
                py_prefix = ['arch', '-x86_64']  # Intel
        elif architecture == '32bit':
            py_prefix = ['arch', '-i386']
        else:
            py_prefix = []
        # 001826.python.compat.line474.comment Since macOS 10.11, the environment variable DYLD_LIBRARY_PATH is no more inherited by child processes, so we
        # 001827.python.compat.line475.comment proactively propagate the current value using the `-e` option of the `arch` command.
        if 'DYLD_LIBRARY_PATH' in os.environ:
            path = os.environ['DYLD_LIBRARY_PATH']
            py_prefix += ['-e', 'DYLD_LIBRARY_PATH=%s' % path]
        cmdargs = py_prefix + cmdargs

    if not __debug__:
        cmdargs.append('-O')

    cmdargs.extend(args)

    env = kwargs.get('env')
    if env is None:
        env = dict(**os.environ)

    # 001828.python.compat.line490.comment Ensure python 3 subprocess writes 'str' as utf-8
    env['PYTHONIOENCODING'] = 'UTF-8'
    # 001829.python.compat.line492.comment ... and ensure we read output as utf-8
    kwargs['encoding'] = 'UTF-8'

    return cmdargs, kwargs


def exec_python(*args: str, **kwargs: str | None):
    """
    Wrap running python script in a subprocess.

    Return stdout of the invoked command.
    """
    cmdargs, kwargs = __wrap_python(args, kwargs)
    return exec_command(*cmdargs, **kwargs)


def exec_python_rc(*args: str, **kwargs: str | None):
    """
    Wrap running python script in a subprocess.

    Return exit code of the invoked command.
    """
    cmdargs, kwargs = __wrap_python(args, kwargs)
    return exec_command_rc(*cmdargs, **kwargs)


# 001830.python.compat.line518.comment Path handling.


# 001831.python.compat.line521.comment Site-packages functions - use native function if available.
def getsitepackages(prefixes: list | None = None):
    """
    Returns a list containing all global site-packages directories.

    For each directory present in ``prefixes`` (or the global ``PREFIXES``), this function finds its `site-packages`
    subdirectory depending on the system environment, and returns a list of full paths.
    """
    # 001832.python.compat.line529.comment This implementation was copied from the ``site`` module, python 3.7.3.
    sitepackages = []
    seen = set()

    if prefixes is None:
        prefixes = [sys.prefix, sys.exec_prefix]

    for prefix in prefixes:
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)

        if os.sep == '/':
            sitepackages.append(os.path.join(prefix, "lib", "python%d.%d" % sys.version_info[:2], "site-packages"))
        else:
            sitepackages.append(prefix)
            sitepackages.append(os.path.join(prefix, "lib", "site-packages"))
    return sitepackages


# 001833.python.compat.line549.comment Backported for virtualenv. Module 'site' in virtualenv might not have this attribute.
getsitepackages = getattr(site, 'getsitepackages', getsitepackages)


# 001834.python.compat.line553.comment Wrapper to load a module from a Python source file. This function loads import hooks when processing them.
def importlib_load_source(name: str, pathname: str):
    # 001835.python.compat.line555.comment Import module from a file.
    mod_loader = importlib.machinery.SourceFileLoader(name, pathname)
    mod = types.ModuleType(mod_loader.name)
    mod.__file__ = mod_loader.get_filename()  # Some hooks require __file__ attribute in their namespace
    mod_loader.exec_module(mod)
    return mod


# 001837.python.compat.line563.comment Patterns of module names that should be bundled into the base_library.zip to be available during bootstrap.
# 001838.python.compat.line564.comment These modules include direct or indirect dependencies of encodings.* modules. The encodings modules must be
# 001839.python.compat.line565.comment recursively included to set the I/O encoding during python startup. Similarly, this list should include
# 001840.python.compat.line566.comment modules used by PyInstaller's bootstrap scripts and modules (loader/pyi*.py)

PY3_BASE_MODULES = {
    '_collections_abc',
    '_weakrefset',
    'abc',
    'codecs',
    'collections',
    'copyreg',
    'encodings',
    'enum',
    'functools',
    'genericpath',  # dependency of os.path
    'io',
    'heapq',
    'keyword',
    'linecache',
    'locale',
    'ntpath',  # dependency of os.path
    'operator',
    'os',
    'posixpath',  # dependency of os.path
    're',
    'reprlib',
    'sre_compile',
    'sre_constants',
    'sre_parse',
    'stat',  # dependency of os.path
    'traceback',  # for startup errors
    'types',
    'weakref',
    'warnings',
}

if not is_py310:
    PY3_BASE_MODULES.add('_bootlocale')

# 001846.python.compat.line603.comment Object types of Pure Python modules in modulegraph dependency graph.
# 001847.python.compat.line604.comment Pure Python modules have code object (attribute co_code).
PURE_PYTHON_MODULE_TYPES = {
    'SourceModule',
    'CompiledModule',
    'Package',
    'NamespacePackage',
    # 001848.python.compat.line610.comment Deprecated.
    # 001849.python.compat.line611.comment TODO Could these module types be removed?
    'FlatPackage',
    'ArchiveModule',
}
# 001850.python.compat.line615.comment Object types of special Python modules (built-in, run-time, namespace package) in modulegraph dependency graph that do
# 001851.python.compat.line616.comment not have code object.
SPECIAL_MODULE_TYPES = {
    # 001852.python.compat.line618.comment Omit AliasNode from here (and consequently from VALID_MODULE_TYPES), in order to prevent PyiModuleGraph from
    # 001853.python.compat.line619.comment running standard hooks for aliased modules.
    # 001854.python.compat.line620.comment 'AliasNode',
    'BuiltinModule',
    'RuntimeModule',
    'RuntimePackage',

    # 001855.python.compat.line625.comment PyInstaller handles scripts differently and not as standard Python modules.
    'Script',
}
# 001856.python.compat.line628.comment Object types of Binary Python modules (extensions, etc) in modulegraph dependency graph.
BINARY_MODULE_TYPES = {
    'Extension',
    'ExtensionPackage',
}
# 001857.python.compat.line633.comment Object types of valid Python modules in modulegraph dependency graph.
VALID_MODULE_TYPES = PURE_PYTHON_MODULE_TYPES | SPECIAL_MODULE_TYPES | BINARY_MODULE_TYPES
# 001858.python.compat.line635.comment Object types of bad/missing/invalid Python modules in modulegraph dependency graph.
# 001859.python.compat.line636.comment TODO: should be 'Invalid' module types also in the 'MISSING' set?
BAD_MODULE_TYPES = {
    'BadModule',
    'ExcludedModule',
    'InvalidSourceModule',
    'InvalidCompiledModule',
    'MissingModule',

    # 001860.python.compat.line644.comment Runtime modules and packages are technically valid rather than bad, but exist only in-memory rather than on-disk
    # 001861.python.compat.line645.comment (typically due to pre_safe_import_module() hooks), and hence cannot be physically frozen. For simplicity, these
    # 001862.python.compat.line646.comment nodes are categorized as bad rather than valid.
    'RuntimeModule',
    'RuntimePackage',
}
ALL_MODULE_TYPES = VALID_MODULE_TYPES | BAD_MODULE_TYPES
# 001863.python.compat.line651.comment TODO: review this mapping to TOC, remove useless entries.
# 001864.python.compat.line652.comment Dictionary to map ModuleGraph node types to TOC typecodes.
MODULE_TYPES_TO_TOC_DICT = {
    # 001865.python.compat.line654.comment Pure modules.
    'AliasNode': 'PYMODULE',
    'Script': 'PYSOURCE',
    'SourceModule': 'PYMODULE',
    'CompiledModule': 'PYMODULE',
    'Package': 'PYMODULE',
    'FlatPackage': 'PYMODULE',
    'ArchiveModule': 'PYMODULE',
    # 001866.python.compat.line662.comment Binary modules.
    'Extension': 'EXTENSION',
    'ExtensionPackage': 'EXTENSION',
    # 001867.python.compat.line665.comment Special valid modules.
    'BuiltinModule': 'BUILTIN',
    'NamespacePackage': 'PYMODULE',
    # 001868.python.compat.line668.comment Bad modules.
    'BadModule': 'bad',
    'ExcludedModule': 'excluded',
    'InvalidSourceModule': 'invalid',
    'InvalidCompiledModule': 'invalid',
    'MissingModule': 'missing',
    'RuntimeModule': 'runtime',
    'RuntimePackage': 'runtime',
    # 001869.python.compat.line676.comment Other.
    'does not occur': 'BINARY',
}


def check_requirements():
    """
    Verify that all requirements to run PyInstaller are met.

    Fail hard if any requirement is not met.
    """
    # 001870.python.compat.line687.comment Fail hard if Python does not have minimum required version
    if sys.version_info < (3, 8):
        raise EnvironmentError('PyInstaller requires Python 3.8 or newer.')

    # 001871.python.compat.line691.comment There are some old packages which used to be backports of libraries which are now part of the standard library.
    # 001872.python.compat.line692.comment These backports are now unmaintained and contain only an older subset of features leading to obscure errors like
    # 001873.python.compat.line693.comment "enum has not attribute IntFlag" if installed.
    from importlib.metadata import distribution, PackageNotFoundError

    for name in ["enum34", "typing", "pathlib"]:
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            continue
        remove = "conda remove" if is_conda else f'"{sys.executable}" -m pip uninstall {name}'
        raise SystemExit(
            f"ERROR: The '{name}' package is an obsolete backport of a standard library package and is incompatible "
            f"with PyInstaller. Please remove this package (located in {dist.locate_file('')}) using\n    {remove}\n"
            "then try again."
        )

    # 001874.python.compat.line708.comment Bail out if binutils is not installed.
    if is_linux and shutil.which("objdump") is None:
        raise SystemExit(
            "ERROR: On Linux, objdump is required. It is typically provided by the 'binutils' package "
            "installable via your Linux distribution's package manager."
        )
