# 011891.python.hook-accessible_output2.line1.comment ------------------------------------------------------------------
# 011892.python.hook-accessible_output2.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011893.python.hook-accessible_output2.line3.comment
# 011894.python.hook-accessible_output2.line4.comment This file is distributed under the terms of the GNU General Public
# 011895.python.hook-accessible_output2.line5.comment License (version 2.0 or later).
# 011896.python.hook-accessible_output2.line6.comment
# 011897.python.hook-accessible_output2.line7.comment The full license is available in LICENSE, distributed with
# 011898.python.hook-accessible_output2.line8.comment this software.
# 011899.python.hook-accessible_output2.line9.comment
# 011900.python.hook-accessible_output2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011901.python.hook-accessible_output2.line11.comment ------------------------------------------------------------------
"""
accessible_output2: http://hg.q-continuum.net/accessible_output2
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('accessible_output2')
