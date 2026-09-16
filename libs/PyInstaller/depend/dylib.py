# 002473.python.dylib.line1.comment -----------------------------------------------------------------------------
# 002474.python.dylib.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 002475.python.dylib.line3.comment
# 002476.python.dylib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 002477.python.dylib.line5.comment or later) with exception for distributing the bootloader.
# 002478.python.dylib.line6.comment
# 002479.python.dylib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 002480.python.dylib.line8.comment
# 002481.python.dylib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 002482.python.dylib.line10.comment -----------------------------------------------------------------------------
"""
Manipulating with dynamic libraries.
"""

import os
import pathlib
import re

from PyInstaller import compat
import PyInstaller.log as logging

logger = logging.getLogger(__name__)

# 002483.python.dylib.line24.comment Ignoring some system libraries speeds up packaging process
_excludes = {
    # 002484.python.dylib.line26.comment Ignore annoying warnings with Windows system DLLs.
    # 002485.python.dylib.line27.comment
    # 002486.python.dylib.line28.comment 'W: library kernel32.dll required via ctypes not found'
    # 002487.python.dylib.line29.comment 'W: library coredll.dll required via ctypes not found'
    # 002488.python.dylib.line30.comment
    # 002489.python.dylib.line31.comment These these dlls has to be ignored for all operating systems because they might be resolved when scanning code for
    # 002490.python.dylib.line32.comment ctypes dependencies.
    r'advapi32\.dll',
    r'ws2_32\.dll',
    r'gdi32\.dll',
    r'oleaut32\.dll',
    r'shell32\.dll',
    r'ole32\.dll',
    r'coredll\.dll',
    r'crypt32\.dll',
    r'kernel32',
    r'kernel32\.dll',
    r'msvcrt\.dll',
    r'rpcrt4\.dll',
    r'user32\.dll',
    # 002491.python.dylib.line46.comment Some modules tries to import the Python library. e.g. pyreadline.console.console
    r'python\%s\%s',
}

# 002492.python.dylib.line50.comment Regex includes - overrides excludes. Include list is used only to override specific libraries from exclude list.
_includes = set()

