# 006981.python.hook-win32ctypes.core.line1.comment -----------------------------------------------------------------------------
# 006982.python.hook-win32ctypes.core.line2.comment Copyright (c) 2020-2023, PyInstaller Development Team.
# 006983.python.hook-win32ctypes.core.line3.comment
# 006984.python.hook-win32ctypes.core.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006985.python.hook-win32ctypes.core.line5.comment or later) with exception for distributing the bootloader.
# 006986.python.hook-win32ctypes.core.line6.comment
# 006987.python.hook-win32ctypes.core.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006988.python.hook-win32ctypes.core.line8.comment
# 006989.python.hook-win32ctypes.core.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006990.python.hook-win32ctypes.core.line10.comment -----------------------------------------------------------------------------

# 006991.python.hook-win32ctypes.core.line12.comment TODO: remove this hook during PyInstaller 4.5 release cycle!

from PyInstaller.utils.hooks import can_import_module, collect_submodules

# 006992.python.hook-win32ctypes.core.line16.comment We need to collect submodules from win32ctypes.core.cffi or win32ctypes.core.ctypes for win32ctypes.core to work.
# 006993.python.hook-win32ctypes.core.line17.comment Always collect the `ctypes` backend, and add the `cffi` one if `cffi` is available. Having the `ctypes` backend always
# 006994.python.hook-win32ctypes.core.line18.comment available helps in situations when `cffi` is available in the build environment, but is disabled at run-time or not
# 006995.python.hook-win32ctypes.core.line19.comment collected (e.g., due to `--exclude cffi`).
hiddenimports = collect_submodules('win32ctypes.core.ctypes')
if can_import_module('cffi'):
    hiddenimports += collect_submodules('win32ctypes.core.cffi')
