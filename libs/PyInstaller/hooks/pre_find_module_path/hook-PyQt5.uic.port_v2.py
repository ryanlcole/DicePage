# 007039.python.hook-PyQt5.uic.port_v2.line1.comment -----------------------------------------------------------------------------
# 007040.python.hook-PyQt5.uic.port_v2.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 007041.python.hook-PyQt5.uic.port_v2.line3.comment
# 007042.python.hook-PyQt5.uic.port_v2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007043.python.hook-PyQt5.uic.port_v2.line5.comment or later) with exception for distributing the bootloader.
# 007044.python.hook-PyQt5.uic.port_v2.line6.comment
# 007045.python.hook-PyQt5.uic.port_v2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007046.python.hook-PyQt5.uic.port_v2.line8.comment
# 007047.python.hook-PyQt5.uic.port_v2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007048.python.hook-PyQt5.uic.port_v2.line10.comment -----------------------------------------------------------------------------


def pre_find_module_path(hook_api):
    # 007049.python.hook-PyQt5.uic.port_v2.line14.comment Forbid imports in the port_v2 directory under Python 3 The code wouldn't import and would crash the build process.
    hook_api.search_dirs = []