_win_includes = {
    # 002493.python.dylib.line54.comment We need to allow collection of Visual Studio C++ (VC) runtime DLLs from system directories in order to avoid
    # 002494.python.dylib.line55.comment missing DLL errors when the frozen application is run on a system that does not have the corresponding VC
    # 002495.python.dylib.line56.comment runtime installed. The VC runtime DLLs may be dependencies of python shared library itself or of extension
    # 002496.python.dylib.line57.comment modules provided by 3rd party packages.

    # 002497.python.dylib.line59.comment Visual Studio 2010 (VC10) runtime
    # 002498.python.dylib.line60.comment http://msdn.microsoft.com/en-us/library/8kche8ah(v=vs.100).aspx
    r'atl100\.dll',
    r'msvcr100\.dll',
    r'msvcp100\.dll',
    r'mfc100\.dll',
    r'mfc100u\.dll',
    r'mfcmifc80\.dll',
    r'mfcm100\.dll',
    r'mfcm100u\.dll',

    # 002499.python.dylib.line70.comment Visual Studio 2012 (VC11) runtime
    # 002500.python.dylib.line71.comment https://docs.microsoft.com/en-us/visualstudio/releases/2013/2012-redistribution-vs
    # 002501.python.dylib.line72.comment
    # 002502.python.dylib.line73.comment VC110.ATL
    r'atl110\.dll',
    # 002503.python.dylib.line75.comment VC110.CRT
    r'msvcp110\.dll',
    r'msvcr110\.dll',
    r'vccorlib110\.dll',
    # 002504.python.dylib.line79.comment VC110.CXXAMP
    r'vcamp110\.dll',
    # 002505.python.dylib.line81.comment VC110.MFC
    r'mfc110\.dll',
    r'mfc110u\.dll',
    r'mfcm110\.dll',
    r'mfcm110u\.dll',
    # 002506.python.dylib.line86.comment VC110.MFCLOC
    r'mfc110chs\.dll',
    r'mfc110cht\.dll',
    r'mfc110enu\.dll',
    r'mfc110esn\.dll',
    r'mfc110deu\.dll',
    r'mfc110fra\.dll',
    r'mfc110ita\.dll',
    r'mfc110jpn\.dll',
    r'mfc110kor\.dll',
    r'mfc110rus\.dll',
    # 002507.python.dylib.line97.comment VC110.OpenMP
    r'vcomp110\.dll',
    # 002508.python.dylib.line99.comment DIA SDK
    r'msdia110\.dll',

    # 002509.python.dylib.line102.comment Visual Studio 2013 (VC12) runtime
    # 002510.python.dylib.line103.comment https://docs.microsoft.com/en-us/visualstudio/releases/2013/2013-redistribution-vs
    # 002511.python.dylib.line104.comment
    # 002512.python.dylib.line105.comment VC120.CRT
    r'msvcp120\.dll',
    r'msvcr120\.dll',
    r'vccorlib120\.dll',
    # 002513.python.dylib.line109.comment VC120.CXXAMP
    r'vcamp120\.dll',
    # 002514.python.dylib.line111.comment VC120.MFC
    r'mfc120\.dll',
    r'mfc120u\.dll',
    r'mfcm120\.dll',
    r'mfcm120u\.dll',
    # 002515.python.dylib.line116.comment VC120.MFCLOC
    r'mfc120chs\.dll',
    r'mfc120cht\.dll',
    r'mfc120deu\.dll',
    r'mfc120enu\.dll',
    r'mfc120esn\.dll',
    r'mfc120fra\.dll',
    r'mfc120ita\.dll',
    r'mfc120jpn\.dll',
    r'mfc120kor\.dll',
    r'mfc120rus\.dll',
    # 002516.python.dylib.line127.comment VC120.OPENMP
    r'vcomp120\.dll',
    # 002517.python.dylib.line129.comment DIA SDK
    r'msdia120\.dll',
    # 002518.python.dylib.line131.comment Cpp REST Windows SDK
    r'casablanca120.winrt\.dll',
    # 002519.python.dylib.line133.comment Mobile Services Cpp Client
    r'zumosdk120.winrt\.dll',
    # 002520.python.dylib.line135.comment Cpp REST SDK
    r'casablanca120\.dll',

    # 002521.python.dylib.line138.comment Universal C Runtime Library (since Visual Studio 2015)
    # 002522.python.dylib.line139.comment
    # 002523.python.dylib.line140.comment NOTE: these should be put under a switch, as they need not to be bundled if deployment target is Windows 10
    # 002524.python.dylib.line141.comment and later, as "UCRT is now a system component in Windows 10 and later, managed by Windows Update".
    # 002525.python.dylib.line142.comment (https://docs.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170)
    # 002526.python.dylib.line143.comment And as discovered in #6326, Windows prefers system-installed version over the bundled one, anyway
    # 002527.python.dylib.line144.comment (see https://docs.microsoft.com/en-us/cpp/windows/universal-crt-deployment?view=msvc-170#local-deployment).
    r'api-ms-win-core.*',
    r'api-ms-win-crt.*',
    r'ucrtbase\.dll',

    # 002528.python.dylib.line149.comment Visual Studio 2015/2017/2019/2022 (VC14) runtime
    # 002529.python.dylib.line150.comment https://docs.microsoft.com/en-us/visualstudio/releases/2022/redistribution
    # 002530.python.dylib.line151.comment
    # 002531.python.dylib.line152.comment VC141.CRT/VC142.CRT/VC143.CRT
    r'concrt140\.dll',
    r'msvcp140\.dll',
    r'msvcp140_1\.dll',
    r'msvcp140_2\.dll',
    r'msvcp140_atomic_wait\.dll',
    r'msvcp140_codecvt_ids\.dll',
    r'vccorlib140\.dll',
    r'vcruntime140\.dll',
    r'vcruntime140_1\.dll',
    # 002532.python.dylib.line162.comment VC141.CXXAMP/VC142.CXXAMP/VC143.CXXAMP
    r'vcamp140\.dll',
    # 002533.python.dylib.line164.comment VC141.OpenMP/VC142.OpenMP/VC143.OpenMP
    r'vcomp140\.dll',
    # 002534.python.dylib.line166.comment DIA SDK
    r'msdia140\.dll',

    # 002535.python.dylib.line169.comment Allow pythonNN.dll, pythoncomNN.dll, pywintypesNN.dll
    r'py(?:thon(?:com(?:loader)?)?|wintypes)\d+\.dll',
}

_win_excludes = {
    # 002536.python.dylib.line174.comment On Windows, only .dll files can be loaded.
    r'.*\.so',
    r'.*\.dylib',

    # 002537.python.dylib.line178.comment MS assembly excludes
    r'Microsoft\.Windows\.Common-Controls',
}

