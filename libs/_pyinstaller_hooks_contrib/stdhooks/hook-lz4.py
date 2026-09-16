# 014469.python.hook-lz4.line1.comment ------------------------------------------------------------------
# 014470.python.hook-lz4.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014471.python.hook-lz4.line3.comment
# 014472.python.hook-lz4.line4.comment This file is distributed under the terms of the GNU General Public
# 014473.python.hook-lz4.line5.comment License (version 2.0 or later).
# 014474.python.hook-lz4.line6.comment
# 014475.python.hook-lz4.line7.comment The full license is available in LICENSE, distributed with
# 014476.python.hook-lz4.line8.comment this software.
# 014477.python.hook-lz4.line9.comment
# 014478.python.hook-lz4.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014479.python.hook-lz4.line11.comment ------------------------------------------------------------------
# 014480.python.hook-lz4.line12.comment hook for https://github.com/python-lz4/python-lz4

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('lz4')
