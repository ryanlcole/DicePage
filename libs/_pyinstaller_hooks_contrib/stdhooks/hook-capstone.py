# 012429.python.hook-capstone.line1.comment ------------------------------------------------------------------
# 012430.python.hook-capstone.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012431.python.hook-capstone.line3.comment
# 012432.python.hook-capstone.line4.comment This file is distributed under the terms of the GNU General Public
# 012433.python.hook-capstone.line5.comment License (version 2.0 or later).
# 012434.python.hook-capstone.line6.comment
# 012435.python.hook-capstone.line7.comment The full license is available in LICENSE, distributed with
# 012436.python.hook-capstone.line8.comment this software.
# 012437.python.hook-capstone.line9.comment
# 012438.python.hook-capstone.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012439.python.hook-capstone.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_dynamic_libs

# 012440.python.hook-capstone.line14.comment Collect needed libraries for capstone
binaries = collect_dynamic_libs('capstone')