_unix_excludes = {
    r'libc\.so(\..*)?',
    r'libdl\.so(\..*)?',
    r'libm\.so(\..*)?',
    r'libpthread\.so(\..*)?',
    r'librt\.so(\..*)?',
    r'libthread_db\.so(\..*)?',
    # 002538.python.dylib.line189.comment glibc regex excludes.
    r'ld-linux\.so(\..*)?',
    r'libBrokenLocale\.so(\..*)?',
    r'libanl\.so(\..*)?',
    r'libcidn\.so(\..*)?',
    r'libcrypt\.so(\..*)?',
    r'libnsl\.so(\..*)?',
    r'libnss_compat.*\.so(\..*)?',
    r'libnss_dns.*\.so(\..*)?',
    r'libnss_files.*\.so(\..*)?',
    r'libnss_hesiod.*\.so(\..*)?',
    r'libnss_nis.*\.so(\..*)?',
    r'libnss_nisplus.*\.so(\..*)?',
    r'libresolv\.so(\..*)?',
    r'libutil\.so(\..*)?',
    # 002539.python.dylib.line204.comment graphical interface libraries come with graphical stack (see libglvnd)
    r'libE?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?\.so(\..*)?',
    r'libdrm\.so(\..*)?',
    # 002540.python.dylib.line207.comment a subset of libraries included as part of the Nvidia Linux Graphics Driver as of 520.56.06:
    # 002541.python.dylib.line208.comment https://download.nvidia.com/XFree86/Linux-x86_64/520.56.06/README/installedcomponents.html
    r'nvidia_drv\.so',
    r'libglxserver_nvidia\.so(\..*)?',
    r'libnvidia-egl-(gbm|wayland)\.so(\..*)?',
    r'libnvidia-(cfg|compiler|e?glcore|glsi|glvkspirv|rtcore|allocator|tls|ml)\.so(\..*)?',
    r'lib(EGL|GLX)_nvidia\.so(\..*)?',
    # 002542.python.dylib.line214.comment libcuda.so, libcuda.so.1, and libcuda.so.{version} are run-time part of NVIDIA driver, and should not be
    # 002543.python.dylib.line215.comment collected, as they need to match the rest of driver components on the target system.
    r'libcuda\.so(\..*)?',
    r'libcudadebugger\.so(\..*)?',
    # 002544.python.dylib.line218.comment libxcb-dri changes ABI frequently (e.g.: between Ubuntu LTS releases) and is usually installed as dependency of
    # 002545.python.dylib.line219.comment the graphics stack anyway. No need to bundle it.
    r'libxcb\.so(\..*)?',
    r'libxcb-dri.*\.so(\..*)?',
    # 002546.python.dylib.line222.comment system running a Wayland compositor should already have these libraries
    # 002547.python.dylib.line223.comment in versions that should not conflict with system drivers, unlike bundled
    r'libwayland.*\.so(\..*)?',
}

_aix_excludes = {
    r'libbz2\.a',
    r'libc\.a',
    r'libC\.a',
    r'libcrypt\.a',
    r'libdl\.a',
    r'libintl\.a',
    r'libpthreads\.a',
    r'librt\\.a',
    r'librtl\.a',
    r'libz\.a',
}

_solaris_excludes = {
    r'libsocket\.so(\..*)?',
}

_cygwin_excludes = {
    r'cygwin1\.dll',
}

if compat.is_win:
    _includes |= _win_includes
    _excludes |= _win_excludes
elif compat.is_cygwin:
    _excludes |= _cygwin_excludes
elif compat.is_aix:
    # 002548.python.dylib.line254.comment The exclude list for AIX differs from other *nix platforms.
    _excludes |= _aix_excludes
elif compat.is_solar:
    # 002549.python.dylib.line257.comment The exclude list for Solaris differs from other *nix platforms.
    _excludes |= _solaris_excludes
    _excludes |= _unix_excludes
elif compat.is_unix:
    # 002550.python.dylib.line261.comment Common excludes for *nix platforms -- except AIX.
    _excludes |= _unix_excludes


class MatchList:
    def __init__(self, entries):
        self._regex = re.compile('|'.join(entries), re.I) if entries else None

    def check_library(self, libname):
        if self._regex:
            return self._regex.match(os.path.basename(libname))
        return False


if compat.is_darwin:
    import macholib.util

    class MacExcludeList(MatchList):
        def __init__(self, entries):
            super().__init__(entries)

        def check_library(self, libname):
            # 002551.python.dylib.line283.comment Try the global exclude list.
            result = super().check_library(libname)
            if result:
                return result

            # 002552.python.dylib.line288.comment Exclude libraries in standard system locations.
            return macholib.util.in_system_path(libname)

    exclude_list = MacExcludeList(_excludes)
    include_list = MatchList(_includes)

