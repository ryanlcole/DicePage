# 006622.python.hook-qtawesome.line1.comment -----------------------------------------------------------------------------
# 006623.python.hook-qtawesome.line2.comment Copyright (c) 2017-2023, PyInstaller Development Team.
# 006624.python.hook-qtawesome.line3.comment
# 006625.python.hook-qtawesome.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006626.python.hook-qtawesome.line5.comment or later) with exception for distributing the bootloader.
# 006627.python.hook-qtawesome.line6.comment
# 006628.python.hook-qtawesome.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006629.python.hook-qtawesome.line8.comment
# 006630.python.hook-qtawesome.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006631.python.hook-qtawesome.line10.comment -----------------------------------------------------------------------------
"""
Hook for QtAwesome (https://github.com/spyder-ide/qtawesome).
Font files and charmaps need to be included with module.
Tested with QtAwesome 0.4.4 and Python 3.6 on macOS 10.12.4.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('qtawesome')
