# 014537.python.hook-mecab.line1.comment ------------------------------------------------------------------
# 014538.python.hook-mecab.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014539.python.hook-mecab.line3.comment
# 014540.python.hook-mecab.line4.comment This file is distributed under the terms of the GNU General Public
# 014541.python.hook-mecab.line5.comment License (version 2.0 or later).
# 014542.python.hook-mecab.line6.comment
# 014543.python.hook-mecab.line7.comment The full license is available in LICENSE, distributed with
# 014544.python.hook-mecab.line8.comment this software.
# 014545.python.hook-mecab.line9.comment
# 014546.python.hook-mecab.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014547.python.hook-mecab.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('mecab')
datas += collect_data_files('mecab_ko_dic')
