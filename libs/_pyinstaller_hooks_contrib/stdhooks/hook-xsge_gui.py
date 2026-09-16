# 020237.python.hook-xsge_gui.line1.comment ------------------------------------------------------------------
# 020238.python.hook-xsge_gui.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020239.python.hook-xsge_gui.line3.comment
# 020240.python.hook-xsge_gui.line4.comment This file is distributed under the terms of the GNU General Public
# 020241.python.hook-xsge_gui.line5.comment License (version 2.0 or later).
# 020242.python.hook-xsge_gui.line6.comment
# 020243.python.hook-xsge_gui.line7.comment The full license is available in LICENSE, distributed with
# 020244.python.hook-xsge_gui.line8.comment this software.
# 020245.python.hook-xsge_gui.line9.comment
# 020246.python.hook-xsge_gui.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020247.python.hook-xsge_gui.line11.comment ------------------------------------------------------------------

# 020248.python.hook-xsge_gui.line13.comment Hook for the xsge_gui module: https://pypi.python.org/pypi/xsge_gui

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('xsge_gui')
