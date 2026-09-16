# 014269.python.hook-libaudioverse.line1.comment ------------------------------------------------------------------
# 014270.python.hook-libaudioverse.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014271.python.hook-libaudioverse.line3.comment
# 014272.python.hook-libaudioverse.line4.comment This file is distributed under the terms of the GNU General Public
# 014273.python.hook-libaudioverse.line5.comment License (version 2.0 or later).
# 014274.python.hook-libaudioverse.line6.comment
# 014275.python.hook-libaudioverse.line7.comment The full license is available in LICENSE, distributed with
# 014276.python.hook-libaudioverse.line8.comment this software.
# 014277.python.hook-libaudioverse.line9.comment
# 014278.python.hook-libaudioverse.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014279.python.hook-libaudioverse.line11.comment ------------------------------------------------------------------
"""
Libaudioverse: https://github.com/libaudioverse/libaudioverse
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('libaudioverse')
