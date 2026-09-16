# 006686.python.hook-scipy.line1.comment -----------------------------------------------------------------------------
# 006687.python.hook-scipy.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006688.python.hook-scipy.line3.comment
# 006689.python.hook-scipy.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006690.python.hook-scipy.line5.comment or later) with exception for distributing the bootloader.
# 006691.python.hook-scipy.line6.comment
# 006692.python.hook-scipy.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006693.python.hook-scipy.line8.comment
# 006694.python.hook-scipy.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006695.python.hook-scipy.line10.comment -----------------------------------------------------------------------------

import glob
import os
import sysconfig

from PyInstaller.compat import is_win, is_linux
from PyInstaller.utils.hooks import (
    get_module_file_attribute,
    check_requirement,
    collect_delvewheel_libs_directory,
    collect_submodules,
)

binaries = []
datas = []

# 006696.python.hook-scipy.line27.comment Package the DLL bundle that official scipy wheels for Windows ship The DLL bundle will either be in extra-dll on
# 006697.python.hook-scipy.line28.comment windows proper and in .libs if installed on a virtualenv created from MinGW (Git-Bash for example)
if is_win:
    extra_dll_locations = ['extra-dll', '.libs']
    for location in extra_dll_locations:
        dll_glob = os.path.join(os.path.dirname(get_module_file_attribute('scipy')), location, "*.dll")
        if glob.glob(dll_glob):
            binaries.append((dll_glob, "."))

# 006698.python.hook-scipy.line36.comment Handle delvewheel-enabled win32 wheels, which have external scipy.libs directory (scipy >= 0.9.2)
if check_requirement("scipy >= 1.9.2") and is_win:
    datas, binaries = collect_delvewheel_libs_directory('scipy', datas=datas, binaries=binaries)

# 006699.python.hook-scipy.line40.comment collect library-wide utility extension modules
hiddenimports = ['scipy._lib.%s' % m for m in ['messagestream', "_ccallback_c", "_fpumode"]]

# 006700.python.hook-scipy.line43.comment In scipy 1.14.0, `scipy._lib.array_api_compat.numpy` added a programmatic import of its `.fft` submodule, which needs
# 006701.python.hook-scipy.line44.comment to be added to hiddenimports.
if check_requirement("scipy >= 1.14.0"):
    hiddenimports += ['scipy._lib.array_api_compat.numpy.fft']

# 006702.python.hook-scipy.line48.comment If scipy is provided by Debian's python3-scipy, its scipy.__config__ submodule is renamed to a dynamically imported
# 006703.python.hook-scipy.line49.comment scipy.__config__${SOABI}__
# 006704.python.hook-scipy.line50.comment https://salsa.debian.org/python-team/packages/scipy/-/blob/1255922cf7c52b05aa44fb733449953cd9adb815/debian/patches/scipy_config_SOABI.patch
if is_linux and "dist-packages" in get_module_file_attribute("scipy"):
    hiddenimports.append('scipy.__config__' + sysconfig.get_config_var('SOABI') + '__')

# 006705.python.hook-scipy.line54.comment The `scipy._lib.array_api_compat.numpy` module performs a `from numpy import *`; in numpy 2.0.0, `numpy.f2py` was
# 006706.python.hook-scipy.line55.comment added to `numpy.__all__` attribute, but at the same time, the upstream numpy hook adds `numpy.f2py` to
# 006707.python.hook-scipy.line56.comment `excludedimports`. Therefore, the `numpy.f2py` sub-package ends up missing. Due to the way exclusion mechanism works,
# 006708.python.hook-scipy.line57.comment we need to add both `numpy.f2py` and all its submodules to hiddenimports here.
if check_requirement("numpy >= 2.0.0"):
    hiddenimports += collect_submodules('numpy.f2py', filter=lambda name: name != 'numpy.f2py.tests')
