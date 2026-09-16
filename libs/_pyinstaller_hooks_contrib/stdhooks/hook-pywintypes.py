# 016338.python.hook-pywintypes.line1.comment ------------------------------------------------------------------
# 016339.python.hook-pywintypes.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016340.python.hook-pywintypes.line3.comment
# 016341.python.hook-pywintypes.line4.comment This file is distributed under the terms of the GNU General Public
# 016342.python.hook-pywintypes.line5.comment License (version 2.0 or later).
# 016343.python.hook-pywintypes.line6.comment
# 016344.python.hook-pywintypes.line7.comment The full license is available in LICENSE, distributed with
# 016345.python.hook-pywintypes.line8.comment this software.
# 016346.python.hook-pywintypes.line9.comment
# 016347.python.hook-pywintypes.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016348.python.hook-pywintypes.line11.comment ------------------------------------------------------------------

# 016349.python.hook-pywintypes.line13.comment pywin32 supports frozen mode; in that mode, it is looking at sys.path for pywintypesXY.dll. However, as of
# 016350.python.hook-pywintypes.line14.comment PyInstaller 5.4, we may collect that DLL into its original pywin32_system32 sub-directory as part of the
# 016351.python.hook-pywintypes.line15.comment binary dependency analysis (and add it to sys.path by means of a runtime hook).

import pathlib

from PyInstaller.utils.hooks import is_module_satisfies, get_pywin32_module_file_attribute

dll_filename = get_pywin32_module_file_attribute('pywintypes')
dst_dir = '.'  # Top-level application directory

if is_module_satisfies('PyInstaller >= 5.4'):
    # 016353.python.hook-pywintypes.line25.comment Try preserving the original pywin32_system directory, if applicable (it is not applicable in Anaconda,
    # 016354.python.hook-pywintypes.line26.comment where the DLL is located in Library/bin).
    dll_path = pathlib.Path(dll_filename)
    if dll_path.parent.name == 'pywin32_system32':
        dst_dir = 'pywin32_system32'

binaries = [(dll_filename, dst_dir)]
