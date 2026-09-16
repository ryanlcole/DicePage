# 011902.python.hook-adbutils.line1.comment ------------------------------------------------------------------
# 011903.python.hook-adbutils.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 011904.python.hook-adbutils.line3.comment
# 011905.python.hook-adbutils.line4.comment This file is distributed under the terms of the GNU General Public
# 011906.python.hook-adbutils.line5.comment License (version 2.0 or later).
# 011907.python.hook-adbutils.line6.comment
# 011908.python.hook-adbutils.line7.comment The full license is available in LICENSE, distributed with
# 011909.python.hook-adbutils.line8.comment this software.
# 011910.python.hook-adbutils.line9.comment
# 011911.python.hook-adbutils.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011912.python.hook-adbutils.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

# 011913.python.hook-adbutils.line15.comment adb.exe is not automatically collected by collect_dynamic_libs()
datas = collect_data_files("adbutils", subdir="binaries", includes=["adb*"])

# 011914.python.hook-adbutils.line18.comment adbutils v2.2.2 replaced `pkg_resources` with `importlib.resources`, and now uses the following code to determine the
# 011915.python.hook-adbutils.line19.comment path to the `adbutils.binaries` sub-package directory:
# 011916.python.hook-adbutils.line20.comment https://github.com/openatx/adbutils/blob/2.2.2/adbutils/_utils.py#L78-L87
# 011917.python.hook-adbutils.line21.comment As `adbutils.binaries` is not directly imported anywhere, we need a hidden import.
if is_module_satisfies('adbutils >= 2.2.2'):
    hiddenimports = ['adbutils.binaries']
