# 015342.python.hook-pinyin.line1.comment ------------------------------------------------------------------
# 015343.python.hook-pinyin.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015344.python.hook-pinyin.line3.comment
# 015345.python.hook-pinyin.line4.comment This file is distributed under the terms of the GNU General Public
# 015346.python.hook-pinyin.line5.comment License (version 2.0 or later).
# 015347.python.hook-pinyin.line6.comment
# 015348.python.hook-pinyin.line7.comment The full license is available in LICENSE, distributed with
# 015349.python.hook-pinyin.line8.comment this software.
# 015350.python.hook-pinyin.line9.comment
# 015351.python.hook-pinyin.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015352.python.hook-pinyin.line11.comment ------------------------------------------------------------------

# 015353.python.hook-pinyin.line13.comment Hook for the pinyin package: https://pypi.python.org/pypi/pinyin
# 015354.python.hook-pinyin.line14.comment Tested with pinyin 0.4.0 and Python 3.6.2, on Windows 10 x64.

from PyInstaller.utils.hooks import collect_data_files

# 015355.python.hook-pinyin.line18.comment pinyin relies on 'Mandarin.dat' and 'cedict.txt.gz'
# 015356.python.hook-pinyin.line19.comment for character and word translation.
datas = collect_data_files('pinyin')
