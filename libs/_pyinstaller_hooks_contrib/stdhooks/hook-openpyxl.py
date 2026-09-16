# 015105.python.hook-openpyxl.line1.comment ------------------------------------------------------------------
# 015106.python.hook-openpyxl.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015107.python.hook-openpyxl.line3.comment
# 015108.python.hook-openpyxl.line4.comment This file is distributed under the terms of the GNU General Public
# 015109.python.hook-openpyxl.line5.comment License (version 2.0 or later).
# 015110.python.hook-openpyxl.line6.comment
# 015111.python.hook-openpyxl.line7.comment The full license is available in LICENSE, distributed with
# 015112.python.hook-openpyxl.line8.comment this software.
# 015113.python.hook-openpyxl.line9.comment
# 015114.python.hook-openpyxl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015115.python.hook-openpyxl.line11.comment ------------------------------------------------------------------

# 015116.python.hook-openpyxl.line13.comment Hook for the openpyxl module: https://pypi.python.org/pypi/openpyxl
# 015117.python.hook-openpyxl.line14.comment Tested with openpyxl 2.3.4, Python 2.7, Windows

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('openpyxl')
