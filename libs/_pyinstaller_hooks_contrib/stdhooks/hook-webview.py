# 020090.python.hook-webview.line1.comment ------------------------------------------------------------------
# 020091.python.hook-webview.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020092.python.hook-webview.line3.comment
# 020093.python.hook-webview.line4.comment This file is distributed under the terms of the GNU General Public
# 020094.python.hook-webview.line5.comment License (version 2.0 or later).
# 020095.python.hook-webview.line6.comment
# 020096.python.hook-webview.line7.comment The full license is available in LICENSE, distributed with
# 020097.python.hook-webview.line8.comment this software.
# 020098.python.hook-webview.line9.comment
# 020099.python.hook-webview.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020100.python.hook-webview.line11.comment ------------------------------------------------------------------

# 020101.python.hook-webview.line13.comment hook for https://github.com/r0x0r/pywebview

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.compat import is_win

if is_win:
    datas = collect_data_files('webview', subdir='lib')
    binaries = collect_dynamic_libs('webview')
