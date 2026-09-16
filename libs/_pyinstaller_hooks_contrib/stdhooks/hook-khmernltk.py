# 014168.python.hook-khmernltk.line1.comment ------------------------------------------------------------------
# 014169.python.hook-khmernltk.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014170.python.hook-khmernltk.line3.comment
# 014171.python.hook-khmernltk.line4.comment This file is distributed under the terms of the GNU General Public
# 014172.python.hook-khmernltk.line5.comment License (version 2.0 or later).
# 014173.python.hook-khmernltk.line6.comment
# 014174.python.hook-khmernltk.line7.comment The full license is available in LICENSE, distributed with
# 014175.python.hook-khmernltk.line8.comment this software.
# 014176.python.hook-khmernltk.line9.comment
# 014177.python.hook-khmernltk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014178.python.hook-khmernltk.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('khmernltk')
hiddenimports = ['sklearn_crfsuite']
