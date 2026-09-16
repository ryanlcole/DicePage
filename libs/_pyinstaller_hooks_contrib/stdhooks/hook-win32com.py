# 020102.python.hook-win32com.line1.comment ------------------------------------------------------------------
# 020103.python.hook-win32com.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020104.python.hook-win32com.line3.comment
# 020105.python.hook-win32com.line4.comment This file is distributed under the terms of the GNU General Public
# 020106.python.hook-win32com.line5.comment License (version 2.0 or later).
# 020107.python.hook-win32com.line6.comment
# 020108.python.hook-win32com.line7.comment The full license is available in LICENSE, distributed with
# 020109.python.hook-win32com.line8.comment this software.
# 020110.python.hook-win32com.line9.comment
# 020111.python.hook-win32com.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020112.python.hook-win32com.line11.comment ------------------------------------------------------------------

hiddenimports = [
    # 020113.python.hook-win32com.line14.comment win32com client and server util
    # 020114.python.hook-win32com.line15.comment modules could be hidden imports
    # 020115.python.hook-win32com.line16.comment of some modules using win32com.
    # 020116.python.hook-win32com.line17.comment Included for completeness.
    'win32com.client.util',
    'win32com.server.util',
]
