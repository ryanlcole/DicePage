# 016273.python.hook-pythoncom.line1.comment ------------------------------------------------------------------
# 016274.python.hook-pythoncom.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016275.python.hook-pythoncom.line3.comment
# 016276.python.hook-pythoncom.line4.comment This file is distributed under the terms of the GNU General Public
# 016277.python.hook-pythoncom.line5.comment License (version 2.0 or later).
# 016278.python.hook-pythoncom.line6.comment
# 016279.python.hook-pythoncom.line7.comment The full license is available in LICENSE, distributed with
# 016280.python.hook-pythoncom.line8.comment this software.
# 016281.python.hook-pythoncom.line9.comment
# 016282.python.hook-pythoncom.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016283.python.hook-pythoncom.line11.comment ------------------------------------------------------------------

# 016284.python.hook-pythoncom.line13.comment pywin32 supports frozen mode; in that mode, it is looking at sys.path for pythoncomXY.dll. However, as of
# 016285.python.hook-pythoncom.line14.comment PyInstaller 5.4, we may collect that DLL into its original pywin32_system32 sub-directory as part of the
# 016286.python.hook-pythoncom.line15.comment binary dependency analysis (and add it to sys.path by means of a runtime hook).

import pathlib

from PyInstaller.utils.hooks import is_module_satisfies, get_pywin32_module_file_attribute

dll_filename = get_pywin32_module_file_attribute('pythoncom')
dst_dir = '.'  # Top-level application directory

if is_module_satisfies('PyInstaller >= 5.4'):
    # 016288.python.hook-pythoncom.line25.comment Try preserving the original pywin32_system directory, if applicable (it is not applicable in Anaconda,
    # 016289.python.hook-pythoncom.line26.comment where the DLL is located in Library/bin).
    dll_path = pathlib.Path(dll_filename)
    if dll_path.parent.name == 'pywin32_system32':
        dst_dir = 'pywin32_system32'

binaries = [(dll_filename, dst_dir)]
