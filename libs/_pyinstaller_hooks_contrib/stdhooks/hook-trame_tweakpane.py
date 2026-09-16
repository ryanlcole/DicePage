# 017997.python.hook-trame_tweakpane.line1.comment ------------------------------------------------------------------
# 017998.python.hook-trame_tweakpane.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017999.python.hook-trame_tweakpane.line3.comment
# 018000.python.hook-trame_tweakpane.line4.comment This file is distributed under the terms of the GNU General Public
# 018001.python.hook-trame_tweakpane.line5.comment License (version 2.0 or later).
# 018002.python.hook-trame_tweakpane.line6.comment
# 018003.python.hook-trame_tweakpane.line7.comment The full license is available in LICENSE, distributed with
# 018004.python.hook-trame_tweakpane.line8.comment this software.
# 018005.python.hook-trame_tweakpane.line9.comment
# 018006.python.hook-trame_tweakpane.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018007.python.hook-trame_tweakpane.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_tweakpane", subdir="module")]
