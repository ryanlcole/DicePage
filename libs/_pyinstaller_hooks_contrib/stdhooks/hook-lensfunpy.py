# 014257.python.hook-lensfunpy.line1.comment ------------------------------------------------------------------
# 014258.python.hook-lensfunpy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014259.python.hook-lensfunpy.line3.comment
# 014260.python.hook-lensfunpy.line4.comment This file is distributed under the terms of the GNU General Public
# 014261.python.hook-lensfunpy.line5.comment License (version 2.0 or later).
# 014262.python.hook-lensfunpy.line6.comment
# 014263.python.hook-lensfunpy.line7.comment The full license is available in LICENSE, distributed with
# 014264.python.hook-lensfunpy.line8.comment this software.
# 014265.python.hook-lensfunpy.line9.comment
# 014266.python.hook-lensfunpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014267.python.hook-lensfunpy.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
# 014268.python.hook-lensfunpy.line14.comment bundle xml DB files, skip other files (like DLL files on Windows)
datas = list(filter(lambda p: p[0].endswith('.xml'), collect_data_files('lensfunpy')))
hiddenimports = ['numpy', 'enum']
