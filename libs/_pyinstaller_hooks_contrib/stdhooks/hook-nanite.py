# 014715.python.hook-nanite.line1.comment ------------------------------------------------------------------
# 014716.python.hook-nanite.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014717.python.hook-nanite.line3.comment
# 014718.python.hook-nanite.line4.comment This file is distributed under the terms of the GNU General Public
# 014719.python.hook-nanite.line5.comment License (version 2.0 or later).
# 014720.python.hook-nanite.line6.comment
# 014721.python.hook-nanite.line7.comment The full license is available in LICENSE, distributed with
# 014722.python.hook-nanite.line8.comment this software.
# 014723.python.hook-nanite.line9.comment
# 014724.python.hook-nanite.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014725.python.hook-nanite.line11.comment ------------------------------------------------------------------

# 014726.python.hook-nanite.line13.comment Hook for nanite: https://pypi.python.org/pypi/nanite

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('nanite')
