# 012969.python.hook-distorm3.line1.comment ------------------------------------------------------------------
# 012970.python.hook-distorm3.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012971.python.hook-distorm3.line3.comment
# 012972.python.hook-distorm3.line4.comment This file is distributed under the terms of the GNU General Public
# 012973.python.hook-distorm3.line5.comment License (version 2.0 or later).
# 012974.python.hook-distorm3.line6.comment
# 012975.python.hook-distorm3.line7.comment The full license is available in LICENSE, distributed with
# 012976.python.hook-distorm3.line8.comment this software.
# 012977.python.hook-distorm3.line9.comment
# 012978.python.hook-distorm3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012979.python.hook-distorm3.line11.comment ------------------------------------------------------------------

# 012980.python.hook-distorm3.line13.comment Hook for the diStorm3 module: https://pypi.python.org/pypi/distorm3
# 012981.python.hook-distorm3.line14.comment Tested with distorm3 3.3.0, Python 2.7, Windows

from PyInstaller.utils.hooks import collect_dynamic_libs

# 012982.python.hook-distorm3.line18.comment distorm3 dynamic library should be in the path with other dynamic libraries.
binaries = collect_dynamic_libs('distorm3', destdir='.')