elif compat.is_win:
    from PyInstaller.utils.win32 import winutils

    class WinExcludeList(MatchList):
        def __init__(self, entries):
            super().__init__(entries)

            self._windows_dir = pathlib.Path(winutils.get_windows_dir()).resolve()

            # 002553.python.dylib.line303.comment When running as SYSTEM user, the home directory is `%WINDIR%\system32\config\systemprofile`.
            self._home_dir = pathlib.Path.home().resolve()
            self._system_home = self._windows_dir in self._home_dir.parents

        def check_library(self, libname):
            # 002554.python.dylib.line308.comment Try the global exclude list. The global exclude list contains lower-cased names, so lower-case the input
            # 002555.python.dylib.line309.comment for case-normalized comparison.
            result = super().check_library(libname.lower())
            if result:
                return result

            # 002556.python.dylib.line314.comment Exclude everything from the Windows directory by default; but allow contents of user's gome directory if
            # 002557.python.dylib.line315.comment that happens to be rooted under Windows directory (e.g., when running PyInstaller as SYSTEM user).
            lib_fullpath = pathlib.Path(libname).resolve()
            exclude = self._windows_dir in lib_fullpath.parents
            if exclude and self._system_home and self._home_dir in lib_fullpath.parents:
                exclude = False
            return exclude

    exclude_list = WinExcludeList(_excludes)
    include_list = MatchList(_includes)
else:
    exclude_list = MatchList(_excludes)
    include_list = MatchList(_includes)

_seen_wine_dlls = set()  # Used for warning tracking in include_library()


def include_library(libname):
    """
    Check if the dynamic library should be included with application or not.
    """
    if exclude_list.check_library(libname) and not include_list.check_library(libname):
        # 002559.python.dylib.line336.comment Library is excluded and is not overridden by include list. It should be excluded.
        return False

    # 002560.python.dylib.line339.comment If we are running under Wine and the library is a Wine built-in DLL, ensure that it is always excluded. Typically,
    # 002561.python.dylib.line340.comment excluding a DLL leads to an incomplete bundle and run-time errors when the said DLL is not installed on the target
    # 002562.python.dylib.line341.comment system. However, having Wine built-in DLLs collected is even more detrimental, as they usually provide Wine's
    # 002563.python.dylib.line342.comment implementation of low-level functionality, and therefore cannot be used on actual Windows (i.e., system libraries
    # 002564.python.dylib.line343.comment from the C:\Windows\system32 directory that might end up collected due to ``_win_includes`` list; a prominent
    # 002565.python.dylib.line344.comment example are VC runtime DLLs, for which Wine provides their own implementation, unless user explicitly installs
    # 002566.python.dylib.line345.comment Microsoft's VC redistributable package in their Wine environment). Therefore, excluding the Wine built-in DLLs
    # 002567.python.dylib.line346.comment actually improves the chances of the bundle running on Windows, or at least makes the issue easier to debug by
    # 002568.python.dylib.line347.comment turning it into the "standard" missing DLL problem. Exclusion should not affect the bundle's ability to run under
    # 002569.python.dylib.line348.comment Wine itself, as the excluded DLLs are available there.
    if compat.is_win_wine and compat.is_wine_dll(libname):
        # 002570.python.dylib.line350.comment Display warning message only once per DLL. Note that it is also displayed only if the DLL were to be included
        # 002571.python.dylib.line351.comment in the first place.
        if libname not in _seen_wine_dlls:
            logger.warning("Excluding Wine built-in DLL: %s", libname)
            _seen_wine_dlls.add(libname)
        return False

    return True


# 002572.python.dylib.line360.comment Patterns for suppressing warnings about missing dynamically linked libraries
_warning_suppressions = []

# 002573.python.dylib.line363.comment On some systems (e.g., openwrt), libc.so might point to ldd. Suppress warnings about it.
if compat.is_linux:
    _warning_suppressions.append(r'ldd')

# 002574.python.dylib.line367.comment Suppress warnings about unresolvable UCRT DLLs (see issue #1566) on Windows 10 and 11.
if compat.is_win_10 or compat.is_win_11:
    _warning_suppressions.append(r'api-ms-win-.*\.dll')

missing_lib_warning_suppression_list = MatchList(_warning_suppressions)


def warn_missing_lib(libname):
    """
    Check if a missing-library warning should be displayed for the given library name (or full path).
    """
    return not missing_lib_warning_suppression_list.check_library(libname)
